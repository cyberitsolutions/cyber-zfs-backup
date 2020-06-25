#!/usr/bin/python3
import subprocess


def main(args):
    new_snapshot = f'{args.pool_or_dataset}@{args.snapshot_name}'
    subprocess.check_call([
        *(['echo'] if args.dry_run else []),
        'zfs', 'snapshot',
        '-r',  # recursive
        # foo@bar --> make a new snapshot of "foo" called "bar"
        new_snapshot])


if __name__ == '__main__':
    main()
