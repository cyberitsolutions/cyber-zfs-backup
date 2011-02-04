
-- Replace filesystem_info foreign keys to be ON DELETE CACADE

alter table filesystem_info drop constraint ppath_id__fk;

alter table filesystem_info add constraint ppath_id__fk foreign key ( ppath_id ) references filesystem_info ( path_id) ON DELETE CASCADE;
