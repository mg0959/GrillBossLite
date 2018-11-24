__author__ = 'GrMartin'
import os

# Storage Locations For Data
basedir = os.path.abspath(os.path.dirname(__file__))
DATASTORAGEDIR = os.path.join(basedir, 'app', 'data')

# CSRF
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
from sys import platform
if "linux" in platform: ARDUINO_PORT = "/dev/ttyACM"
elif platform == "win32": ARDUINO_PORT = "COM3"
ARDUINO_BAUDRATE = 9600

# Time interval to pull readings from arduino in seconds
SOCKET_SAMPLING_INTERVAL = 2 #when socket connected
RECORD_SAMPLING_INTERVAL = 5

#Set to true if testing without arduino
TESTING_NO_ARDUINO = False
CALIBRATE_THERM = False

#THERM Calibration Values
THERM_CONST_A = 572.17
THERM_CONST_B = -673.68
THERM_CONST_C = 386.37
THERM_CONST_D = 11.494
