
-- Make filesystem_info table infinitely more useful :)

alter table filesystem_info add column path_id bigserial not null;
alter table filesystem_info add column ppath_id bigint;
