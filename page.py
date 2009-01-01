
import html
from html import head, body, title


def header(content="Header"):
    return html.div(content, att='class="header"')

def footer(content="Footer"):
    return html.div(content, att='class="footer"')

css_links = html.link(att='type="text/css" rel="stylesheet" href="/static/zbm.css"') \
    + html.link(att='type="text/css" rel="stylesheet" href="/static/tablesorter.css"')

js_links = html.script(att='type="text/javascript" src="/static/jquery-1.2.6.min.js"') \
    + html.script(att='type="text/javascript" src="/static/jquery.tablesorter.min.js"') \
    + html.script(att='type="text/javascript" src="/static/zbm.js"')

# Default page template.
def page(title, content=""):
    return html.html(
        head(html.title(title) + css_links + js_links)
        + body(header()
            + html.div(content, att='id="main"')
            + footer()))

