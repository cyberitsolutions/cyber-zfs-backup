#!/usr/bin/python3

import datetime
import os
import time
import pathlib

# NOTE: we use arrow (not datetime) because datetime.timedelta can't do weeks/months/years!
# NOTE: we use click (not argparse) gives us easier input validation.
import arrow                    # https://arrow.readthedocs.io
import click                    # https://click.palletsprojects.com


@click.command()
@click.argument('path', type=click.Path(exists=True,
                                        file_okay=False,
                                        resolve_path=True))
@click.argument('days', type=click.IntRange(min=0))
@click.argument('weeks', type=click.IntRange(min=0))
@click.argument('months', type=click.IntRange(min=0))
@click.argument('years', type=click.IntRange(min=0))
@click.option('--verbose', '-v', is_flag=True)
# NOTE: just use datefudge(1) instead of the old -d YYYY-MM-DD.
def main(path, days, weeks, months, years, verbose):
    # Sigh, click.Path doesn't use pathlib.
    path = pathlib.PosixPath(path)
    print('HELLO')

    # NOTE: like rsnapshot,
    #       the weeklies "start up" where the dailies "leave off", i.e. they do not overlap.
    #       (And so on for older rotations)
    #       UPDATE: actually they do overlap a little bit, because range(n)  is [0..n-1] not [1..n]!
    #
    # NOTE: jeremyc's code was manually doing weeklies as "go to Sunday, then walk back 7 days".
    #       Other stuff was even more klunky.
    #
    # NOTE: ZFS snapshots are in UTC, so we do *everything* in UTC.
    then = arrow.utcnow()
    goal_date_list = set()      # accumulator
    for i in range(days):
        then = then.shift(days=-i)
        goal_date_list.add(then)
    for i in range(weeks):
        then = then.shift(weeks=-i)
        goal_date_list.add(then)
    for i in range(months):
        then = then.shift(weeks=-i)
        goal_date_list.add(then)
    for i in range(months):
        then = then.shift(months=-i)
        goal_date_list.add(then)
    import pprint
    pprint.pprint(sorted(goal_date_list))



if __name__ == '__main__':
    main()
    exit()



# Go through the directory, find one file matching each date, delete the rest

dirs = os.listdir(path)

datelist = set(datelist)

keep = {}                       # actually not useful for anything
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
    # t = os.stat(os.path.join(path, dir)).st_mtime # mtime and ctime should be roughly identical
    # d = datetime.date.fromtimestamp(t)
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
                d = d + datetime.timedelta(days=1)
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
    keys = sorted(list(delete.keys()))
    replacement = nexthighest(keys, remain)

    if (replacement is None):
        # print >> sys.stderr, "No valid backup for ", remain
        pass    # This is going to be fairly common, keep stdout clean
    else:
        # If the replacement backup is newer than another backup to be
        # kept, forget about it.
        # i.e. 2010-05-01 was missing
        # 2010-05-30 is the next newest backup to be deleted
        # 2010-05-15 is being kept as well
        kkeys = sorted(list(keep.keys()))
        next = nexthighest(kkeys, remain)
        if (replacement > next):
            # print >> sys.stderr, "No valid backup for ", remain
            continue
        keep[replacement] = delete[replacement]
        del delete[replacement]

if verbose:
    keepvs = sorted(list(keep.values()))
    deletevs = list(delete.values())
    deletevs.sort()
    print("Keeping:\n", "\n".join(keepvs))
    print("Deleting:\n", "\n".join(deletevs))
else:
    print("\n".join(list(delete.values())))
