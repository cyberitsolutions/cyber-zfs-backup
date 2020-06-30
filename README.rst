Sales Pitch
===========
Like zfs-auto-snapshot_ or syncoid_, except that it

• does a recursive snapshot (so all datasets get the same timestamp)
• does an incremental *replication* push (so no arguments about who expired what)
• does timestamp-based snapshot names (YYYY-MM-DD...),
  not rotation-based snapshot names (daily.N).

Limitations:

• because of "zfs recv -R", you cannot have *different* retention policies on the backup server.
• because of recursive snapshot, you cannot "opt out" of snapshots for a boring dataset (e.g. zippy/zippy/var/tmp or zippy/zippy/var/cache).
• strongly encourages you *not* to start your datasets at the root of your pool (i.e. it wants -o mountpoint=/ on "zippy/zippy" not on "zippy").
• it's "some rando's crappy script", whereas zfs-auto-snapshot is a first-party OpenZFS thing with more mindshare.

.. _zfs-auto-snapshot: https://github.com/zfsonlinux/zfs-auto-snapshot
.. _syncoid: https://github.com/jimsalterjrs/sanoid


Get Started
===========

1. Run it by hand from the git clone::

       $ python3 -m cyber_zfs_backup --help

   Or make it into a deb package::

       $ apt-get build-dep ./
       $ debuild
       # apt install ../python3-cyber-zfs-backup_…_all.deb
       # cyber-zfs-backup --help

2. The .deb provides a systemd timer (cron job).

   To change *when* the job runs::

       # systemctl edit cyber-zfs-backup.timer
       [Timer]
       OnCalendar=
       OnCalendar=13:00

   To change *what* the job runs::

       # systemctl edit cyber-zfs-backup
       [Service]
       ExecStart=
       ExecStart=cyber-zfs-backup --dataset=morpheus/my-funny-dataset-name

3. If you don't need push support, add "--action snapshot expire".

   If you need push support, set up SSH:

   a. The deb includes some examples in /etc/ssh/.
      To use them, add "--ssh-config=/etc/ssh/cyber-zfs-backup.ssh_config".

   b. Make sure the remote host trusts /etc/ssh/cyber-zfs-backup.id_ed25519.
      ("ssh-copy-id -i", or edit authorized_keys by hand).

      FIXME: work out something like "restrict,command=rrsync -rw /".

   c. Make sure the local host trust's the remote host's host keys.
      Something like this::

         # ssh -F /etc/ssh/cyber-zfs-backup.ssh_config -o BatchMode=no offsite
         The authenticity of host 'offsite.example.com (172.16.17.18)' can't be established.
         ECDSA key fingerprint is SHA256:deadbeefbabedeadbeefbabedeafbeefbabedeadbee.
         Are you sure you want to continue connecting (yes/no)? yes
         Warning: Permanently added '203.7.155.208' (ECDSA) to the list of known hosts.




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


FIXME: Creation Date Metadata
-----------------------------
We use an easy-to-parse timestamp format in the snapshot name.
Why don't we just parse "zfs list -t snapshot -o creation" ?
Because that is outputting a timestamp format that is *GARBAGE* and impossible to parse safely.


FIXME: ZFS Channel Programs
---------------------------
Currently we just run zfs and parse the output, like savages.
We should use ZCP instead and get more atomicity.

https://openzfs.org/wiki/Projects/ZFS_Channel_Programs


FIXME: more discussion here.
