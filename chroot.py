
import os
import re


class BadChroot(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return self.value

class BadChrootPath(BadChroot):
    pass


class ChrootedPath:
    def __init__(self, chroot, path):
        # The chroot representation of the path must always be
        # absolute, ie. have a leading /.
        if len(path) > 0:
            if path[0] != '/':
                raise BadChrootPath("Chroot path %s is not absolute (no leading /)." % ( path ))
        else:
            raise BadChrootPath("Chroot path is empty.")

        self.chroot = chroot
        self.path = os.path.normpath(path)

        ( self.parent_dir, self.basename ) = os.path.split(self.path)

        self.join_path = re.sub('^/*', '', self.path)
        join_parent_dir = re.sub('^/*', '', self.parent_dir)
        
        # Must only realpath the containing directory.
        real_path = os.path.normpath(os.path.join(os.path.realpath(os.path.join(self.chroot.chroot_dir, join_parent_dir)), self.basename))

        if self.chroot.chroot_dir != real_path[0:len(self.chroot.chroot_dir)]:
            raise BadChrootPath("Path %s maps to real path %s which is not inside chroot dir %s." % ( path, real_path, self.chroot.chroot_dir ))

        self.real_path = real_path

        # Not acquired by default, usually not necessary.
        self.ancestors = None

    def has_parent(self):
        return self.path != '/'

    def parent(self):
        return self.chroot.chrooted_path(os.path.join(self.path, '..'))

    def child(self, filename):
        return self.chroot.chrooted_path(os.path.join(self.path, filename))

    def acquire_ancestors(self):
        """ Generates list of ancestors, nearest first. """
        if self.ancestors is None:
            if not self.has_parent():
                self.ancestors = []
            else:
                parent = self.parent()
                self.ancestors = [parent]
                parent.acquire_ancestors()
                self.ancestors.extend(parent.ancestors)
        # A list of ChrootedPath objects.
        return self.ancestors


class Chroot:
    def __init__(self, chroot_dir):
        self.chroot_dir = os.path.realpath(os.path.normpath(chroot_dir))

        if not os.path.isdir(self.chroot_dir):
            raise BadChroot("%s is not a directory." % ( self.chroot_dir ))

    def chrooted_path(self, path):
        return ChrootedPath(self, path)

