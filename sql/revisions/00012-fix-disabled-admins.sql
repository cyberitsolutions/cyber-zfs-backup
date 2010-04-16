-- The admins table should not display users who are disabled.
-- 1) Rename the table.
alter table admins rename to all_admins;

-- 2) Create a new view that shows non-disabled admins with the old table name.
create view admins as
select id, a.username, a.company_name
from
	all_admins as a
	join users on a.username = users.username;
