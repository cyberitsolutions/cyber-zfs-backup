#!/usr/bin/perl -w
#
# backup a single legacy (pure rsync) share

$hosted_backup_root_fs = "tank/hosted-backup";
$hosted_backup_backups_fs = "$hosted_backup_root_fs/backups";
$hosted_backup_config_dir = "/$hosted_backup_root_fs/config-legacy";

# screw you, Perl...
chomp ($backup_stamp = qx/date -u +%Y-%m-%dT%H:%M:%SZ/);

sub usage {
  print STDERR "usage: $0 client:user\@host:module:sub:dir\n";
  exit 1;
};

usage() unless $#ARGV == 0;

($client, $source_userhost, $module_path_colon) = split /:/, $ARGV[0], 3;
usage() unless $client =~ /^[a-z][a-z0-9]+$/;
usage() unless $source_userhost =~ /^[a-z]+@[.a-z0-9-]+$/;
($source_host = $source_userhost) =~ s/^.*@//;
usage() unless length($module_path_colon) > 0;
($module_path = "$module_path_colon") =~ y#:#/#;

$passfile = "$hosted_backup_config_dir/$ARGV[0]";
die "passfile not found: $passfile" unless -f $passfile;

$rsync_source = "rsync://$source_userhost/$module_path";
$target_fs = "$hosted_backup_backups_fs/$client/$source_host:$module_path_colon";
$rsync_target_dir = "/$target_fs";

# $cmd_zfs_create = qq(zfs create -p $target_fs);
$cmd_rsync = qq(rsync --stats --password-file='$passfile' --inplace --numeric-ids --delete-after -aP '$rsync_source/.' '$rsync_target_dir/.' > '$rsync_target_dir.$backup_stamp.out' 2> '$rsync_target_dir.$backup_stamp.err');
$cmd_zfs_snapshot = qq(zfs snapshot '$target_fs\@$backup_stamp');
$cmd_cache_disk_usage = qq(env LD_LIBRARY_PATH=/usr/postgres/8.2/lib /tank/hosted-backup/bin/cache_directory_sizes '$rsync_target_dir/.zfs/snapshot/$backup_stamp');

print "syncing $client from $rsync_source at $backup_stamp\n";
# don't create the filesystem - we want an error if it's not there yet.
# system $cmd_zfs_create;
print "\n", $cmd_rsync, "\n";
#system $cmd_zfs_snapshot;
#system $cmd_cache_disk_usage;
print "done.\n";
