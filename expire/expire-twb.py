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
        acc_keep, acc_kill = test_expire(now, snapshots)
        if len(acc_kill) > 2:
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


def test():
    logging.basicConfig(level=logging.INFO)
    import random

    now = arrow.now()

    def make_snapshot():
        # Our current backup code names snapshots (NB: Z = UTC)
        #   tank/foo/bar@2019-05-27T14:00:00Z
        # For this test, we'll just use the part after '@'.
        # arrow.get() understands that format without help.
        snapshots.append(
            str(now.to('UTC').strftime('%Y-%m-%dT%H:%M:%SZ')))

    # This variable stores our fake view of "the world", i.e.
    # just a list of snapshot names (as str objects).
    snapshots = []

    for i in range(1000):
        # Go forward 1 day, to simulate the progress of time.
        now = now.floor('day').shift(days=1)
        # Add some jitter.
        now = now.replace(hour=random.randrange(3),
                          minute=random.randrange(60))

        # Simulate a backup.  It succeeds 80% of the time.
        if random.random() <= 0.95:
            make_snapshot()
            logging.info('%s backup done', now)
        else:
            logging.warning('%s backup failed', now)

        # Add some jitter --- the time between the backup and the expiry
        now = now.shift(minutes=90*random.random())

        # Simulate the expiry.
        # We pass the list and IT WILL BE MUTATED to simulate the deletions.
        logging.info('%s expiry starts', now)
        test_expire(now, snapshots)

        # Simulate a rare second manual backup done by the sysadmin.
        # This lets us test a few "multiple snaps per day".
        if random.random() <= 0.02:
            logging.warning('%s sysadmin made manual backup(s)', now)
            now = now.shift(minutes=300*random.random())
            make_snapshot()


def decide_what_to_expire(now, snapshots):
    days, weeks, months, years = 7, 4, 12, 999
    acc_keep, acc_kill = [], []         # ACCUMULATOR

    snapshots.sort(key=arrow.get, reverse=True)  # most recent date first

    for snapshot in snapshots:
        prev_snapshot_ts = arrow.get(acc_keep[-1]) if acc_keep else None
        snapshot_ts = arrow.get(snapshot)
        if not acc_keep:
            logging.debug('%s %s first snapshot', now, snapshot_ts)
            keep = True
        elif snapshot_ts > now:
            logging.warning('%s %s future snapshot!', now, snapshot_ts)
            keep = True
        elif snapshot_ts.floor('day') == now.floor('day'):
            logging.debug('%s %s KEEP because today', now, snapshot_ts)
            keep = True

        # NOTE: these branches are IDENTICAL except for day/week/&c.
        elif days:              # we're looking for the next day
            if prev_snapshot_ts.floor('day') == snapshot_ts.floor('day'):
                # Day hasn't changed; keep looking
                keep = False
            else:
                # Day HAS changed!
                days = days - 1
                keep = True
        elif weeks:              # we're looking for the next week
            if prev_snapshot_ts.floor('week') == snapshot_ts.floor('week'):
                # Week hasn't changed; keep looking
                keep = False
            else:
                # Week HAS changed!
                weeks = weeks - 1
                keep = True
        elif months:              # we're looking for the next month
            if prev_snapshot_ts.floor('month') == snapshot_ts.floor('month'):
                # Month hasn't changed; keep looking
                keep = False
            else:
                # Month HAS changed!
                months = months - 1
                keep = True
        elif years:              # we're looking for the next year
            if prev_snapshot_ts.floor('year') == snapshot_ts.floor('year'):
                # Year hasn't changed; keep looking
                keep = False
            else:
                # Year HAS changed!
                years = years - 1
                keep = True
        else:
            # We don't care about any more rotations, so
            # just throw away anything else.
            # FIXME: we should keep "infinite" years by default, and
            #        raise an error in this case!
            raise RuntimeError()

        logging.info('%s %s %s (%s)',
                     now,
                     snapshot_ts,
                     'keep' if keep else 'KILL',
                     my_humanize(now, snapshot_ts))
        (acc_keep if keep else acc_kill).append(snapshot)

    return (acc_keep, acc_kill)


# This bodge helps you examine test_expire's output.
# It is something like arrow.Arrow.humanize().
# It is something like postgresql age().
def my_humanize(now: arrow.Arrow, ts: arrow.Arrow) -> str:
    days_different = now.toordinal() - ts.toordinal()
    s = 'today'
    if days_different == 0:
        return s
    s += ' +' if days_different > 0 else ' -'
    if days_different > 365:
        s += ' {} years'.format(days_different//365)
        days_different = days_different % 365
    if days_different > 31:     # shitty approximation!
        s += ' {} months'.format(days_different//31)
        days_different = days_different % 31
    if days_different > 7:     # shitty approximation!
        s += ' {} weeks'.format(days_different//7)
        days_different = days_different % 7
    if days_different:     # shitty approximation!
        s += ' {} days'.format(days_different)
    return s


if __name__ == '__main__':
    main()
