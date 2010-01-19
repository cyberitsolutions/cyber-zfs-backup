-- Allow users with no company_name set to allow for global admins

alter table users alter column company_name drop not null;
