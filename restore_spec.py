#
# A specification for files/directories to include from a
# collection - either tarball or zipfile.
#
# Uses the browse.FileSpec class.

import datetime

import os.path
import db
import chroot
import browse
import auth

# Needed for RESTORE_BASE_DIR.
import zbm_cfg

# Used for creating restore files.
import zipfile, tarfile

class BadInclude(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return self.value

def get_current_restore_id():
    ( username, _, company_name, _ ) = auth.login_status()
    row = db.get1("select id from restores where active and username = %(username)s and company_name = %(company_name)s", vars())
    db.commit()
    if row is None:
        return None
    return int(row[0])

def get_previous_restore_id():
    ( username, _, company_name, _ ) = auth.login_status()
    row = db.get1("select max(id) from restores where not active and username = %(username)s and company_name = %(company_name)s", vars())
    db.commit()
    if row is None:
        return None
    return int(row[0])

def cancel_current_restore():
    current_restore_id = get_current_restore_id()
    db.do("update restores set active = false where id = %(current_restore_id)s", vars())
    db.commit()

def retrieve_previous_restore():
    previous_restore_id = get_previous_restore_id()
    current_restore_id = get_current_restore_id()
    if current_restore_id is not None:
        db.do("delete from restore_files where restore_id = %(current_restore_id)s", vars())
        db.do("delete from restores where id = %(current_restore_id)s", vars())
    db.do("update restores set active = true where id = %(previous_restore_id)s", vars())
    db.commit()

def zip_directory(zip_archive, path, archive_path):
    """ Handles zipping up a directory. """
    dir_contents = os.listdir(path)
    for f in dir_contents:
        f = os.path.join(path, f)   # Make the path relative.
        archive_name = os.path.join(archive_path, os.path.basename(f))
        if os.path.isdir(f):
            # Recursive case.
            zip_directory(zip_archive, f, archive_name)
        else:
            zip_archive.write(f, archive_name)

def create_zip_restore_file(rs):
    """ Create a zip restore file.
        Returns a tuple (result_boolean, message). """
    # zipfile.ZipFile(name=None, mode='r', compression=zipfile.ZIP_DEFLATED, ...)
    # name=os.path.join(RESTORE_BASE_DIR), company_name, 'restore_NN_YYYYMMDDhhmm.zip'
    #     (where NN=restore_id and YYYYMMDDhhmm is a timestamp)
    # mode='w'
    #
    # ZipFile.write(filename, arcname, ...)

    # First work out the restore filename.
    now = datetime.datetime.now()
    restore_dirname = "restore_%d_%s" % ( rs.restore_id, now.strftime("%Y%m%d%H%M") )
    restore_basename = restore_dirname + ".zip"
    # This is the partial-path we return from this function.
    # Update: No, we're now just returning restore_basename.
    restore_company_basename = os.path.join(rs.company_name, restore_basename)
    restore_filename = os.path.join(zbm_cfg.RESTORE_BASE_DIR, restore_company_basename)

    zf = zipfile.ZipFile(restore_filename, mode='w', compression=zipfile.ZIP_DEFLATED)

    # Now we need to add all the files... we need the literal filename
    # (full path) and the archive name (share plus path).
    for spp in rs.include_set:
        fs = rs.include_set[spp]
        archive_path = os.path.join(restore_dirname, browse.share_plus_path_to_archive_path(spp))
        if fs.type == 'dir':
            zip_directory(zf, fs.real_path, archive_path)
        else:
            zf.write(fs.real_path, archive_path)

    zf.close()
    os.chmod(restore_filename, 0644)

    return ( True, restore_basename )

def create_tar_restore_file(rs):
    """ Create a tar restore file.
        Returns a tuple (result_boolean, message). """
    now = datetime.datetime.now()
    restore_dirname = "restore_%d_%s" % ( rs.restore_id, now.strftime("%Y%m%d%H%M") )
    restore_basename = restore_dirname + ".tar.gz"
    # This is the partial-path we return from this function.
    # Update: No, we're now just returning restore_basename.
    restore_company_basename = os.path.join(rs.company_name, restore_basename)
    restore_filename = os.path.join(zbm_cfg.RESTORE_BASE_DIR, restore_company_basename)

    tf = tarfile.open(restore_filename, mode='w:gz')

    # Now we need to add all the files... we need the literal filename
    # (full path) and the archive name (share plus path).
    for spp in rs.include_set:
        fs = rs.include_set[spp]
        archive_path = os.path.join(restore_dirname, browse.share_plus_path_to_archive_path(spp))
        tf.add(fs.real_path, archive_path)

    tf.close()
    os.chmod(restore_filename, 0644)

    return ( True, restore_basename )

def create_restore_file(rs, restore_type):
    """ Create a restore file (zip or tar) from a restore spec.
        Returns a tuple (result_boolean, message). """
    ######################################################################
    # The include set is rs.include_set - a dictionary of
    #   share_plus_path => file_spec
    # 
    # restore_type is expected to be "zip" or "tar".
    ######################################################################
    #
    # tarfile.open(name=None, mode='r', fileobj=None, bufsize=10240, **kwargs)
    # name=os.path.join(RESTORE_BASE_DIR), company_name, 'restore_NN_YYYYMMDDhhmm.tar.gz'
    #     (where NN=restore_id and YYYYMMDDhhmm is a timestamp)
    # mode='w:gz'
    #
    # TarFile.add(name, arcname=None, recursive=True, exclude=None)
    #
    #   Add the file name to the archive. name may be any type of file
    #   (directory, fifo, symbolic link, etc.). If given, arcname
    #   specifies an alternative name for the file in the archive.
    #   Directories are added recursively by default.
    ######################################################################
    #
    # zipfile.ZipFile(name=None, mode='r', compression=zipfile.ZIP_DEFLATED, ...)
    # name=os.path.join(RESTORE_BASE_DIR), company_name, 'restore_NN_YYYYMMDDhhmm.zip'
    #     (where NN=restore_id and YYYYMMDDhhmm is a timestamp)
    # mode='w'
    #
    # ZipFile.write(filename, arcname, ...)
    if restore_type == 'zip':
        return create_zip_restore_file(rs)
    elif restore_type == 'tar':
        return create_tar_restore_file(rs)

    # We can't create any other kind of restore file.
    return ( False, None )

# Tracks paths to include and paths to exclude.
#
# Note: This is actually going to have to autoslurp to/from the
# database - adding and removing will have to update DB too.
# Shit.
#
# Ah, it's not too bad. Don't stress. Remember, you do *not* need to
# worry about performance - take the simplest and crudest option
# available, it'll be fine. Remember ec.cgi!
class RestoreSpec:
    def __init__(self, restore_id=None):
        # Try to grab the current active restore for this user. If
        # there isn't one there, create one.
        ( username, _, company_name, _ ) = auth.login_status()
        self.username = username
        self.company_name = company_name
        if restore_id is None:
            # Either create new or grab existing(!).
            row = db.get1("select id from restores where active and username = %(username)s and company_name = %(company_name)s", vars())
            db.commit()
            if row is None:
                # Create a new one.
                creation = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.do("insert into restores ( username, company_name, creation ) values ( %(username)s, %(company_name)s, %(creation)s )", vars())
                row = db.get1("select id from restores where username = %(username)s and company_name = %(company_name)s and creation = %(creation)s", vars())
                db.commit()
            # Grab the id.
            restore_id = int(row[0])

        self.restore_id = restore_id

        # Initialise.
        self.include_set = {}
        self.disk_usage_running_total = 0

        self.update_from_db()

    def update_from_db(self):
        restore_id = self.restore_id
        rows = db.get("select s.name, file_path, du_size from restore_files r, shares s where r.share_id = s.id and r.restore_id = %(restore_id)s", vars())
        db.commit()

        for r in rows:
            share = r[0]
            path = r[1]
            du_size = r[2]
            sp = chroot.build_share_path(self.company_name, r[0])
            mychroot = chroot.Chroot(sp)
            chrooted_path = mychroot.chrooted_path(path)
            share_plus_path = browse.join_share_to_path(share, path)
            self.include_set[share_plus_path] = browse.FileSpec(chrooted_path, share, disk_usage=du_size)
        
        self.disk_usage_running_total = sum([ r[2] for r in rows ])

    def __str__(self):
        """ Return a list of the included share+paths. """
        return str([ sp for sp in self.include_set ])

    def is_directly_included(self, file_spec):
        """ Returns true iff the file_spec is included. """
        # It has to be both the share and the path.
        return file_spec.share_plus_path in self.include_set

    def is_indirectly_included(self, file_spec):
        """ Returns true iff an ancestor of the file_spec is included. """
        # First make sure the ancestors are actually acquired.
        file_spec.chrooted_path.acquire_ancestors()
        # Now check for ancestors in the include set.
        ancestor_paths = [ browse.join_share_to_path(file_spec.share, cp.path) for cp in file_spec.chrooted_path.ancestors ]
        for ap in ancestor_paths:
            if ap in self.include_set:
                return True
        return False

    def is_included(self, file_spec):
        if self.is_directly_included(file_spec):
            return True
        if self.is_indirectly_included(file_spec):
            return True
        return False

    def include(self, file_spec):
        # This is a crucial part of the logic.
        if self.is_included(file_spec):
            raise BadInclude("File %s is already included in the restore spec." % ( file_spec.share_plus_path ))

        # Grab a copy of the include_set keys *before* including this
        # file_spec.
        before_fs_included_keys = self.include_set.keys()

        # We need the disk usage.
        # Just for the insert.
        du_size = file_spec.acquire_disk_usage()
        self.disk_usage_running_total += file_spec.disk_usage
        # Include it.
        self.include_set[file_spec.share_plus_path] = file_spec

        # Now we much check to see if any of the other included
        # file_specs become indirectly included - if so, they must be
        # removed.
        for k in before_fs_included_keys:
            check_fs = self.include_set[k]
            if self.is_indirectly_included(check_fs):
                self.remove(check_fs, do_commit=False)

        # Update the DB.
        row = db.get1("select id from shares where name = %(share_name)s and company_name = %(company_name)s", { 'company_name' : self.company_name, 'share_name' : file_spec.share })
        if row is None:
            # FIXME: Raise a better exception.
            raise BadInclude("Share %s does not exist in DB." % ( file_spec.share ))
        share_id = row[0]
        restore_id = self.restore_id
        file_path = file_spec.path
        db.do("insert into restore_files ( restore_id, share_id, file_path, du_size ) values ( %(restore_id)s, %(share_id)s, %(file_path)s, %(du_size)s)", vars())
        db.commit()

    def remove(self, file_spec, do_commit=True):
        # FIXME: Should check that the restore_id is active
        # before doing anything.
        # Can only remove paths that are directly included.
        if not file_spec.share_plus_path in self.include_set:
            raise BadInclude("File %s is not directly included in the restore spec." % ( file_spec.share_plus_path ))

        # Prepare to update the DB.
        row = db.get1("select id from shares where name = %(share_name)s and company_name = %(company_name)s", { 'company_name' : self.company_name, 'share_name' : file_spec.share })
        if row is None:
            # FIXME: Raise a better exception.
            raise BadInclude("Share %s does not exist in DB." % ( file_spec.share ))
        share_id = row[0]
        restore_id = self.restore_id
        file_path = file_spec.path

        # We need the disk usage to update the running total.
        # Do NOT call acquire_disk_usage as we don't need to.
        du_row = db.get1("select du_size from restore_files where restore_id = %(restore_id)s and share_id = %(share_id)s and file_path = %(file_path)s", vars())
        disk_usage = 0
        if not du_row is None:
            file_spec.disk_usage = du_row[0]
        disk_usage = file_spec.acquire_disk_usage()
        self.disk_usage_running_total -= disk_usage
        # Remove it.
        del self.include_set[file_spec.share_plus_path]

        db.do("delete from restore_files where restore_id = %(restore_id)s and share_id = %(share_id)s and file_path = %(file_path)s", vars())
        if do_commit:
            db.commit()

