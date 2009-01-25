
import sys
import os
import datetime
import time
from os.path import join
import subprocess as sp

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

class FileSpec:
    def __init__(self, chrooted_path, name=False):
        self.chrooted_path = chrooted_path
        self.real_path = self.chrooted_path.real_path

        # Need to handle (non-basename) softlinks appropriately.
        self.basename = os.path.basename(self.chrooted_path.path)
        if not name:
            name = self.basename
        
        self.name = name
        self.display = name
        self.path = chrooted_path.path
        self.type = file_type(self.real_path)
        self.size = getlsize(self.real_path)
        # Not acquired by default, as it can be expensive.
        self.disk_usage = None
        self.mtime = getlmtime(self.real_path)

        if self.type == 'link':
            self.display = html.a(self.name, att='title="%s"' % ( cgi.escape(os.readlink(self.real_path), quote=True) ))
        elif self.type == 'dir':
            self.display = html.a(self.name, att='href="/browse?path=%s"' % ( cgi.escape(self.path, quote=True) ))

    def acquire_disk_usage(self):
        """ This can be expensive, so is not done by default. """
        if self.disk_usage is None:
            self.disk_usage = get_disk_usage(self.real_path)


# os.path.islink
# os.path.isdir
# os.path.isfile
def get_dir_contents(chrooted_path, sort_by="name", include_parent=True):
    real_dir = chrooted_path.real_path
    if not os.path.isdir(real_dir):
        raise InaccessiblePathError("%s is not an accessible directory." % ( chrooted_path.path ))

    dir_contents = []
    try:
        dir_contents = os.listdir(real_dir)
    except OSError, e:
        pass
    contents = [ FileSpec(chrooted_path.child(fname)) for fname in dir_contents ]

    contents.sort(filespec_cmp[sort_by])

    if include_parent:
        if chrooted_path.has_parent():
            pdir = chrooted_path.parent()
            parent_dir = FileSpec(pdir, name="Up to higher level directory")
            contents.insert(0, parent_dir)
        else:
            contents.insert(0, None)

    return contents

