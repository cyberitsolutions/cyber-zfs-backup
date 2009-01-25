#
# A specification for files/directories to include from a
# collection - either tarball or zipfile.
#
# Uses the browse.FileSpec class.

import browse

class BadInclude(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return self.value


# Tracks paths to include and paths to exclude.
class RestoreSpec:
    def __init__(self):
        self.include_set = {}
        self.disk_usage_running_total = 0

    def is_included(self, file_spec):
        if file_spec.path in self.include_set:
            return True
        # First make sure the ancestors are actually acquired.
        file_spec.chrooted_path.acquire_ancestors()
        # Now check for ancestors in the include set.
        ancestor_paths = [ cp.path for cp in file_spec.chrooted_path.ancestors ]
        for ap in ancestor_paths:
            if ap in self.include_set:
                return True
        return False

    def include(self, file_spec):
        # This is a crucial part of the logic
        if self.is_included(file_spec):
            raise BadInclude("File %s is already included in the restore spec." % ( file_spec.path ))
        # We need the disk usage.
        file_spec.acquire_disk_usage()
        self.disk_usage_running_total += file_spec.disk_usage
        # Include it.
        self.include_set[file_spec.path] = file_spec

    def remove(self, file_spec):
        # Can only remove paths that are directly included.
        if not file_spec.path in self.include_set:
            raise BadInclude("File %s is not directly included in the restore spec." % ( file_spec.path ))
        # We need the disk usage.
        file_spec.acquire_disk_usage()
        self.disk_usage_running_total -= file_spec.disk_usage
        # Remove it.
        del self.include_set[file_spec.path]

