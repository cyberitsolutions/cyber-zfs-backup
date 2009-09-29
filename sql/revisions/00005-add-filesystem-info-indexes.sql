
-- Add necessary index and (nullable) foreign key.

alter table filesystem_info add constraint path_id__idx unique ( path_id );

alter table filesystem_info add constraint ppath_id__fk foreign key ( ppath_id ) references filesystem_info ( path_id );

