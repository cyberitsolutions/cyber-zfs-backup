#!/usr/bin/perl -w
#
# backup a single share

$hosted_backup_root_fs = "tank/hosted-backup";
$hosted_backup_backups_fs = "$hosted_backup_root_fs/backups";
$hosted_backup_config_dir = "/$hosted_backup_root_fs/config";

# screw you, Perl...
chomp ($backup_stamp = qx/date -u +%Y-%m-%dT%H:%M:%SZ/);

sub usage {
  print STDERR "usage: $0 client:user\@host:path:to:target\n";
  exit 1;
};

usage() unless $#ARGV == 0;

($client, $source_userhost, $source_path_colon) = split /:/, $ARGV[0], 3;
usage() unless $client =~ /^[a-z][a-z0-9]+$/;
usage() unless $source_userhost =~ /^[a-z]+@[.a-z0-9-]+$/;
($source_host = $source_userhost) =~ s/^.*@//;
usage() unless length($source_path_colon) > 0;
($source_path = ":$source_path_colon") =~ y#:#/#;

$keyfile = "$hosted_backup_config_dir/$ARGV[0]";
die "keyfile not found: $keyfile" unless -f $keyfile;

$rsync_source = "$source_userhost:$source_path";
$target_fs = "$hosted_backup_backups_fs/$client/$source_host:$source_path_colon";
$rsync_target_dir = "/$target_fs";

# $cmd_zfs_create = qq(zfs create -p $target_fs);
$cmd_rsync = qq(rsync --stats -e "ssh -i $keyfile" --inplace --numeric-ids --delete-after -aP $rsync_source/. $rsync_target_dir/. > $rsync_target_dir.$backup_stamp.out 2> $rsync_target_dir.$backup_stamp.err);
$cmd_zfs_snapshot = qq(zfs snapshot $target_fs\@$backup_stamp);
$cmd_cache_disk_usage = qq(env LD_LIBRARY_PATH=/usr/postgres/8.2/lib /tank/hosted-backup/bin/cache_directory_sizes $rsync_target_dir/.zfs/snapshot/$backup_stamp);

print "syncing $client from $rsync_source at $backup_stamp\n";
# don't create the filesystem - we want an error if it's not there yet.
# system $cmd_zfs_create;
system $cmd_rsync;
system $cmd_zfs_snapshot;
system $cmd_cache_disk_usage;
print "done.\n";
