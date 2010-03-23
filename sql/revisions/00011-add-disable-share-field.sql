-- Add a "disabled" field to the shares table without requiring changes to the rest of the system.
-- 1) Rename the table.
alter table shares rename to all_shares;

-- 2) Add the "disabled" field.
-- Note: Only "global" admins should read directly from the all_shares table.
alter table all_shares add column disabled boolean default false;

-- 3) Create a new view that shows non-disabled shares with the old table name;
create view shares as
select id, s.name, company_name
from
	all_shares as s
-- ensure that the share's company is also not disabled.
	join companies on s.company_name = companies.name
where
	s.disabled = false;
