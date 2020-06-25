Sales Pitch
===========
Like zfs-auto-snapshot_ or syncoid_, except that it

• does a recursive snapshot (so all datasets get the same timestamp)
• does a incremental *replication* push (so no arguments about who expired what)
• does timestamp-based snapshot names (YYYY-MM-DD...),
  not rotation-based snapshot names (daily.N).

Limitations:

• because of "zfs recv -R", you cannot have *different* retention policies on the backup server.
• because of recursive snapshot, you cannot "opt out" of snapshots for a boring dataset (e.g. zippy/zippy/var/tmp or zippy/zippy/var/cache).
• strongly encourages you *not* to start your datasets at the root of your pool (i.e. it wants -o mountpoint=/ on "zippy/zippy" not on "zippy").
• it's "some rando's crappy script", whereas zfs-auto-snapshot is a first-party OpenZFS thing with more mindshare.

.. _zfs-auto-snapshot: https://github.com/zfsonlinux/zfs-auto-snapshot
.. _syncoid: https://github.com/jimsalterjrs/sanoid


Boring Discussion
=================
Let each host have a hostname.
Let each host have a ZFS pool.
Let each host have a subset of that pool for its own datasets.
By default assume these names all match.

For example, on the host "zippy" we have a pool "zippy" and a tree within that "zippy". ::

    root@zippy:~# zippy zpool list
    NAME    SIZE  ALLOC   FREE  CKPOINT  EXPANDSZ   FRAG    CAP  DEDUP    HEALTH  ALTROOT
    zippy  5.45T   797G  4.68T        -         -     0%    14%  1.00x    ONLINE  -

    root@zippy:~# zfs get mountpoint zippy/zippy zippy/zippy/home zippy/zippy/root
    NAME              PROPERTY    VALUE       SOURCE
    zippy/zippy       mountpoint  /           local
    zippy/zippy/home  mountpoint  /home       local
    zippy/zippy/root  mountpoint  /root       local

Each host shall make daily snapshots of its own dataset (A/A) with RFC 33339 names.
Each host shall expire those snapshots according to its own expiry preferences (e.g. 7 dailies, 4 weeklies, 12 monthlies, and infinite yearlies).

No host shall expire snapshots from backups of another host (A/B).

If host A backs up host B, it logically ends up in A's A/B tree.
For example, zippy it backing up these hosts. ::

    root@zippy:~# zfs get refer -t filesystem
    NAME                                PROPERTY    VALUE     SOURCE
    zippy/host02                        referenced  24.0G     -
    zippy/host03                        referenced  26.3G     -
    zippy/host05                        referenced  38.9G     -
    zippy/host06                        referenced  12.2G     -
    zippy/mdhcp                         referenced  96K       -
    zippy/storage01                     referenced  16.6G     -
    [...]

Typically A.example.com backs up B.example.com, so for laziness we omit all the domains.
If we back up a host from a "foreign" domain, include it?
Or should we use FQDNs throughout?
(Can pools and datasets have "aliases", so that both FQDN and unqualified names work?)

All backups shall be "replication" backups, i.e.
if A/A has twelve snapshots, then
the backup on B/A must also have exactly those twelve snapshots.

Backups shall always be made over ssh.
For now, backups shall be push-based (not pull-based).

Backups shall be incremental except for the initial backup.
To compute the latest shared snapshot, the sender shall SSH into the receiver and ask "what snapshots do you have?"
It SHALL NOT simply guess.
If the sender and receiver both have data (i.e. initial backup has finished) AND have no snapshots in common, the backup process should abort noisly, not send a non-incremental.

FIXME: more discussion here.
