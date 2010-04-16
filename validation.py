
import db

"""All these validation functions return None if any of their arguments are None."""

def user_exists(username):
    if username is None:
        return None
    else:
        return db.get1("select count(1) from users where username = %(username)s", vars())[0] > 0

def company_exists(company):
    if company is None:
        return None
    else:
        return db.get1("select count(1) from companies where name = %(company)s", vars())[0] > 0

def share_exists(share):
    if share is None:
        return None
    else:
        return db.get1("select count(1) from shares where name = %(share)s", vars())[0] > 0

def user_in_company(username, company):
    # TODO: Admins should be considered "in" companies they're not attached to in users table.
    if None in [username, company]:
        return None
    else:
        return db.get1("select count(1) from users where company = %(company)s and username = %(username)s", vars())[0] > 0

def share_in_company(share, company):
    if None in [share, company]:
        return None
    else:
        return db.get1("select count(1) from shares where company_name = %(company_name)s and name = %(share)s", vars())[0] > 0

def user_has_share(username, share):
    if None in [username, share]:
        return None
    else:
        return db.get1("select count(1) \
            from users join shares on users.company_name = shares.company_name \
            where username = %s(username) and shares.name = %(share)s" , vars()
        )[0] > 0
