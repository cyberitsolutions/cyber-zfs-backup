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

• https://openzfs.org/wiki/Projects/ZFS_Channel_Programs
• https://www.delphix.com/blog/delphix-engineering/zfs-channel-programs
• https://zfsonlinux.org/manpages/0.8.4/man8/zfs-program.8.html

UPDATE: this is a non-starter.  There is no access to date/time
functions, so there is no viable way to implement a retention policy
*inside* a ZFS channel program::

    # zfs program -j -n omega /dev/stdin <<< 'local s="" for k,v in pairs(_G) do s = s .. tostring(v) .. "\t" .. tostring(k) .. "\n" end return s' | jq --raw-output .return | sort
    1       EPERM
    10      ECHILD
    11      EAGAIN
    12      ENOMEM
    122     EDQUOT
    125     ECANCELED
    13      EACCES
    14      EFAULT
    15      ENOTBLK
    16      EBUSY
    17      EEXIST
    18      EXDEV
    19      ENODEV
    2       ENOENT
    20      ENOTDIR
    21      EISDIR
    22      EINVAL
    23      ENFILE
    24      EMFILE
    25      ENOTTY
    26      ETXTBSY
    27      EFBIG
    28      ENOSPC
    29      ESPIPE
    3       ESRCH
    30      EROFS
    31      EMLINK
    32      EPIPE
    33      EDOM
    34      ERANGE
    35      EDEADLK
    36      ENAMETOOLONG
    37      ENOLCK
    4       EINTR
    5       EIO
    6       ENXIO
    7       E2BIG
    8       ENOEXEC
    9       EBADF
    95      ENOTSUP
    Lua 5.2 _VERSION
    function: 00000000019d218e      select
    function: 00000000080fb5bf      rawequal
    function: 0000000009baa4e1      getmetatable
    function: 000000001d6dda9e      rawlen
    function: 0000000023b33d74      error
    function: 000000002ab2ecbf      ipairs
    function: 0000000039f68134      collectgarbage
    function: 000000004021bc73      type
    function: 000000004d872795      pairs
    function: 000000006d63bf09      tostring
    function: 00000000bcbba06f      rawset
    function: 00000000c3939123      rawget
    function: 00000000cf76f1f1      tonumber
    function: 00000000def8c887      assert
    function: 00000000f6551542      next
    function: 00000000f6f338ae      setmetatable
    table: 00000000210f0f67 _G
    table: 0000000024f294a7 coroutine
    table: 0000000054256033 string
    table: 000000006ad4255f zfs
    table: 00000000c49f1579 table

    # zfs program -j -n omega /dev/stdin <<< 'local s="" for k,v in pairs(_G.coroutine) do s = s .. tostring(v) .. "\t" .. tostring(k) .. "\n" end return s' | jq --raw-output .return | sort
    function: 0000000061b2c387      create
    function: 00000000661ce1c8      resume
    function: 000000006ba739ac      running
    function: 00000000abd16109      status
    function: 00000000adc4bf6c      yield
    function: 00000000dae48116      wrap

    # zfs program -j -n omega /dev/stdin <<< 'local s="" for k,v in pairs(_G.string) do s = s .. tostring(v) .. "\t" .. tostring(k) .. "\n" end return s' | jq --raw-output .return | sort
    function: 0000000036b575b7      reverse
    function: 0000000043205ae5      len
    function: 000000005b799fc2      gmatch
    function: 0000000060623f9f      lower
    function: 000000007ea57532      format
    function: 000000009f43d105      char
    function: 00000000b53b8e9f      upper
    function: 00000000ca8fc3f6      sub
    function: 00000000cae83a1e      byte
    function: 00000000d56ed26c      gsub
    function: 00000000e022c71e      rep
    function: 00000000ed52ab72      find
    function: 00000000f603fa1f      match

    # zfs program -j -n omega /dev/stdin <<< 'local s="" for k,v in pairs(_G.table) do s = s .. tostring(v) .. "\t" .. tostring(k) .. "\n" end return s' | jq --raw-output .return | sort
    function: 0000000025c2df24      concat
    function: 00000000469d5d8d      insert
    function: 00000000bb53dc13      sort
    function: 00000000bca821b7      unpack
    function: 00000000eb0870da      remove
    function: 00000000fe629b2f      pack

    # zfs program -j -n omega /dev/stdin <<< 'local s="" for k,v in pairs(_G.zfs) do s = s .. tostring(v) .. "\t" .. tostring(k) .. "\n" end return s' | jq --raw-output .return | sort
    function: 00000000489d3d0f      exists
    function: 0000000081600378      debug
    function: 00000000b872b118      get_prop
    table: 000000009a0e61fa list
    table: 00000000a5fe73ef sync
    table: 00000000aadedb25 check

    # zfs program -j -n omega /dev/stdin <<< 'local s="" for k,v in pairs(_G.zfs.list) do s = s .. tostring(v) .. "\t" .. tostring(k) .. "\n" end return s' | jq --raw-output .return | sort
    function: 000000005ddfc3ad      clones
    function: 00000000974d946f      properties
    function: 000000009c0bdb8f      children
    function: 000000009e00ec0f      system_properties
    function: 00000000c4414610      snapshots

    # zfs program -j -n omega /dev/stdin <<< 'local s="" for k,v in pairs(_G.zfs.sync) do s = s .. tostring(v) .. "\t" .. tostring(k) .. "\n" end return s' | jq --raw-output .return | sort
    function: 000000006dddd4e0      destroy
    function: 00000000c2f864fa      promote
    function: 00000000d039fee1      rollback
    function: 00000000e27c65ce      snapshot

    # zfs program -j -n omega /dev/stdin <<< 'local s="" for k,v in pairs(_G.zfs.check) do s = s .. tostring(v) .. "\t" .. tostring(k) .. "\n" end return s' | jq --raw-output .return | sort
    function: 000000000ff6dc42      snapshot
    function: 00000000ea051e3e      rollback
    function: 00000000ebbecb73      destroy
    function: 00000000ef0734c9      promote

Also (aside) if you blow the stack, "zfs program" segfaults (meh), but
also you get errors in dmesg and also all subsequent "zfs" commands
block in D state until you reboot! ::

    ## DO NOT RUN THIS DANGEROUS CODE!
    # <RhodiumToad> but I bet they didn't know about how gsub allocates a ton of stack
    # <RhodiumToad> there are three problematic functions that can do this, gsub is one of them
    # <RhodiumToad> hm, the table.concat one might not work on 5.2
    local function f(s) s:gsub(".", f) return "x" end f("foo")
    return tostring(setmetatable({},{__tostring=function(t) string.format("%s",t) end}))


FIXME: more discussion here.
