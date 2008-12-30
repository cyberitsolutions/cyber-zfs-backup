
import sys
import os
import datetime
import time
from os.path import join
import re

######################################################################
# Exceptions.

class BadPrefixError(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return self.value

class InaccessiblePathError(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return self.value

######################################################################
# Classes.

# A quasi-chroot.
class PathPrefix:
    def __init__(self, prefix='/'):
        if prefix[0] != '/':
            raise BadPrefixError()
        self.prefix = os.path.realpath(os.path.normpath(prefix))

    def is_prefixed(self, real_path):
        return self.prefix == real_path[0:len(self.prefix)]

    def is_accessible(self, path):
        return self.is_prefixed(self._real(path))

    def normed(self, path):
        return os.path.normpath(re.sub('^/+', '', path))

    def _real(self, path):
        ( containing_dir, basename ) = os.path.split(self.normed(path))
        # We want the containing_dir realpathed, but *not*
        # the basename!
        return os.path.normpath(os.path.join(os.path.realpath(os.path.join(self.prefix, containing_dir)), basename))

    def real(self, path):
        real_path = self._real(path)
        if self.is_prefixed(real_path):
            return real_path
        # Someone's playing tricks with symlinks or .. dirs.
        raise BadPrefixError("Real path %s doesn't match prefix %s" % ( real_path, self.prefix ))

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
    def __init__(self, path_prefix, path, name=False):
        self.path_prefix = path_prefix
        self.real_path = path_prefix.real(path)

        # Need to handle (non-basename) softlinks appropriately.
        self.basename = os.path.basename(path)
        if not name:
            name = self.basename
        
        self.name = name
        self.path = path
        self.type = file_type(self.real_path)
        self.size = getlsize(self.real_path)
        self.mtime = getlmtime(self.real_path)


# os.path.islink
# os.path.isdir
# os.path.isfile
def get_dir_contents(path_prefix, dir, sort_by="name", include_parent=True):
    if not path_prefix.is_accessible(dir):
        raise InaccessiblePathError("Path %s is not accessible." % ( dir ))
    real_dir = path_prefix.real(dir)
    if not os.path.isdir(real_dir):
        raise InaccessiblePathError("%s is not an accessible directory." % ( dir ))

    dir_contents = []
    try:
        dir_contents = os.listdir(real_dir)
    except OSError, e:
        pass
    contents = [ FileSpec(path_prefix, os.path.join(dir, fname)) for fname in dir_contents ]

    contents.sort(filespec_cmp[sort_by])

    if include_parent:
        pdir = os.path.join(dir, '..')
        parent_dir = None
        if path_prefix.is_accessible(pdir):
            parent_dir = FileSpec(path_prefix, pdir, name="Up to higher level directory")
        contents.insert(0, parent_dir)

    return contents

