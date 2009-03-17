
import sys
import os
import datetime
import time
from os.path import join
import subprocess as sp

import string
import re

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
def get_disk_usage(path):
    """ Returns the path's disk usage in bytes.

        Always recursive for directories, use with caution. """
    # Note: Assumes du(1) is in path (usually a safe assumption).
    output = sp.Popen(["du", '-sb', path], stdout=sp.PIPE).communicate()[0]
    return int(output.split('\t')[0])

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
            self.display = html.a(self.name, att='href="/browse?share=%s&amp;path=%s"' % ( cgi.escape(self.share, quote=True), cgi.escape(self.path, quote=True) ))

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
            contents.insert(0, None)

    return contents

