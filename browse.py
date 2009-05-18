
import sys
import os
import datetime
import time
from os.path import join
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
    if db.get1("select count(1) from filesystem_info where path = %(path)s", vars()) > 0:
        db.do("update filesystem_info set usage_size = %(usage_size)s where path = %(path)s", vars())
    else:
        db.do("insert into filesystem_info ( path, usage_size ) values ( %(path)s, %(usage_size)s )", vars())

def update_or_insert_filesystem_info_apparent_size(path, apparent_size):
    if db.get1("select count(1) from filesystem_info where path = %(path)s", vars()) > 0:
        db.do("update filesystem_info set apparent_size = %(apparent_size)s where path = %(path)s", vars())
    else:
        db.do("insert into filesystem_info ( path, apparent_size ) values ( %(path)s, %(apparent_size)s )", vars())

def update_toplevel_path_apparent_size(path):
    """ Manually extracts du apparent-size of path and all
        subdirectories in database. """
    escaped_path = re.sub("'", "''", re.sub('%', "\\\\%", path))
    # This is a bit dicey, but let's see how well it works.
    rows = db.get("select path from filesystem_info where path like '%s'" % ( escaped_path + "%" ))
    got_usage = sets.Set()
    for r in rows:
        got_usage.add(r[0])

    lines = sp.Popen([cfg.GNU_DU_PATH, '--apparent-size', '--block-size=1', path], stdout=sp.PIPE).communicate()[0].split('\n')
    # The last one is always empty, so get rid of it.
    lines.pop()
    for line in lines:
        if line is not None:
            ( contents_size_str, du_path ) = line.split('\t', 1)
            if du_path in got_usage:
                # Ignore.
                pass
            else:
                contents_size = int(contents_size_str)
                update_or_insert_filesystem_info_contents_size(path, contents_size)
    db.commit()

def update_toplevel_path_disk_usage(path):
    """ Manually extracts du disk-usage-size of path and all
        subdirectories in database. """
    escaped_path = re.sub("'", "''", re.sub('%', "\\\\%", path))
    # This is a bit dicey, but let's see how well it works.
    rows = db.get("select path from filesystem_info where path like '%s'" % ( escaped_path + "%" ))
    got_usage = sets.Set()
    for r in rows:
        got_usage.add(r[0])

    # --apparent-size --block-size=1
    lines = sp.Popen([cfg.GNU_DU_PATH, '--block-size=1', path], stdout=sp.PIPE).communicate()[0].split('\n')
    # The last one is always empty, so get rid of it.
    lines.pop()
    for line in lines:
        if line is not None:
            ( du_size_str, du_path ) = line.split('\t', 1)
            if du_path in got_usage:
                # Ignore.
                pass
            else:
                du_size = int(du_size_str)
                db.do("insert into filesystem_info ( path, du_size ) values ( %(du_path)s, %(du_size)s )", vars())
    db.commit()

# Note: The contents of the supplied path are assumed to never ever
# change. Unless they're completely removed. This will be true for a
# ZFS snapshot, which is the use case normally expected.
def get_disk_usage(path):
    """ Checks to see if the path has an available du_size cached
        in our database - otherwise manually extracts it via
        really_get_disk_usage, stores result in database and returns. """
    row = db.get1("select du_size from filesystem_info where path = %(path)s", vars())
    db.commit()
    if row is None:
        du_size = really_get_disk_usage(path)
        db.do("insert into filesystem_info ( path, du_size ) values ( %(path)s, %(du_size)s )", vars())
        db.commit()
        return du_size
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
    # FIXME: Crude and kludgy way to exclude the leading '/' from path.
    return os.path.join(share, path[1:])

class FileSpec:
    def __init__(self, chrooted_path, share, name=False, disk_usage=None):
        self.chrooted_path = chrooted_path
        self.real_path = self.chrooted_path.real_path
        self.share = share

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
        self.size = getlsize(self.real_path)
        # Not acquired by default, as it can be expensive.
        self.disk_usage = disk_usage
        self.mtime = getlmtime(self.real_path)

        if self.type == 'link':
            self.display = html.a(self.name, att='title="%s"' % ( cgi.escape(os.readlink(self.real_path), quote=True) ))
        elif self.type == 'dir':
            self.display = html.a(self.name, att='href="/backup/browse?share=%s&amp;path=%s"' % ( cgi.escape(self.share, quote=True), cgi.escape(self.path, quote=True) ))
            ops1 = os.path.split(self.path)[1]
            ops2 = os.path.split(ops1)[1]
            if ops2 == "":
                pass
            else:
                self.size = self.acquire_disk_usage()

    def acquire_disk_usage(self):
        """ This can be expensive, so is not done by default. """
        if self.disk_usage is None:
            self.disk_usage = get_disk_usage(self.real_path)
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
def get_dir_contents(chrooted_path, share, sort_by="name", include_parent=True):
    real_dir = chrooted_path.real_path
    if not os.path.isdir(real_dir):
        raise InaccessiblePathError("%s is not an accessible directory." % ( chrooted_path.path ))

    dir_contents = []
    try:
        dir_contents = os.listdir(real_dir)
    except OSError, e:
        pass
    contents = [ FileSpec(chrooted_path.child(fname), share) for fname in dir_contents ]

    contents.sort(filespec_cmp[sort_by])

    if include_parent:
        if chrooted_path.has_parent():
            pdir = chrooted_path.parent()
            parent_dir = FileSpec(pdir, share, name="Up to higher level directory")
            contents.insert(0, parent_dir)
        else:
            # By convention, this is a directory of snapshots.
            # So use the ZFS snapshot creation times from zfs.
            zfs_fs = get_zfs_filesystem(real_dir)
            st = get_snapshot_timestamps(zfs_fs)
            for c in contents:
                c.mtime = st[c.name]
            contents.insert(0, None)

    return contents

