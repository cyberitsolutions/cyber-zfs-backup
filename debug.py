
def plog(msg):
    f = open('/tmp/plog.log', 'a')
    f.write("%s\n" % ( msg ))
    f.close()

