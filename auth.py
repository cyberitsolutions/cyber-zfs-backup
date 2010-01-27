# -*- encoding: UTF-8 -*-
#
# Form based authentication for CherryPy. Requires the
# Session tool to be loaded.
#

import cherrypy
import urllib
import db
import md5
import os
import string

import zbm_cfg as cfg

import html
import page

# Keys stored in session.
USER_NAME = '_cp_username'
USER_FULLNAME = '_cp_fullname'
COMPANY_NAME = '_cp_company'
COMPANY_FULLNAME = '_cp_company_full'

def login_status():
    """ Returns (username, fullname, company_name, company_fullname) if logged in or None if not. """
    username = cherrypy.session.get(USER_NAME)
    if username is None:
        return None
    fullname = cherrypy.session.get(USER_FULLNAME)
    company_name = cherrypy.session.get(COMPANY_NAME)
    company_fullname = cherrypy.session.get(COMPANY_FULLNAME)
    return (username, fullname, company_name, company_fullname)

def reset_password(username, password):
    hashed_password = md5.md5(password).hexdigest()
    db.do("update users set hashed_password = %(hashed_password)s where username = %(username)s", vars())

    # Also update the htdigest zbm_passwords file.
    os.system("/etc/zbm/remove_user.sh " + username)

    # We need the company name here.
    company_name = cherrypy.session.get(COMPANY_NAME)
    hashed_expression = md5.md5(string.join([username, company_name, password], ':')).hexdigest()
    f = open('/etc/zbm/zbm_passwords', 'a')
    f.write("%s\n" % ( string.join([username, company_name, hashed_expression], ':') ))
    f.close()

    db.commit()

def check_credentials(username, password):
    """ Verifies credentials for username and password.
        Returns None on success or a string describing the error on failure. """
    # Adapt to your needs
    hashed_password = md5.md5(password).hexdigest()
    # users.company_name is null for global admins
    row = db.get1("select u.full_name, u.company_name, c.long_name from users u left join companies c on u.company_name = c.name where username = %(username)s and hashed_password = %(hashed_password)s", vars())
    #db.commit()
    if row is None:
        return ( "Incorrect username or password.", None )
    if row[1]:
        fullname = row[2]
    else:
        fullname = None

    return ( None, {
        'full_name':row[0],
        'company_name':row[1],
        'company_fullname':fullname
    } )
    # An example implementation which uses an ORM could be:
    # u = User.get(username)
    # if u is None:
    #     return u"Username %s is unknown to me." % username
    # if u.password != md5.new(password).hexdigest():
    #     return u"Incorrect password"

def check_auth(*args, **kwargs):
    """A tool that looks in config for 'auth.require'. If found and it
    is not None, a login is required and the entry is evaluated as a list of
    conditions that the user must fulfil."""
    conditions = cherrypy.request.config.get('auth.require', None)
    # format GET params
    get_params = urllib.quote(cherrypy.request.request_line.split()[1])
    if conditions is not None:
        username = cherrypy.session.get(USER_NAME)
        # We seem to need to do this in preparation for the redirect.
        cherrypy.request.base = cfg.BACKUP_BASE_URL
        if username:
            cherrypy.request.login = username
            for condition in conditions:
                # A condition is just a callable that returns True or False.
                if not condition():
                    # Send old page as from_page parameter.
                    raise cherrypy.HTTPRedirect(cfg.BACKUP_BASE_PATH + "/auth/login?from_page=%s" % get_params)
        else:
            # Send old page as from_page parameter
            raise cherrypy.HTTPRedirect(cfg.BACKUP_BASE_PATH + "/auth/login?from_page=%s" % get_params)

def user_is_global_admin(username=None):
    # If company_name is null, the user is a global admin.
    if username is None:
        username = cherrypy.session.get(USER_NAME)
    return db.get1("select count(1) from admins where username = %(username)s and company_name is null", vars())[0] > 0

def get_user_admin_companies(username=None, allow_null=False):
    if username is None:
        username = cherrypy.session.get(USER_NAME)
    if not allow_null and user_is_global_admin(username):
        return db.get("select name, long_name from companies")
    else:
        return db.get("select name, long_name from admins left outer join companies on name = company_name where username = %(username)s", vars())

