#!/usr/bin/python3
import logging
import subprocess
import collections


# NOTE: we use arrow (not datetime) because
#       datetime.timedelta can't do weeks/months/years!
# NOTE: we use click (not argparse) gives us easier input validation.
import arrow                    # https://arrow.readthedocs.io
import click                    # https://click.palletsprojects.com
# import libzfs_core            # https://pyzfs.readthedocs.io


@click.command()
# @click.option('--days', default=7, type=click.IntRange(min=0))
# @click.option('--weeks', default=4, type=click.IntRange(min=0))
# @click.option('--months', default=6, type=click.IntRange(min=0))
# @click.option('--years', default=10, type=click.IntRange(min=0))
@click.option('--verbose', is_flag=True)
def main(                       # days, weeks, months, years,
         verbose):
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING)

    # Get the list of snapshots.
    # For each snapshot (newest first),
    #
    #  * keep the first one
    #  * if days>0, discard snapshots until the day changes,
    #    then keep that one, and decrement days.
    #  * likewise for the other rotations,
    #  * otherwise, discard.
    #
    # This means rotations won't "share" a snapshot, e.g. 2017-01-01
    # can't count as BOTH a monthly and a daily.
    #
    # More importantly, that means that if there are missing backups,
    # or multiple backups per day, we won't get confused and over-delete.
    # ...I think.

    now = arrow.now()
    for dataset, snapshots in zfs_snapshots().items():
        snapshots_to_kill = decide_what_to_expire(now, snapshots)
        if len(snapshots_to_kill) > 2:
            logging.warning(
                'Multiple snaps marked for destruction! %s',
                dataset)
        # do the actual "zfs destroy" here.


def zfs_snapshots():     # -> {'tank/foo/bar': ['1970-01-01T...', ...], ...}
    # FIXME: use pyzfs instead of subprocess+csv!
    # NOTE: I thought of doing this in separate stages, like
    #         for dataset in zfs list -H:
    #           for snapshot in zfs list -H -t snapshot $dataset:
    #             pass
    #       Doing ONE BIG "zfs list" means less raciness (I hope).
    acc = collections.defaultdict(list)
    for line in subprocess.check_output(
            ['zfs', 'list', '-Htsnapshot',
             '-r', 'tank/hosted-backup/backups/djk',  # DEBUGGING
            ],
            universal_newlines=True).splitlines():
        snapshot_name, _, _, _, _ = line.strip().split('\t')
        dataset_name, snapshot_suffix = snapshot_name.split('@')
        try:
            arrow.get(snapshot_suffix)
        except arrow.parser.ParserError:
            logging.info(
                'Ignoring snapshot does not belong to us: %s', snapshot_name)
        else:
            acc[dataset_name].append(snapshot_suffix)
    return dict(acc)


def decide_what_to_expire(now, snapshots):
    # FIXME: stop hard-coding the retention policy here?
    # FIXME: support different policies for different datasets?
    # FIXME: this retention policy is too small!  Space is cheap.
    # NOTE: We ALWAYS keep at least one snapshot per year.
    #       If you really don't want this,
    #       you can do a manual expiry once a year.
    days, weeks, months = 7, 4, 12
    snapshots_to_keep, snapshots_to_kill = [], []  # ACCUMULATORS

    # Make sure the most recent date is first.
    # The original strings SHOULD sort correctly, but
    # sort them as arrows Just In Case.
    #
    # (We need to keep the strings around because str -> Arrow -> str
    # might not give the SAME string, and then "zfs destroy" would not
    # work.)
    snapshots.sort(key=arrow.get, reverse=True)
    for snapshot in snapshots:
        # NOTE: ts_prev is the last *KEPT* snapshot, not the last CANDIDATE snapshot.
        ts_prev = arrow.get(snapshots_to_keep[-1]) if snapshots_to_keep else None
        ts_cur = arrow.get(snapshot)

        keep = False
        # ALWAYS keep NEWEST snapshot (first run through loop).
        # This simplifies subsequent iterations.
        if not snapshots_to_keep:
            keep = True
        # NOTE: day/week/month branches are IDENTICAL except for the interval.
        elif days:              # we're looking for the next day
            if ts_cur.floor('day') != ts_prev.floor('day'):
                days -= 1
                keep = True     # Day HAS changed, keep this one.
            # else day hasn't changed, so keep = False (default)
        elif weeks:              # we're looking for the next week
            if ts_cur.floor('week') != ts_prev.floor('week'):
                keep = True     # Week HAS changed, keep this one.
                weeks -= - 1
            # else week hasn't changed, so keep = False (default)
        elif months:              # we're looking for the next month
            if ts_cur.floor('month') != ts_prev.floor('month'):
                keep = True     # Month HAS changed, keep this one.
                months -= 1
            # else month hasn't changed, so keep = False (default)
        else:         # We ALWAYS keep at least one snapshot per year.
            if ts_cur.floor('year') != ts_prev.floor('year'):
                keep = True     # Year HAS changed, keep this one.
            # else year hasn't changed, so keep = False (default)

        # Add to one list or the other.
        # NOTE: we only *return* the kill list, but
        #       we use the keep list internally for the next iteration
        #       through this loop.
        logging.debug('%s "%s"', 'keep' if keep else 'KILL', snapshot)
        (snapshots_to_keep if keep else snapshots_to_kill).append(snapshot)

    return snapshots_to_kill


if __name__ == '__main__':
    main()
