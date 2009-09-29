
import string

import html
from html import head, body, title

import auth


def mini_header(content=None):
    return html.div(html.nbsp(), att='class="header"')

def header(content=None):
    logout_link = html.a("Logout", att='href="/backup/auth/logout"')
    if content is None:
        status = auth.login_status()
        if status is None:
            content = ''
        else:
            content = "%s (%s)" % ( html.a(status[0], att='href="/backup/user"'), status[1] )
            if status[3]:
                company = " of %s" % status[3]
            else:
                company = " the admin"
            content += company
    menu_bar = string.join([html.a("Browse Shares", att='href="/backup/browse"'), html.a("View Cart", att='href="/backup/show"')], " | ")
    return html.div(html.span(content + html.nbsp(3) + logout_link + html.nbsp(), att='class="logout"') + html.nbsp() + menu_bar, att='class="header"')

def footer(content="Datasafe/R"):
    return html.div(content, att='class="footer"')

css_links = html.link(att='type="text/css" rel="stylesheet" href="/backup/static/zbm.css"') \
    + html.link(att='type="text/css" rel="stylesheet" href="/backup/static/tablesorter.css"')

js_links = html.script(att='type="text/javascript" src="/backup/static/jquery-1.2.6.min.js"') \
    + html.script(att='type="text/javascript" src="/backup/static/jquery.tablesorter.min.js"') \
    + html.script(att='type="text/javascript" src="/backup/static/jquery.growl.js"') \
    + html.script(att='type="text/javascript" src="/backup/static/zbm.js"')

# Default page template.
def page(title, content=""):
    return html.html(
        head(html.title(title) + css_links + js_links)
        + body(header()
            + html.div(content, att='id="main"')
            + footer()))

# Mini-header-using page template.
def mini_page(title, content=""):
    return html.html(
        head(html.title(title) + css_links + js_links)
        + body(mini_header()
            + html.div(content, att='id="main"')
            + footer()))