def user_is_multi_admin(username=None):
    """Return True if the user is an admin in multiple companies, else return False."""
    if username is None:
        username = cherrypy.session.get(USER_NAME)
    return user_is_global_admin(username) or db.get1("select count(1) from admins where username = %(username)s", vars())[0] > 1

def user_is_admin(username=None, company=None):
    if user_is_global_admin(username):
        return True
    if username is None:
        username = cherrypy.session.get(USER_NAME)
    if company is None:
        company = cherrypy.session.get(COMPANY_NAME)
    # If the user is not a global admin and the company_name is STILL None, there's something wrong!
    return db.get1("select count(1) from admins where username = %(username)s and company_name = %(company)s", vars())[0] > 0

cherrypy.tools.auth = cherrypy.Tool('before_handler', check_auth)

def require(*conditions):
    """A decorator that appends conditions to the auth.require config
    variable."""
    def decorate(f):
        if not hasattr(f, '_cp_config'):
            f._cp_config = dict()
        if 'auth.require' not in f._cp_config:
            f._cp_config['auth.require'] = []
        f._cp_config['auth.require'].extend(conditions)
        return f
    return decorate


# Conditions are callables that return True
# if the user fulfills the conditions they define, False otherwise
#
# They can access the current username as cherrypy.request.login
#
# Define those at will however suits the application.

def member_of(groupname):
    def check():
        # replace with actual check if <username> is in <groupname>
        #return cherrypy.request.login == 'joe' and groupname == 'admin'
        return False
    return check

def name_is(reqd_username):
    return lambda: reqd_username == cherrypy.request.login

# These might be handy

def any_of(*conditions):
    """Returns True if any of the conditions match"""
    def check():
        for c in conditions:
            if c():
                return True
        return False
    return check

# By default all conditions are required, but this might still be
# needed if you want to use it inside of an any_of(...) condition
def all_of(*conditions):
    """Returns True if all of the conditions match"""
    def check():
        for c in conditions:
            if not c():
                return False
        return True
    return check


# Controller to provide login and logout actions

class AuthController(object):

    def on_login(self, username):
        """Called on successful login"""

    def on_logout(self, username):
        """Called on logout"""

    def get_loginform(self, username, msg="Enter login information.", from_page="/backup"):
        return page.mini_page("Datasafe/R - Login",
            html.h1("Login")
            + html.form(
                html.input(att='type="hidden" name="from_page" value="%s"' % ( from_page ))
                + html.p(msg)
                + html.table(
                    html.tbody(
                        html.tr([
                                html.th("Username:") + html.td(html.input(att='type="text" name="username" value="%s"' % ( username ))),
                                html.th("Password:") + html.td(html.input(att='type="password" name="password"')),
                                html.td(html.input(att='type="submit" value="Login"'),
                                    att='colspan="2"')
                            ]
                        )
                    ),
                    att='class="borderless"'),
                att='name="login" method="post" action="/backup/auth/login"')
            + html.script('document.getElementsByName("username")[0].focus();', att='language="javascript"'))


    @cherrypy.expose
    def login(self, username=None, password=None, from_page="/backup"):
        if username is None or password is None:
            return self.get_loginform("", from_page=from_page)

        ( error_msg, user ) = check_credentials(username, password)
        if not error_msg is None:
            return self.get_loginform(username, error_msg, from_page)
        else:
            sess = cherrypy.session
            sess[USER_NAME] = cherrypy.request.login = username
            sess[USER_FULLNAME] = user['full_name']
            sess[COMPANY_NAME] = user['company_name']
            sess[COMPANY_FULLNAME] = user['company_fullname']
            self.on_login(username)

            # We assume we're always using https.
            cherrypy.request.base = cfg.BACKUP_BASE_URL
            raise cherrypy.HTTPRedirect(from_page or cfg.BACKUP_BASE_PATH)

    @cherrypy.expose
    def logout(self, from_page="/backup"):
        sess = cherrypy.session
        username = sess.get(USER_NAME, None)
        sess[USER_NAME] = None
        sess[USER_FULLNAME] = None
        sess[COMPANY_NAME] = None
        sess[COMPANY_FULLNAME] = None
        if username:
            cherrypy.request.login = None
            self.on_logout(username)
        cherrypy.request.base = cfg.BACKUP_BASE_URL
        raise cherrypy.HTTPRedirect(from_page or cfg.BACKUP_BASE_PATH)

