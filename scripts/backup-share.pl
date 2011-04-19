#!/usr/bin/perl -w
#
# backup a single share

$hosted_backup_root_fs = "tank/hosted-backup";
$hosted_backup_backups_fs = "$hosted_backup_root_fs/backups";
$hosted_backup_config_dir = "/$hosted_backup_root_fs/config";
$hosted_backup_config_hack_dir = "/$hosted_backup_root_fs/config-ugly-hacks";
$hosted_backup_config_email_dir = "/$hosted_backup_root_fs/config-email-logs";

$rsync_standard_args = "-aP --stats --inplace --numeric-ids --delete-after --delete-excluded --compress --human-readable --exclude proc/ --exclude sys/ --exclude dev/";

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

$authfile = "$hosted_backup_config_dir/$ARGV[0]";
die "authfile not found: $authfile" unless -f $authfile;

$recipients = "";
$email_notifications_file = "$hosted_backup_config_email_dir/$ARGV[0]";
if ( -r $email_notifications_file && ! -z $email_notifications_file ) {
  open EMAIL_RECIPIENTS, $email_notifications_file;
  $recipients = <EMAIL_RECIPIENTS>;
  chomp $recipients;
  close EMAIL_RECIPIENTS;
}
$recipients = "hosted-backups\@cyber.com.au $recipients";

$config_hack_file = "$hosted_backup_config_hack_dir/$ARGV[0]";
$config_hack = '';
if ( -T $config_hack_file ) {
  open(CONFIG_HACK_FILE, $config_hack_file) || die "couldn't read config hack file:";
  $config_hack = join(" ", map {s/\s*(#.*)?\s*$//; $_} <CONFIG_HACK_FILE>);
  close CONFIG_HACK_FILE;
}

$rsync_source = "$source_userhost:$source_path";
$rsync_transport_auth = "-e 'ssh -i $authfile -o ServerAliveInterval=30 -o ServerAliveCountMax=10'";
$target_fs = "$hosted_backup_backups_fs/$client/$source_host:$source_path_colon";
$rsync_target_dir = "/$target_fs";

# XXX THIS IS FUCKED. IT IS NOW TIME TO THROW THIS OUT AND START AGAIN WITH AN ACTUAL SPEC.
$rsync_standard_args = "-aP --stats --numeric-ids --delete-after --delete-excluded --compress --human-readable --exclude proc/ --exclude sys/ --exclude dev/" if $source_userhost eq "root\@vanilla.cyber.com.au";
$rsync_standard_args = "-aP --stats --numeric-ids --delete-after --delete-excluded --compress --human-readable --exclude proc/ --exclude sys/ --exclude dev/" if $source_userhost eq "root\@white.cyber.com.au";
$rsync_transport_auth = "-e 'ssh -p 5250 -i $authfile -o ServerAliveInterval=30 -o ServerAliveCountMax=10'" if $client eq "palletcontrol";
$rsync_transport_auth = "-e '/tank/hosted-backup/openssh-5.6p1/bin/ssh -p 2222 -i $authfile -o ServerAliveInterval=30 -o ServerAliveCountMax=10'" if $client eq "worklogic";
# $rsync_standard_args = "-aP --stats --numeric-ids --delete-after --delete-excluded --compress --human-readable --exclude proc/ --exclude sys/ --exclude dev/" if $client eq "aunic";

# $cmd_zfs_create = qq(zfs create -p $target_fs);
$cmd_rsync = qq(rsync $rsync_standard_args $rsync_transport_auth $config_hack '$rsync_source/.' '$rsync_target_dir/.' > '$rsync_target_dir.$backup_stamp.out' 2> '$rsync_target_dir.$backup_stamp.err');
$cmd_zfs_snapshot = qq(zfs snapshot '$target_fs\@$backup_stamp');
$cmd_cache_disk_usage = qq(env LD_LIBRARY_PATH=/usr/postgres/8.2/lib /tank/hosted-backup/bin/cache_directory_sizes '$rsync_target_dir/.zfs/snapshot/$backup_stamp');
$cmd_email_notification = qq((cat /${hosted_backup_root_fs}/email-header.txt; tail -20 "$rsync_target_dir.$backup_stamp.out" | perl -ne '\$go += /^Number/; print if \$go'; echo; cat "$rsync_target_dir.$backup_stamp.err") | /usr/bin/mailx -s 'backup log $ARGV[0]' $recipients);

print "$client from $rsync_source starting $backup_stamp\n";
# don't create the filesystem - we want an error if it's not there yet.
# system $cmd_zfs_create;
system $cmd_rsync;
system $cmd_zfs_snapshot;
system $cmd_email_notification;
system $cmd_cache_disk_usage;
print "$client from $rsync_source done.\n";
