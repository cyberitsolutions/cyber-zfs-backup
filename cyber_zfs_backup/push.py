#!/usr/bin/python3
import subprocess


def main(args):
    # 1. SSH to remote host and find out what the latest snapshot it has is.
    # 2. zfs send incremental from <that snapshot> to <current snapshot>
    # 3. pipe (2) into <SSH to remote host and zfs recv -F>.

    raise NotImplementedError()
    new_snapshot = f'{args.pool_or_dataset}@{args.snapshot_name}'
    remote_dataset = 'FIXME'
    remote_snapshots = subprocess.check_output(
        ['ssh',
         '-F', '/etc/cyber-zfs-backup/ssh_config',
         '/sbin/zfs',
         # FIXME
         'zfs', 'list', '-H', '-t', 'snapshot', ],
        universal_newlines=True).splitlines()
    with subprocess.Popen(['zfs', 'send', 'FIXME']):
        pass


if __name__ == '__main__':
    main()
