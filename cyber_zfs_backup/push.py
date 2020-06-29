#!/usr/bin/python3
import logging
import os
import subprocess

import arrow


def main(args):
    # 1. SSH to remote host and find out what the latest snapshot it has is.
    # 2. zfs send incremental from <that snapshot> to <current snapshot>
    # 3. pipe (2) into <SSH to remote host and zfs recv -F>.

    # FIXME: code duplication here (with itself, and with expire.py)
    # NOTE: we can't use libzfs on the far end of an SSH command, unless
    #       we do some kinda crazy shit where we send a python script over there.
    remote_snapshots_proc = subprocess.run(
        ['ssh', args.ssh_destination,
         *(['-F', args.ssh_config] if args.ssh_config else []),
         *(['sudo'] if args.use_sudo else []),
         'zfs', 'list', '-H',
         '-o', 'name',
         '-s', 'creation',
         '-t', 'snapshot',
         args.zfs_receive_dataset],
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    if (remote_snapshots_proc.returncode == 1 and
        'dataset does not exist' in remote_snapshots_proc.stderr):
        push_is_incremental = False
        if not args.force_non_incremental:
            logging.error(
                'remote dataset does not exist yet;'
                ' use --force-non-incremental to do a full sync')
            exit(os.EX_DATAERR)
    elif remote_snapshots_proc.returncode != 0:
        print(remote_snapshots_proc.stderr, end='', file=sys.stderr, flush=True)
        raise subprocess.CalledProcessError(
            returncode=remote_snapshots_proc.returncode,
            cmd=remote_snapshots_proc.args)
    else:
        push_is_incremental = True
        remote_snapshots_stdout = remote_snapshots_proc.stdout
        local_snapshots_stdout = subprocess.check_output(
            ['zfs', 'list', '-H',
             '-o', 'name',
             '-s', 'creation',
             '-t', 'snapshot',
             args.pool_or_dataset],
            universal_newlines=True)
        remote_snapshot_names = set(
            snapshot_name
            for line in remote_snapshots_stdout.splitlines()
            for dataset_name, _, snapshot_name in [line.partition('@')]
            if args.snapshot_name_re.fullmatch(snapshot_name))
        local_snapshot_names = set(
            snapshot_name
            for line in local_snapshots_stdout.splitlines()
            for dataset_name, _, snapshot_name in [line.partition('@')]
            if args.snapshot_name_re.fullmatch(snapshot_name))
        common_snapshot_names = remote_snapshot_names.intersection(local_snapshot_names)
        if not common_snapshot_names:
            logging.error(
                'local and remote datasets have no snapshots in common;'
                ' this should be impossible, human intervention required')
            exit(os.EX_DATAERR)
        latest_common_snapshot = max(common_snapshot_names, key=arrow.get)

    # Do an incremental replication send.
    with subprocess.Popen(
            ['zfs', 'send',
             # NOTE: "zfs send -n | zfs recv -n" is wrong, so only -n the recv.
             # *(['--dryrun'] if args.dry_run else []),
             *(['--verbose'] if args.loglevel < logging.WARNING else []),
             # FIXME: are these "nice to have" or "essential"?
             #        Do any have *important* backcompat issues?
             '--large-block', '--embed', '--compressed', '--raw', '--parsable',
             '--replicate',      # essential for our design!
             *(['-I', latest_common_snapshot] if push_is_incremental else []),
             # FIXME: args.snapshot_name assumes --action=snapshot has happened.
             #        When doing just --action=push, this snapshot doesn't exist!
             f'{args.pool_or_dataset}@{args.snapshot_name}'],
            stdout=subprocess.PIPE) as zfs_send_proc:
        subprocess.check_call(
            ['ssh', args.ssh_destination,
             *(['-F', args.ssh_config] if args.ssh_config else []),
             *(['sudo'] if args.use_sudo else []),
             'zfs', 'receive',
             *(['-n'] if args.dry_run else []),
             *(['-v'] if args.loglevel < logging.WARNING else []),
             *(['-F'] if push_is_incremental else []),  # essential for our design!
             # FIXME: do we need something like this to avoid A/A and A/B competing for the root mount???
             '-o', f'mountpoint=/srv/backup/{args.hostname}',
             '-o', f'canmount=noauto',
             '-o', f'readonly=on',
             # FIXME: use '-d' instead of args.zfs_receive_dataset?
             args.zfs_receive_dataset],
            stdin=zfs_send_proc.stdout)
        zfs_send_proc.wait()                         # FIXME: yuk!
        if zfs_send_proc.returncode:                 # FIXME: yuk!
            raise subprocess.CalledProcessError(     # FIXME: yuk!
                returncode=zfs_send_proc.returncode,  # FIXME: yuk!
                cmd=zfs_send_proc.args)               # FIXME: yuk!


if __name__ == '__main__':
    main()
