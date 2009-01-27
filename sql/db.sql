
----------------------------------------------------------------------
create table companies (
    name varchar(32) primary key,
    long_name varchar(256) unique not null,

    check ( length(name) > 0 ),
    check ( name ~* '^[-a-zA-Z0-9_]+$' ),   -- Alphanumeric or [-_].
    check ( length(long_name) > 0 )
);
comment on table companies is
    'Company records.';

comment on column companies.name is
    'Primary key, short name of company - also used as a directory name.';
comment on column companies.long_name is
    'Long name of company.';

----------------------------------------------------------------------
create table shares (
    id serial primary key,
    name varchar(32) not null,
    company_name varchar(32) not null,

    unique ( name, company_name ),
    foreign key ( company_name ) references companies ( name ),
    check ( length(name) > 0 ),
    check ( name ~* '^[-a-zA-Z0-9_]+$' )    -- Alphanumeric or [-_].
);

comment on table shares is
    'Fileshares owned by a company.';

comment on column shares.name is
    'Name of the share - will also be used as a directory name.';
comment on column shares.company_name is
    'Reference to the relevant company by name.';

----------------------------------------------------------------------
create table users (
    username varchar(32) primary key,
    full_name varchar(256) not null,
    company_name varchar(32) not null,

    hashed_password varchar(256) not null,

    foreign key ( company_name ) references companies ( name ),
    check ( length(username) > 1 ),
    check ( username ~* '^[a-zA-Z0-9]+$' ), -- Alphanumeric or _.
    check ( length(hashed_password) > 0 )
);

comment on table users is
    'Users of the ZBM application.';

comment on column users.username is
    'Username of the user - usually a short no-space form of full name.';
comment on column users.full_name is
    'Full name of the user.';
comment on column users.company_name is
    'Reference to the relevant company by name.';
comment on column users.hashed_password is
    'MD5-hashed form of the user''s plaintext password.';

----------------------------------------------------------------------

-- One record for each restore in progress.
-- One restore at a time per user.
-- Enforce at application level, not database.
create table restores (
    id serial primary key,
    username varchar(32) not null,
    company_name varchar(32) not null,
    creation timestamp not null,
    active boolean default true not null,

    unique ( username, creation ),
    -- TODO: Add check constraint to enforce only one active restore per user.
    foreign key ( company_name ) references companies ( name ),
    foreign key ( username ) references users ( username )
);

-- Now *this* should be a larger table.
create table restore_files (
    restore_id integer not null,
    share_id integer not null,
    file_path text not null,
    -- A directory file means that we much be including
    -- *everything* underneath it (ie. recursive).
    -- If we don't want everything under the dir, we
    -- don't include the directory.
    du_size integer not null,

    foreign key ( restore_id ) references restores ( id ),
    foreign key ( share_id ) references shares ( id )
);

