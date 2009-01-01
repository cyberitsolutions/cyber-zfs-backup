
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
# Classes.

# A quasi-chroot.
#class PathPrefix:
#    def __init__(self, path_prefix='/'):
#        if path_prefix[0] != '/':
#            raise BadPrefixError()
#        self.path_prefix = os.path.realpath(os.path.normpath(path_prefix))
#
#    def prefix(self, path):
#        np = self.normed(path)
#        # Remove the automatically-leading / before the join.
#        return os.path.join(self.path_prefix, np[1:])
#
#    def is_prefixed(self, real_path):
#        plog("is_prefixed(%s)" % ( real_path ))
#        return self.path_prefix == real_path[0:len(self.path_prefix)]
#
#    def is_accessible(self, path):
#        plog("is_accessible(%s)" % ( path ))
#        return self.is_prefixed(self._real(path))
#
#    def normed(self, path):
#        plog("normed(%s)" % ( path ))
#        subbed = '/' + re.sub('^\.?/+', '', path)
#        plog("subbed == '%s'" % ( subbed ))
#        return os.path.normpath(subbed)
#
#    def _real(self, path):
#        plog("_real(%s)" % ( path ))
#        ( containing_dir, basename ) = os.path.split(self.normed(path))
#        plog("containing_dir == %s ; basename == %s" % ( containing_dir, basename ))
#        # We want the containing_dir realpathed, but *not*
#        # the basename!
#        return os.path.join(os.path.realpath(self.prefix(containing_dir)), basename)
#
#    def real(self, path):
#        real_path = self._real(path)
#        if self.is_prefixed(real_path):
#            return real_path
#        # Someone's playing tricks with symlinks or .. dirs.
#        raise BadPrefixError("Real path %s doesn't match prefix %s" % ( real_path, self.path_prefix ))

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

