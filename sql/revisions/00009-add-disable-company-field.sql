-- Add a "disabled" field to the companies table without requiring changes to the rest of the system.
-- 1) Rename the table.
alter table companies rename to all_companies;

-- 2) Add the "disabled" field.
-- Note: Only "global" admins should read directly from the all_companies table.
alter table all_companies add column disabled boolean default false;

-- 3) Create a new view that shows non-disabled companies with the old table name.
create view companies as
select name, long_name, email
from
	all_companies
where
	disabled = false;
