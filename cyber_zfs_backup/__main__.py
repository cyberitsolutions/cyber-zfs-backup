#!/usr/bin/python3
import argparse
import logging
import pathlib
import re
import socket

import arrow


# Ref. https://doc.python.org/whatsnew/3.0.html#removed-syntax
from .snapshot import main as snapshot
from .expire import main as expire
from .push import main as push


def main():
    args = parse_args()
    if 'snapshot' in args.actions:
        snapshot(args)
    if 'expire' in args.actions:
        expire(args)
    if 'push' in args.actions:
        push(args)


def parse_args():
    # The hostname is used as the default ZFS pool name and ZFS filesystem root.
    # The split... crap guarantees it's unqualified ("alice" not "alice.com").
    hostname = socket.gethostname().split('.')[0]
    parser = argparse.ArgumentParser()
    # NOTE: We want to name snapshots after a timestamp, preferably in RFC3339.
    #       ZFS does not allow "+" in snapshot names, so we operate in UTC (Zulu).
    #       2020-06-25T12:13:15Z not
    #       2020-06-25T12:13:30+10:00
    #
    #       to avoid "...+10:00" in local
    #       Local timestamps might have a "+10:00" timezone, and
    #       ZFS does not allow "+" in snapshot names.
    now = arrow.utcnow()
    parser.set_defaults(
        now=now,
        snapshot_name=now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        snapshot_name_re=re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'))
    parser.add_argument('--dry-run', '--no-act', '-n',
                        action='store_true')
    parser.add_argument('--verbose', '-v',
                        action='store_const',
                        dest='loglevel',
                        const=logging.INFO,
                        default=logging.WARNING)
    parser.add_argument('--debug',
                        action='store_const',
                        dest='loglevel',
                        const=logging.DEBUG,
                        default=logging.WARNING)
    parser.add_argument('--action',
                        nargs='*',
                        dest='actions',
                        choices=('snapshot', 'expire', 'push'),
                        default=['snapshot', 'expire', 'push'])
    parser.add_argument('--pool',
                        '--dataset',
                        dest='pool_or_dataset',
                        default=f'{hostname}/{hostname}',
                        metavar='POOL/DATASET')
    ## NOTE: these could be subcommand options, but
    ## there are not enough of them to bother setting up subcommands.
    # expire-specific options
    parser.add_argument('--force-destroy-lots', action='store_true')
    # push-specific options
    parser.add_argument('--ssh-destination', default='offsite')
    parser.add_argument('--zfs-receive-dataset', default=f'offsite/{hostname}')
    parser.add_argument('--ssh-config', type=pathlib.Path, help='for IdentityFile= et cetera')
    parser.add_argument('--use-sudo', action='store_true')

    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    # Work around not using subcommands, above.
    if 'expire' not in args.actions:
        if args.force_destroy_lots:
            logging.warn('--force-destroy-lots without --action=expire has no effect')
    if 'push' in args.actions:
        if args.ssh_config:
            logging.warn('--ssh-config without --action=push has no effect')

    # Ensure these strings are safe to shove down an SSH pipeline (i.e. through system(3)).
    for word in args.pool_or_dataset.split('/'):
        if not is_rfc952(word):  # FIXME: be less picky here
            raise RuntimeError('pool/dataset name is not safe to send over SSH!',
                               args.pool_or_dataset)

    return args


def is_rfc952(s):
    return bool(re.fullmatch('^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$', s))


if __name__ == '__main__':
    main()
