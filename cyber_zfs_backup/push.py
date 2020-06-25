#!/usr/bin/python3
import logging
import subprocess

import arrow


def main(args):
    # 1. SSH to remote host and find out what the latest snapshot it has is.
    # 2. zfs send incremental from <that snapshot> to <current snapshot>
    # 3. pipe (2) into <SSH to remote host and zfs recv -F>.

    # FIXME: deal with the following cases:
    #          1. remote_dataset doesn't exist yet (--> do non-incremental replication send)
    #          2. remote_dataset exists but has no snaps (--> raise error)
    #          3. remote_dataset exists and has snaps, but no snaps in common (--> raise error)

    # FIXME: code duplication here (with itself, and with expire.py)
    # NOTE: we can't use libzfs on the far end of an SSH command, unless
    #       we do some kinda crazy shit where we send a python script over there.
    remote_snapshots_stdout = subprocess.check_output(
        ['ssh', args.ssh_destination,
         *(['-F', args.ssh_config] if args.ssh_config else []),
         *(['sudo'] if args.use_sudo else []),
         'zfs', 'list', '-H',
         '-o', 'name',
         '-s', 'creation',
         '-t', 'snapshot',
         args.zfs_receive_dataset],
        universal_newlines=True)
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
    latest_common_snapshot = max(common_snapshot_names, key=arrow.get)

    # Do an incremental replication send.
    with subprocess.Popen(
            ['zfs', 'send',
             *(['--dryrun'] if args.dry_run else []),
             *(['--verbose'] if args.loglevel < logging.WARNING else []),
             # FIXME: are these "nice to have" or "essential"?
             #        Do any have *important* backcompat issues?
             '--large-block', '--embed', '--compressed', '--raw', '--parsable',
             '--replicate',      # essential for our design!
             '-I', latest_common_snapshot,
             f'{args.pool_or_dataset}@{args.snapshot_name}'],
            stdout=subprocess.PIPE) as zfs_send_proc:
        subprocess.check_call(
            ['ssh', args.ssh_destination,
             *(['-F', args.ssh_config] if args.ssh_config else []),
             *(['sudo'] if args.use_sudo else []),
             'zfs', 'receive',
             *(['-n'] if args.dry_run else []),
             *(['-v'] if args.loglevel < logging.WARNING else []),
             '-F',              # essential for our design!
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
