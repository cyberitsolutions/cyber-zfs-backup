
import sys
import os
import datetime
import time
from os.path import join
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
        self.path = chrooted_path.path
        self.type = file_type(self.real_path)
        self.size = getlsize(self.real_path)
        self.mtime = getlmtime(self.real_path)

        if self.type == 'link':
            self.name = html.a(self.name, att='title="%s"' % ( cgi.escape(os.readlink(self.real_path)) ))


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

