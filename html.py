# This is a very very _very_ simple HTML library.
#
# Usage:
#
# html(head(title("Title"))
#     + body(h1("Heading")
#     + p("Paragraph")
#     + hr()
#     + p("Footer", att="style='font-size:0.9em'")))
#
# => "<html><head><title>Title</title></head><body><h1>Heading</h1><p>Paragraph</p><hr></hr><p style='font-size:0.9em'>Footer</p></body></html>"
#
# If you think it's too simple to use, feel free to go away and use
# some fancy templating "solution" like Mako or Cheetah. Have fun.


######################################################################
# Default doctype.
html_4_01_strict = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">'


######################################################################
# HTML tag handler.
def tag(tagname, items, attributes='', close=True, newline=True):
    if attributes != '': attributes = ' ' + attributes
    start = '<' + tagname + attributes + '>'
    end = ''
    if close: end = '</' + tagname + '>'
    retval = ''
    if type(items) != type([]):
        items = [items]
    for i in items:
        retval += "%s%s%s" % ( start, i, end )
    if newline:
        return retval + "\n"
    else:
        return retval


######################################################################
# HTML tag wrapper functions.

# Formatting.
def a(data='', att=''): return tag('a', data, att, newline=False)
def b(data='', att=''): return tag('b', data, att, newline=False)
def i(data='', att=''): return tag('i', data, att, newline=False)
def em(data='', att=''): return tag('em', data, att, newline=False)
def strong(data='', att=''): return tag('em', data, att, newline=False)

def p(data='', att=''): return tag('p', data, att)
def br(data='', att=''): return tag('br', data, att, close=False)

def h1(data='', att=''): return tag('h1', data, att)
def h2(data='', att=''): return tag('h2', data, att)
def h3(data='', att=''): return tag('h3', data, att)
def h4(data='', att=''): return tag('h4', data, att)

# Structural.
def html(data='', att='', doctype=html_4_01_strict):
    return doctype + tag('html', data, att)
def head(data='', att=''): return tag('head', data, att)
def body(data='', att=''): return tag('body', data, att)
def title(data='', att=''): return tag('title', data, att)
def div(data='', att=''): return tag('div', data, att)
def span(data='', att=''): return tag('span', data, att)
def link(data='', att=''): return tag('link', data, att, close=False)
def script(data='', att=''): return tag('script', data, att)

# Tables.
def table(data='', att=''): return tag('table', data, att)
def thead(data='', att=''): return tag('thead', data, att)
def tbody(data='', att=''): return tag('tbody', data, att)
def tfoot(data='', att=''): return tag('tfoot', data, att)
def tr(data='', att=''): return tag('tr', data, att)
def td(data='', att=''): return tag('td', data, att)
def th(data='', att=''): return tag('th', data, att)

# Misc.
def hr(data='', att=''): return tag('hr', data, att, close=False)
def img(data='', att=''): return tag('img', data, att, close=False, newline=False)

# Lists.
def ul(data='', att=''): return tag('ul', data, att)
def ol(data='', att=''): return tag('ol', data, att)
def li(data='', att=''): return tag('li', data, att)

def dl(data='', att=''): return tag('dl', data, att)
def dt(data='', att=''): return tag('dt', data, att)

# Forms.
def form(data='', att=''): return tag('form', data, att)
def input(data='', att=''): return tag('input', data, att, close=False, newline=False)
def textarea(data='', att=''): return tag('textarea', data, att)
def option(data='', att=''): return tag('option', data, att)
def select(data='', att=''): return tag('select', data, att)

# Entities
def nbsp(n=1):
    return "&nbsp;" * n

