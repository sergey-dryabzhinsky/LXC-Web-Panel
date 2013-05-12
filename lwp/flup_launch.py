'''
Flup launcher
'''

from flup.server.fcgi_fork import WSGIServer

def launch(app):
    WSGIServer(app, bindAddress='./lwp.sock', umask=0007).run()

