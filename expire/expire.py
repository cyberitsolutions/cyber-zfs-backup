#!/usr/bin/env python

import datetime
import sys
import os
import getopt
import time

(opts, args) = getopt.getopt(sys.argv[1:], "vd:")

if len(args) < 4:
    print "Usage: ", sys.argv[0], " [-v] <path> <d> <w> <m>"
    print "\tpath: directory containing backups"
    print "\td: number of daily backups to keep"
    print "\tw: weekly backups"
    print "\tm: monthly backups"
    print "\ty: yearly backups"
    sys.exit(1)

path = args[0]

dailies = int(args[1])
weeklies = int(args[2])
monthlies = int(args[3])
yearlies = int(args[4])

# Filenames are all UTC, so do these calculations in UTC too

today_utc = datetime.datetime.utcnow()
today = today_utc.date()

verbose = False
for (o,v) in opts:
    if (o == "-v"):
        verbose = True
    elif (o == "-d"):
        # hidden option for testing.
        today = datetime.datetime.strptime(v, "%Y-%m-%d").date()

datelist = []

curdate = today
daydiff = datetime.timedelta(days = -1)
for i in range(0, dailies):
    datelist.append(curdate)
    curdate += daydiff #daydiff should be -ve

# Weeks: back up to Sunday, remove 7 days at a time

wd = today.weekday()
curweek = today - datetime.timedelta(days = wd)
weekdiff = datetime.timedelta(days = 7)
for i in range(0, weeklies):
    if curweek not in datelist:
        datelist.append(curweek)
    curweek -= weekdiff

# Months: count manually
tm = today.month
ty = today.year

for i in range(0, monthlies):
    curmonth = datetime.date(ty, tm, 1)
    if curmonth not in datelist:
        datelist.append(curmonth)
    tm -= 1
    if tm == 0:
        tm = 12
        ty -= 1

for i in range(0, yearlies):
    curyear = datetime.date(ty, 1, 1)
    if curyear not in datelist:
        datelist.append(curyear)
    ty -= 1

# Go through the directory, find one file matching each date, delete the rest

dirs = os.listdir(path)

datelist = set(datelist)

keep = {} # actually not useful for anything
delete = {}


# Sample from the python docs
class UTC(datetime.tzinfo):
    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

for dir in dirs:
    # {{{ Don't use mtime, there's some weirdness on zhug
    #t = os.stat(os.path.join(path, dir)).st_mtime # mtime and ctime should be roughly identical
    #d = datetime.date.fromtimestamp(t)
    # }}}

    ts = time.strptime(dir, "%Y-%m-%dT%H:%M:%SZ")
    dt = datetime.datetime(ts[0], ts[1], ts[2], ts[3], ts[4], ts[5], ts[6], UTC())

    d = dt.date()

    if d in datelist:
        keep[d] = dir
        datelist.remove(d)
    else:
        # Keep the delete list searchable in case there are missed dates
        # This list will be used during deletion, so make sure multiple
        # backups on the same date won't mess it up.

        # This will break if there are enough backups on the same date
        # that they catch up with the real backups
        if d in delete:
            d = datetime.date.min
            while d in delete:
                d = d + datetime.timedelta(days = 1)
        delete[d] = dir

# If there's anything left in datelist it represents a gap in the backups.
# Search forwards to find a replacement. It's more likely a backup will run
# early than late.

# Helper function: find the lowest element in the list above elem
# list must be sorted
# This could also be implemented as a binary search


def nexthighest(list, elem):
    for e in list:
        if e > elem:
            return e
    return None

for remain in datelist:
    keys = delete.keys()
    keys.sort() # in-place sort, can't inline it
    replacement = nexthighest(keys, remain)

    if (replacement == None):
        # print >> sys.stderr, "No valid backup for ", remain
        pass # This is going to be fairly common, keep stdout clean
    else:
        # If the replacement backup is newer than another backup to be
        # kept, forget about it. 
        # i.e. 2010-05-01 was missing
        # 2010-05-30 is the next newest backup to be deleted
        # 2010-05-15 is being kept as well
        kkeys = keep.keys()
        kkeys.sort()
        next = nexthighest(kkeys, remain)
        if (replacement > next):
            # print >> sys.stderr, "No valid backup for ", remain
            continue
        keep[replacement] = delete[replacement]
        del delete[replacement]

if verbose:
    keepvs = keep.values()
    keepvs.sort()
    deletevs = delete.values()
    deletevs.sort()
    print "Keeping:\n", "\n".join(keepvs)
    print "Deleting:\n", "\n".join(deletevs)
else:
    print "\n".join(delete.values())

