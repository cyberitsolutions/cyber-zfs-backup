
import sys
import os
import datetime
import time
import calendar
from os.path import join, dirname
import subprocess as sp

import sets
import string
import re

import zbm_cfg as cfg

# Needed for the disk-usage-info caching.
import db

import html
import cgi
import chroot


######################################################################
# Exceptions.

class InaccessiblePathError(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return self.value

######################################################################
# Functions.

def convert_utc_timestamp_string(str, format="%Y-%m-%dT%H:%M:%SZ"):
    """ Return the date value for the input string. """
    str = str.strip()
    str_time = time.strptime(str, format)
    return datetime.datetime(*str_time[0:6])

def datetime_to_sse(dt):
    return int(calendar.timegm(dt.timetuple()))

# Yay! Awesome. This will do fine.
# Perhaps a tad sluggish on huge dirs, but more than
# good enough for the time being.
def really_get_disk_usage(path):
    """ Returns the path's disk usage in bytes.

        Always recursive for directories, use with caution. """
    # Note: Assumes du(1) is in path (usually a safe assumption).
    # Update: No, apparently it's not as safe an assumption as I'd
    # thought (or at least that the *correct* GNU-style du being first
    # in the PATH).
    output = sp.Popen([cfg.GNU_DU_PATH, '-sb', path], stdout=sp.PIPE).communicate()[0]
    return int(output.split('\t')[0])

def update_or_insert_filesystem_info_usage_size(path, usage_size):
    ppath = dirname(path)
    ppath_id = db.get1("select path_id from filesystem_info where path = %(ppath)s", vars())
    if ppath_id:
        ppath_id = ppath_id[0]

    if int(db.get1("select count(1) from filesystem_info where path = %(path)s", vars())[0]) > 0:
        db.do("update filesystem_info set usage_size = %(usage_size)s where path = %(path)s", vars())
    else:
        db.do("insert into filesystem_info ( path, usage_size, ppath_id ) values ( %(path)s, %(usage_size)s, %(ppath_id)s )", vars())

def update_or_insert_filesystem_info_apparent_size(path, apparent_size):
    ppath = dirname(path)
    ppath_id = db.get1("select path_id from filesystem_info where path = %(ppath)s", vars())
    if ppath_id:
        ppath_id = ppath_id[0]

    if int(db.get1("select count(1) from filesystem_info where path = %(path)s", vars())[0]) > 0:
        db.do("update filesystem_info set apparent_size = %(apparent_size)s where path = %(path)s", vars())
    else:
        db.do("insert into filesystem_info ( path, apparent_size, ppath_id ) values ( %(path)s, %(apparent_size)s, %(ppath_id)s )", vars())

def update_toplevel_path_apparent_size(path):
    """ Manually extracts du apparent-size of path and all
        subdirectories in database. """
    lines = sp.Popen([cfg.GNU_DU_PATH, '--apparent-size', '--block-size=1', path], stdout=sp.PIPE).communicate()[0].split('\n')
    # The last one is always empty, so get rid of it.
    lines.pop()
    # Reverse the output to get shallow directories first
    lines.reverse()
    for line in lines:
        if line is not None:
            ( du_size_str, du_path ) = line.split('\t', 1)
            apparent_size = int(du_size_str)
            update_or_insert_filesystem_info_apparent_size(du_path, apparent_size)
            db.commit()

def update_toplevel_path_usage_size(path):
    """ Manually extracts du disk-usage-size of path and all
        subdirectories in database. """
    # --apparent-size --block-size=1
    lines = sp.Popen([cfg.GNU_DU_PATH, '--block-size=1', path], stdout=sp.PIPE).communicate()[0].split('\n')
    # The last one is always empty, so get rid of it.
    lines.pop()
    # Reverse the output to get shallow directories first
    lines.reverse()
    for line in lines:
        if line is not None:
            ( du_size_str, du_path ) = line.split('\t', 1)
            usage_size = int(du_size_str)
            update_or_insert_filesystem_info_usage_size(du_path, usage_size)
            db.commit()

# Note: The contents of the supplied path are assumed to never ever
# change. Unless they're completely removed. This will be true for a
# ZFS snapshot, which is the use case normally expected.
def get_apparent_size(path):
    """ Checks to see if the path has an available apparent_size cached
        in our database - otherwise returns zero. """
    row = db.get1("select apparent_size from filesystem_info where path = %(path)s", vars())
    db.commit()
    if row is None:
        return getlsize(path)
    return int(row[0])

def getlsize(path):
    return os.lstat(path)[6]

def getlmtime(path):
    return os.lstat(path)[8]

def file_type(filepath):
    if os.path.islink(filepath):
        return 'link'
    if os.path.isfile(filepath):
        return 'file'
    if os.path.isdir(filepath):
        return 'dir'
    return 'special'

# These three always show the directories first.

def cmp_filespec_name(a, b):
    if a.type == 'dir' and b.type != 'dir':
        return -1
    if b.type == 'dir' and a.type != 'dir':
        return 1
    return cmp(a.name, b.name)

def cmp_filespec_size(a, b):
    if a.type == 'dir' and b.type != 'dir':
        return -1
    if b.type == 'dir' and a.type != 'dir':
        return 1
    return cmp(a.size, b.size)

def cmp_filespec_mtime(a, b):
    if a.type == 'dir' and b.type != 'dir':
        return -1
    if b.type == 'dir' and a.type != 'dir':
        return 1
    return cmp(a.mtime, b.mtime)

filespec_cmp = {
    'name' : cmp_filespec_name,
    'size' : cmp_filespec_size,
    'mtime' : cmp_filespec_mtime
}

######################################################################

def join_share_to_path(share, path):
    return string.join([share, path], '+')

def split_share_from_path(share_plus_path):
    return share_plus_path.split('+', 1)

def share_plus_path_to_archive_path(share_plus_path):
    """ Returns an expression suitable for use as an archive path. """
    ( share, path ) = split_share_from_path(share_plus_path)

    # Bugfix for invalid (colon) characters in the snapshot name.
    # Normally snapshot dirs look like this: "2010-03-24T14:05:31Z".
    #
    # This can't be allowed for a Windows system, as ':' is not a valid
    # character.
    m = re.match('^/([^/]+)(/.*)$', path)
    if not m:
        raise InaccessiblePathError("Bad path: \"%s\"" % path)
    snapdir = m.group(1)
    postsnap = m.group(2)
    decolonised_snapdir = re.sub(':', '_', snapdir)
    return os.path.join(share, decolonised_snapdir + postsnap)

class FileSpec:
    def __init__(self, chrooted_path, share, name=False, disk_usage=None, apparent_size=None, mtime=None, company_name=None):
        self.chrooted_path = chrooted_path
        self.real_path = self.chrooted_path.real_path
        self.share = share
        self.company_name = company_name

        # Need to handle (non-basename) softlinks appropriately.
        self.basename = os.path.basename(self.chrooted_path.path)
        if not name:
            name = self.basename
        
        self.name = name
        self.display = name
        self.path = chrooted_path.path

        # Used as a unique ID (well, unique by company).
        self.share_plus_path = join_share_to_path(self.share, self.path)

        # Extra file info.
        self.type = file_type(self.real_path)
        if apparent_size is None:
            self.size = getlsize(self.real_path)
        else:
            self.size = apparent_size
        # Not acquired by default, as it can be expensive.
        self.disk_usage = disk_usage
        if mtime is None:
            self.mtime = getlmtime(self.real_path)
        else:
            self.mtime = mtime

        if self.type == 'link':
            self.display = html.a(self.name, att='title="%s"' % ( cgi.escape(os.readlink(self.real_path), quote=True) ))
        elif self.type == 'dir':
            href = '/backup/browse?share=%s&amp;path=%s'% ( cgi.escape(self.share, quote=True), cgi.escape(self.path, quote=True) )
            if self.company_name:
                href += '&amp;company_name=%s' % (cgi.escape(self.company_name, quote=True))
            self.display = html.a(self.name, att='href="%s"' % (href))
            ops1 = os.path.split(self.path)[1]
            ops2 = os.path.split(ops1)[1]

    # Note: This actually returns the cached *apparent* size, which is
    # quite different to the disk usage.
    #
    # Refer to the argument Pete had with Ron and Steve in the tearoom
    # if you want to know why we're doing that.
    def acquire_disk_usage(self):
        """ This is only ever acquired from the database, so should be
            (relatively) cheap. """
        if self.disk_usage is None:
            self.disk_usage = get_apparent_size(self.real_path)
        return self.disk_usage

    def get_parent(self, name=False):
        """ Returns FileSpec of parent directory (if inside chroot). """
        if not self.chrooted_path.has_parent():
            return None
        pdir = self.chrooted_path.parent()
        return FileSpec(pdir, self.share, name=name)

def get_zfs_filesystem(realpath):
    """ Returns a ZFS filesystem name from a real path to that filesystem. """
    # Fairly boring really, just removes the leading / character
    # (and the trailing /.zfs/snapshot).
    return re.sub('/.zfs/snapshot$', '', realpath[1:])

def get_zfs_timestamp(filesystem):
    # Check to see if we've been given real_path instead of zfs_filesystem
    if filesystem[1] == '/':
        filesystem = get_zfs_filesystem(filesystem)
    output = sp.Popen(["zfs", "get", "-p", "-H", "-r", "-o", "name,value", "creation", filesystem], stdout=sp.PIPE).communicate()[0].split('\n')

def get_snapshot_timestamps(filesystem):
    """ For a ZFS filesystem, return a dict mapping snapshot name to datetime. """
    # zfs get -p -H -r -o name,value creation tank/hosted-backup/backups/ron/fabre.id.au:home
    output = sp.Popen(["zfs", "get", "-p", "-H", "-r", "-o", "name,value", "creation", filesystem], stdout=sp.PIPE).communicate()[0].split('\n')
    output = output[1:]
    output = output[:len(output)-1]
    d = {}
    for o in output:
        ( snap_name, sse ) = re.split(r'\t+', o)
        ( filesystem_name, snapshot_name ) = snap_name.split('@')
        d[snapshot_name] = int(sse)
    return d

# os.path.islink
# os.path.isdir
# os.path.isfile
def get_dir_contents(chrooted_path, share, page_num, sort_by="name", include_parent=True, reverse=False, company_name=None):
    real_dir = chrooted_path.real_path
    page_count = 1
    contents = []

    def get_files(real_dir):
        files = []
        # Retreive everything that's not a directory
        file_list = filter(lambda f: not os.path.isdir(os.path.join(real_dir, f)), os.listdir(real_dir))
        for f in file_list:
            file_path = os.path.join(f)
            files.append(FileSpec(chrooted_path.child(file_path), share, company_name=company_name))
        return files

    path_info = db.get1("select path_id,ppath_id,apparent_size from filesystem_info where path=%(real_dir)s", vars())
    if not path_info:
        raise InaccessiblePathError("%s is not an accessible directory." % ( chrooted_path.path ))
    if True:
        path_id = path_info[0]
        ppath_id = path_info[1]

        orderby_condition = ""
        orderby_condition = "order by path"

        limit = cfg.DEFAULT_PAGE_SIZE
        limit_condition = "limit %d" % limit
        offset = (int(page_num) - 1) * limit
        offset_condition = "offset %d" % offset
        if ppath_id is None:
            #zd = get_snapshot_timestamps(get_zfs_filesystem(real_dir))
            # Reverse it
            orderby_condition += " DESC"
        dir_count = db.get1("select count(*) from filesystem_info where ppath_id=%d" % ( path_id ))[0]
        for subdir in db.get("select path,apparent_size from filesystem_info where ppath_id=%d %s %s %s" % ( path_id, orderby_condition, limit_condition, offset_condition )):
            subpath = os.path.join(chrooted_path.path, subdir[0][len(real_dir) + len(os.sep):])
            chrooted_subpath = chrooted_path.child(subpath)
            mtime = None
            if ppath_id is None:
                # Get the mtime from the name.
                mtime = datetime_to_sse(convert_utc_timestamp_string(chrooted_subpath.basename))
            spec = FileSpec(chrooted_subpath, share, apparent_size=subdir[1], mtime=mtime, company_name=company_name)
            contents.append(spec)
        # Assuming that directories should always appear above files,
        # directory names don't need to be sorted.
        # This actually doesn't do much, the real sorting is in JS
        if sort_by != 'name':
            contents.sort(filespec_cmp[sort_by], reverse=reverse)

        # Don't try to list files for the topmost directory as it can take a while
        # There should be no files in there anyway
        files = []
        if ppath_id is not None:
            files = get_files(real_dir)
        # Cannot assume files will come in sorted order.
        files.sort(filespec_cmp[sort_by], reverse=reverse)
        # Now limit files appropriately based on number of directories
        # already displaying.
        file_start = max(0, offset - dir_count)
        contents.extend(files[file_start:file_start + limit - len(contents)])

        # There will always be a minimum of 1 page displayed.
        page_count = max(1, (dir_count + len(files) - 1) / limit + 1)

        if ppath_id is None:
            # No "Up to higher" link
            contents.insert(0, None)
        else:
            # Check to see if parent path ID exists
            if include_parent:
                contents.insert(0, FileSpec(chrooted_path.parent(), share, name="Up to higher level directory", company_name=company_name))
    return (page_count, contents)

