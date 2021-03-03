This is a server that's using cyber-zfs-backup to snapshot itself.
In this naming scheme, the pool is named after the host, and then the local rootfs is also named after the host (thus light/light).
This makes it obvious when host A holds backups of host B, because they're then just A/B.
In a conventional setup, light/light would be called something like rpool/ROOT/ubuntu-deadbeefbabe (I think).

::

    cyber@light:~$ /sbin/zfs list -o keystatus,encryption,compression,compressratio,used,usedbydataset,usedbysnapshots,refer,name
    KEYSTATUS    ENCRYPTION   COMPRESS        RATIO   USED  USEDDS  USEDSNAP     REFER  NAME
    -            off          zstd            1.83x  2.02G    192K        0B      192K  light
    available    aes-256-gcm  zstd            1.83x  2.00G   1.76G     3.50M     1.76G  light/light
    available    aes-256-gcm  zstd            1.00x  1.34M    320K        0B      320K  light/light/home
    available    aes-256-gcm  zstd            1.00x  1.02M    784K      264K      784K  light/light/home/cyber
    available    aes-256-gcm  zstd            1.45x  4.81M   4.34M      488K     4.34M  light/light/root
    available    aes-256-gcm  zstd            1.54x   236M    320K        0B      320K  light/light/var
    available    aes-256-gcm  zstd            1.29x   221M    221M        0B      221M  light/light/var/cache
    available    aes-256-gcm  zstd            6.66x  13.0M   1.47M     1.89M     1.47M  light/light/var/log
    available    aes-256-gcm  zstd            7.21x  9.62M   2.89M     6.73M     2.89M  light/light/var/log/journal
    available    aes-256-gcm  zstd            1.00x  1.16M    656K      528K      656K  light/light/var/tmp

This is a server that's receiving incremental encrypted snapshots from light.
It also has some legacy rsync-based backups that are encrypted at rest, but need a decrypt key at run time (boo!)

::

    cyber@obese:~$ /sbin/zfs list -o keystatus,encryption,compression,compressratio,used,usedbydataset,usedbysnapshots,refer,name
    KEYSTATUS    ENCRYPTION   COMPRESS        RATIO   USED  USEDDS  USEDSNAP     REFER  NAME
    -            off          zstd            1.54x   141G     96K        0B       96K  obese
    unavailable  aes-256-gcm  zstd            1.83x  1.77G   1.54G     3.05M     1.54G  obese/light
    unavailable  aes-256-gcm  zstd            1.00x  1012K    184K       72K      184K  obese/light/home
    unavailable  aes-256-gcm  zstd            1.00x   756K    536K      220K      536K  obese/light/home/cyber
    unavailable  aes-256-gcm  zstd            1.48x  3.43M   3.17M      264K     3.17M  obese/light/root
    unavailable  aes-256-gcm  zstd            1.51x   230M    184K       72K      184K  obese/light/var
    unavailable  aes-256-gcm  zstd            1.29x   219M    219M       72K      219M  obese/light/var/cache
    unavailable  aes-256-gcm  zstd            6.95x  9.95M   1.16M     1.13M     1.16M  obese/light/var/log
    unavailable  aes-256-gcm  zstd            7.37x  7.66M   2.73M     4.92M     2.73M  obese/light/var/log/journal
    unavailable  aes-256-gcm  zstd            1.00x   680K    496K      184K      496K  obese/light/var/tmp
    -            off          zstd            2.21x  3.13G   1.47G     1.08G     1.47G  obese/obese
    -            off          zstd            1.04x   724K     96K        0B       96K  obese/obese/home
    -            off          zstd            1.04x   628K    160K      468K      160K  obese/obese/home/cyber
    -            off          zstd            1.30x  3.46M   1.60M     1.86M     1.60M  obese/obese/root
    -            off          zstd            2.51x   596M     96K        0B       96K  obese/obese/var
    -            off          zstd            2.20x   560M   37.5M      522M     37.5M  obese/obese/var/cache
    -            off          zstd            7.94x  34.1M   1.73M     3.82M     1.73M  obese/obese/var/log
    -            off          zstd            8.12x  28.5M   7.08M     21.4M     7.08M  obese/obese/var/log/journal
    -            off          zstd            1.00x  1.42M    152K     1.27M      152K  obese/obese/var/tmp
    available    aes-256-gcm  zstd            1.52x   136G    244K        0B      244K  obese/zebra
    available    aes-256-gcm  zstd            1.18x  3.37G   3.37G        0B     3.37G  obese/zebra/alpha.cyber.com.au:.
    available    aes-256-gcm  zstd            1.53x   133G    133G        0B      133G  obese/zebra/omega.cyber.com.au:.

I tried to minimize how much access the sender has to the receiver's system.
Here's what I came up with so far::

    cyber@light:~$ grep ^ /etc/systemd/system/cyber-zfs-backup.service.d/override.conf
    [Service]
    ExecStart=
    ExecStart=cyber-zfs-backup --use-sudo --ssh-config=/etc/ssh/cyber-zfs-backup.ssh_config --ssh-destination=obese --zfs-receive-dataset=obese/light

    cyber@light:~$ grep -vE '^[[:space:]]*(#|$)' /etc/ssh/cyber-zfs-backup.ssh_config
    Host obese offsite
      HostName REDACTED
      Port REDACTED
      User zfs-receive
      BatchMode yes
      IdentityFile       /etc/ssh/cyber-zfs-backup.id_ed25519
      UserKnownHostsFile /etc/ssh/cyber-zfs-backup.known_hosts

    # FIXME: rename this to "cyber-zfs-receive"?
    cyber@obese:~$ getent passwd zfs-receive
    zfs-receive:x:108:116:SSH account for sudo zfs list/recv:/etc/zfs-receive:/bin/sh

    cyber@obese:~$ getent group zfs-receive
    zfs-receive:x:116:

    # FIXME: move to /etc/ssh/sshd_config.d/cyber-zfs-receive.conf
    cyber@obese:~$ grep AllowGroups /etc/ssh/sshd_config
    AllowGroups REDACTED
    AllowGroups zfs-receive

    cyber@obese:~$ sudo find ~zfs-receive -exec ls -hlds {} +
    1.0K d--x------ 3 zfs-receive zfs-receive   3 Feb 10 02:00 /etc/zfs-receive
    1.0K d--x------ 2 zfs-receive zfs-receive   4 Feb 10 01:51 /etc/zfs-receive/.ssh
    5.0K -r-------- 1 zfs-receive zfs-receive 864 Feb 10 03:02 /etc/zfs-receive/.ssh/authorized_keys

    cyber@obese:~$ sudo cat ~zfs-receive/.ssh/authorized_keys
    # FIXME: force the commands to start with "sudo zfs list" or "sudo zfs receive"?
    #        I don't want to make separate "list" and "receive" keys, so we EITHER
    #        need something like a rrsync wrapper, OR we need to use SSH certificates.
    #        An SSH certificate can include MULTIPLE forced commands at once, AND the user cannot change them.
    #
    # FIXME: zfs has built-in support for limited escalation commands.  Use that instead of sudo?
    restrict ssh-ed25519 REDACTED cyber-zfs-backup push key from light to offsite

    # FIXME: this whitelist is too broad
    cyber@obese:~$ sudo cat /etc/sudoers.d/cyber-zfs-receive
    zfs-receive ALL=(root:root) NOPASSWD: /sbin/zfs list *, /sbin/zfs receive *
