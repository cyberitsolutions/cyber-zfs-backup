
-- Allow NULL company name for global administrator users
-- (otherwise admins always need to be from a client company)

alter table users alter column company_name drop not null;

-- Add column for admin users

alter table users add column admin boolean default false not null;
