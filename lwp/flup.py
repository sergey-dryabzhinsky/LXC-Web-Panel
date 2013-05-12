'''
Flup launcher
'''

from flup.server.fcgi_fork import WSGIServer

class ScriptNameStripper(object):
   def __init__(self, app):
       self.app = app

   def __call__(self, environ, start_response):
       environ['SCRIPT_NAME'] = ''
       return self.app(environ, start_response)

def launch(app):
    app = ScriptNameStripper(app)
    WSGIServer(app, bindAddress=(app.config['ADDRESS'], app.config['POST'],)).run()

