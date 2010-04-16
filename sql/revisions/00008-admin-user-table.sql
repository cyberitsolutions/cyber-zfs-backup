-- Table to manage who is an admin user for what company(s)

create table admins (
    -- Since we need *something* to be a primary key and company_name can be
    -- null ...
    id serial primary key,
    username varchar(32) not null,
    company_name varchar(32),
    
    unique ( username, company_name ),
    foreign key ( username ) references users ( username ),
    foreign key ( company_name ) references companies ( name )
);
