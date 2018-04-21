__author__ = 'GrMartin'

#!flask/bin/python

from app import app, socketio
socketio.run(app,  debug=True, use_reloader=False)