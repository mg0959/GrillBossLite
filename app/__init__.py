__author__ = 'GrMartin'

from flask import Flask, session
#from flask.ext.socketio import SocketIO
from flask_socketio import SocketIO
from flask_login import LoginManager
#from flask.ext.mail import Mail


app = Flask(__name__)
app.config.from_object('config')
app.clients = []

# SocketIO
socketio = SocketIO(app)


from config import MAIL_SERVER, MAIL_PASSWORD, MAIL_USERNAME, ADMINS, ARDUINO_BAUDRATE, ARDUINO_PORT, TESTING_NO_ARDUINO
#from error_log_email import TlsSMTPHandler

if TESTING_NO_ARDUINO:
    from tests import testArd
    Arduino = testArd()
else:
    from .controls import ArduinoTools
    Arduino = ArduinoTools(port=ARDUINO_PORT, baudrate=ARDUINO_BAUDRATE)


# set up log in system - For later
# lm = LoginManager()
# lm.init_app(app)
# lm.login_view = 'login'

# set up email capabilities - For later
# mail = Mail(app)

# set up logging
if not app.debug and MAIL_SERVER !='':
    import logging
    from logging.handlers import SMTPHandler
    credentials = None
    if MAIL_USERNAME or MAIL_PASSWORD:
        credentials = (MAIL_USERNAME, MAIL_PASSWORD)
    #mail_handler = TlsSMTPHandler((MAIL_SERVER, 587), 'Errors@grillBoss.com', ADMINS, 'GrillBoss Error!', credentials)
    #mail_handler.setLevel(logging.ERROR)
    #app.logger.addHandler(mail_handler)

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler('tmp/grillBoss.log', 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('GrillBoss startup')

from app import views