#!/usr/bin/python3
import logging


# NOTE: we use arrow (not datetime) because
#       datetime.timedelta can't do weeks/months/years!
# NOTE: we use click (not argparse) gives us easier input validation.
import arrow                    # https://arrow.readthedocs.io
import click                    # https://click.palletsprojects.com


@click.command()
@click.argument('path',
                default='/tank',
                type=click.Path(exists=True,
                                file_okay=False,
                                resolve_path=True))
@click.argument('--days', default=7, type=click.IntRange(min=0))
@click.argument('--weeks', default=4, type=click.IntRange(min=0))
@click.argument('--months', default=6, type=click.IntRange(min=0))
@click.argument('--years', default=10, type=click.IntRange(min=0))
@click.option('--verbose', is_flag=True)
def main(path, days, weeks, months, years, verbose):
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
    pass


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


def test_expire(now, snapshots):
    days, weeks, months, years = 7, 4, 12, 10
    snapshots.sort(key=arrow.get, reverse=True)  # most recent date first

    before_len = len(snapshots)

    for prev_snapshot, snapshot in zip([None] + snapshots,
                                       snapshots):
        prev_snapshot_ts = arrow.get(prev_snapshot) if prev_snapshot else None
        snapshot_ts = arrow.get(snapshot) if snapshot else None
        if prev_snapshot is None:
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
            keep = False

        logging.info('%s %s %s (%s)',
                     now,
                     snapshot_ts,
                     'keep' if keep else 'KILL',
                     my_humanize(now, snapshot_ts))
        if keep:
            pass
        else:
            logging.debug('%s zfs destroy ...@%s', now, snapshot)
            # edit the simulation, rather than actually deleting
            snapshots.remove(snapshot)

    after_len = len(snapshots)
    if before_len - after_len > 1:
        logging.warning('%s multiple KILLs in this expiry!', now)


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


test()
