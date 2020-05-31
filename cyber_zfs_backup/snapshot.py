#!/usr/bin/python3
import socket
import subprocess
import time


def main():
    print('FIXME')
    # FIXME: use args.now (and share it with the other subcommands)
    timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())  # FIXME: UGLY
    hostname = socket.gethostname()
    dataset = f'{hostname}/{hostname}'  # default thing to snapshot
    new_snapshot = f'{dataset}@{now}'
    subprocess.check_call(['zfs', 'snapshot',
                           '-r',  # recursive
                           # foo@bar --> make a new snapshot of "foo" called "bar"
                           new_snapshot])


if __name__ == '__main__':
    main()
