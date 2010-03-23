-- Add a "disabled" field to the users table without requiring changes to the rest of the system.
-- 1) Rename the table.
alter table users rename to all_users;

-- 2) Add the "disabled" field.
-- Note: Only "global" admins should read directly from the all_users table.
alter table all_users add column disabled boolean default false;

-- 3) Create a new view that shows non-disabled users with the old table name.
create view users as
select username, full_name, company_name, hashed_password, u.email
from
	all_users as u
-- left join to preserve company_name is null fields.
	left join companies on u.company_name = companies.name
where
	u.disabled = false and
-- Ensure that the user's company is not disabled.
	(u.company_name is null or
	companies.name is not null);
