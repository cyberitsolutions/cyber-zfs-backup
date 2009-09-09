
-- Okay, looks like we'll have to rebuild this table from scratch.

drop table filesystem_info;

create table filesystem_info (
    path text primary key,
    apparent_size bigint not null default 0,
    usage_size bigint not null default 0
);

