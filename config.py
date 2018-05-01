__author__ = 'GrMartin'
import os

# Storage Locations For Data
basedir = os.path.abspath(os.path.dirname(__file__))
DATASTORAGEDIR = os.path.join(basedir, 'app', 'data')

# Security Stuff
CSRF_ENABLED = True
SECRET_KEY = 'sm0keyMe4tIzGood'

# email server
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = "" #os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = "" #os.environ.get('MAIL_PASSWORD')

# administrator list
ADMINS = ['mg0959@gmail.com']

# Arduino Settings
ARDUINO_PORT = "COM3"
ARDUINO_BAUDRATE = 9600

# Celery Settings
#CELERY_BROKER_URL = 'redis://localhost:6379/0'
#CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Time interval to pull readings from arduino in seconds
SOCKET_SAMPLING_INTERVAL = 2 #when socket connected
RECORD_SAMPLING_INTERVAL = 10

#Set to true if testing without arduino
TESTING_NO_ARDUINO = False
