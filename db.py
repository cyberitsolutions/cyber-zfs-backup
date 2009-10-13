
import cherrypy
import psycopg2


def connect(thread_index):
    # Create a connection and store it in the current thread.
    # No, we don't use the thread_index var.
    cherrypy.thread_data.db = psycopg2.connect(database='zbm', host='localhost', user='zbm', password='zbm')

def commit():
    cherrypy.thread_data.db.commit()

def rollback():
    cherrypy.thread_data.db.rollback()

# Just execute, ignore the result.
def do(sql, vars=None):
    # Get cursor.
    c = cherrypy.thread_data.db.cursor()
    c.execute(sql, vars=vars)
    # Close cursor.
    c.close()

# Return a list of results.
def get(sql, vars=None):
    # Get cursor.
    c = cherrypy.thread_data.db.cursor()
    c.execute(sql, vars=vars)
    result = c.fetchall()
    # Close cursor.
    c.close()
    return result

# Returns a generator for a list of results.
def getgen(sql, vars=None, chunk_size=1000):
    # Get cursor.
    c = cherrypy.thread_data.db.cursor()
    c.execute(sql, vars=vars)

    done = False
    count = 0
    while not done:
        results = c.fetchmany(chunk_size)
        count += len(results)
        if len(results) == 0:
            done = True
        for res in results:
            yield res
    # Close cursor.
    c.close()

# Return a single result.
def get1(sql, vars=None):
    # Get cursor.
    c = cherrypy.thread_data.db.cursor()
    c.execute(sql, vars=vars)
    result = c.fetchone()
    # Close cursor.
    c.close()
    return result

