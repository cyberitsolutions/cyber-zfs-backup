#!/usr/bin/python3
import subprocess


def main():
    print('FIXME')
    # FIXME: use args.now (and share it with the other subcommands)
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())  # FIXME: UGLY
    hostname = socket.gethostname()
    dataset = f'{hostname}/{hostname}'  # default thing to snapshot
    new_snapshot = f'{dataset}@{now}'
    # Make sure these strings are safe to shove down an SSH pipeline (i.e. through system(3)).
    assert all(word.isidentifier()
               for pool_or_dataset in args.pools_or_datasets
               for word in pool_or_dataset.split('/'))
    remote_snapshots = subprocess.check_output([
        'ssh',
        '-F', '/etc/cyber-zfs-backup/ssh_config',
        '/sbin/zfs', '
        ['zfs', 'list', '-H', '-t', 'snapshot',
             *(['-r'] + pools_or_datasets if pools_or_datasets else [])],
            universal_newlines=True).splitlines():

    with subprocess.Popen([
            'zfs', 'send', '

if __name__ == '__main__':
    main()
