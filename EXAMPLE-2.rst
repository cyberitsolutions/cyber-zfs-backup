The server's name is "heavy"; it's backing up to "obese"::

    cyber@obese:~$ sudo adduser --system --group --home /etc/zfs-receive-heavy --shell /bin/sh   zfs-receive-heavy
    cyber@obese:~$ sudo chmod 100 /etc/zfs-receive-heavy
    cyber@obese:~$ sudo install -d -m 0100 -o zfs-receive-heavy -g zfs-receive-heavy /etc/zfs-receive-heavy/.ssh
    cyber@obese:~$ sudo tee /etc/zfs-receive-heavy/.ssh/authorized_keys  <<< 'restrict ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDu5QEJ5KaEun86JJrJemjoKN50rVFdU/8V2pEHOk67c cyber-zfs-backup push key from heavy to offsite'
    cyber@obese:~$ sudo chown -h zfs-receive-heavy: ~zfs-receive-heavy/.ssh/authorized_keys
    cyber@obese:~$ sudo chmod 400 ~zfs-receive-heavy/.ssh/authorized_keys

Tell server to allow zfs-receive-heavy to use SSH::

    cyber@obese:~$ sudoedit /etc/ssh/sshd_config.d/cyber-zfs-receive.conf
    AllowGroups zfs-receive-heavy
    cyber@obese:~$ sudo systemctl force-reload ssh

Configure SSH endpoint::

    cyber@heavy:~$ sudoedit /etc/ssh/cyber-zfs-backup.ssh_config
    Host obese offsite
      HostName obese.server.ron.vpn.cyber.com.au
      User zfs-receive-heavy
      BatchMode yes
      IdentityFile       /etc/ssh/cyber-zfs-backup.id_ed25519
      UserKnownHostsFile /etc/ssh/cyber-zfs-backup.known_hosts

Configure what and where to backup::

    cyber@heavy:~$ sudo systemctl edit cyber-zfs-backup
    [Service]
    ExecStart=
    ExecStart=cyber-zfs-backup --ssh-config=/etc/ssh/cyber-zfs-backup.ssh_config --ssh-destination=obese --zfs-receive-dataset=obese/heavy

Do trust-on-first-use host key checking::

    cyber@heavy:~$ sudo ssh -F /etc/ssh/cyber-zfs-backup.ssh_config -o BatchMode=no offsite whoami
    Are you sure you want to continue connecting (yes/no/[fingerprint])?

Confirm everything is working::

    cyber@heavy:~$ sudo ssh -F /etc/ssh/cyber-zfs-backup.ssh_config obese whoami
    zfs-receive-heavy

Grant temporary access to do the initial full push::

    # Need "receive,mount,create" at a minimum for "zfs receive".
    # Need others because I happen to set those.
    # NOTE: "userprop" covers com.sun:auto-snapshot (and others)

    cyber@obese:~$ sudo zfs allow -u zfs-receive-heavy receive,mount,create,quota,mountpoint,readonly,canmount,devices,userprop obese


    # FIXME: this STILL returns non-zero exit status!
    cyber@heavy:~$ sudo cyber-zfs-backup --ssh-config=/etc/ssh/cyber-zfs-backup.ssh_config --ssh-destination=obese --zfs-receive-dataset=obese/heavy --force-destroy-lots --force-non-incremental


Now the initial sync is done, move the permission "down" one::

    cyber@obese:~$ sudo zfs unallow -u zfs-receive-heavy                                                                          obese
    cyber@obese:~$ sudo zfs   allow -u zfs-receive-heavy receive,mount,create,quota,mountpoint,readonly,canmount,devices,userprop obese/heavy
    cyber@obese:~$ sudo zfs   allow -u zfs-receive-heavy receive,mount,create,quota,mountpoint,readonly,canmount,devices,userprop,rename obese/heavy

That STILL wasn't working, so I had to brute-force it and add **EVERY** permission::

    # THIS FAILS BECAUSE *SOME* PROPERY ISN'T ALLOWED; IT DOES NOT SAY WHICH ONE.
    cyber@obese:~$ sudo zfs allow -u zfs-receive-heavy "$(/sbin/zfs unallow |& sed -n '/^allow/,/^zoned/ s/[ \t].*//p' | tr -s '[:space:]' ,)" obese/heavy

    # DOING EACH ONE AT A TIME BY HAND, I SEE THAT ONLY ONE FAILED - "mlslabel".
    cyber@obese:~$ /sbin/zfs unallow |& sed -n '/^allow/,/^zoned/ s/[ \t].*//p' | while read -r x; do sudo zfs allow -u zfs-receive-heavy "$x" obese/heavy || echo "== $x =="; done
    cyber@obese:~$ /sbin/zfs allow  obese/heavy
    ---- Permissions on obese/heavy --------------------------------------
    Local+Descendent permissions:
            user zfs-receive-heavy aclinherit,aclmode,acltype,allow,atime,bookmark,canmount,casesensitivity,change-key,checksum,clone,compression,context,copies,create,dedup,defcontext,destroy,devices,diff,dnodesize,encryption,exec,filesystem_limit,fscontext,groupobjquota,groupobjused,groupquota,groupused,hold,keyformat,keylocation,load-key,logbias,mount,mountpoint,nbmand,normalization,overlay,pbkdf2iters,primarycache,projectobjquota,projectobjused,projectquota,projectused,promote,quota,readonly,receive,recordsize,redundant_metadata,refquota,refreservation,relatime,release,rename,reservation,rollback,rootcontext,secondarycache,send,setuid,share,sharenfs,sharesmb,snapdev,snapdir,snapshot,snapshot_limit,special_small_blocks,sync,userobjquota,userobjused,userprop,userquota,userused,utf8only,version,volblocksize,volmode,volsize,vscan,xattr,zoned

    # NOW WE CAN FINALLY GET AN INCREMENTAL PUSH WITH NO ERRORS?  YESSSS, EXITS WITHOUT ANY ERRORS FINALLY.
    # FIXME: narrow that allow list down again!!!
    cyber@heavy:~$ script -c 'sudo cyber-zfs-backup --ssh-config=/etc/ssh/cyber-zfs-backup.ssh_config --ssh-destination=obese --zfs-receive-dataset=obese/heavy --debug --force-destroy-lots'
