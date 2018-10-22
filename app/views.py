__author__ = 'Grant Martin'
from app import app, Arduino, socketio
from flask import render_template, session, request, current_app
from flask_socketio import emit, disconnect
from config import SOCKET_SAMPLING_INTERVAL
import datetime, uuid

@app.route('/')
@app.route('/index')
@app.route('/gb')
def index():
    return render_template("index.html")

@app.route('/sandbox')
def sandbox():
    return render_template("sandbox.html")

@socketio.on('get arduinoStatus', namespace='/data')
def arduinoStatus():
    Arduino.updateReadings()
    emit('statusData', Arduino.makeStatusDict(), broadcast=True)

@socketio.on('get_smokeSessionData', namespace='/data')
def getSmokeSessionData():
    emit('smokeSessionData', Arduino.getDataFromSessionStart())


@socketio.on('send_arduino_cmd', namespace="/data")
def sendArduinoCmd(cmd_data):
    fan_speed = cmd_data["fan_speed"]
    print("got fan speed: ", fan_speed)
    Arduino.fan.adjustSpeed(cmd_data["fan_speed"])
    arduinoStatus()

@socketio.on('disconnect request', namespace='/data')
def disconnect_request():
    print('Disconnecting client')
    emit('cmd_response', {'response': 'Client Disconnected'})
    disconnect()

@socketio.on('startSession', namespace='/data')
def startSession():
    print("Start Session")
    Arduino.startSession()
    emit('cmd_response', {'response': 'Session Started'})

@socketio.on('endSession', namespace='/data')
def startSession():
    print("End Session")
    Arduino.stopSession()
    emit('cmd_response', {'response': 'Session Ended'})

@socketio.on('connect', namespace='/data')
def socket_connect():
    socketId = str(uuid.uuid4())
    current_app.clients.append(socketId)
    session['socketId'] = socketId
    print("Client Connected. Active sockets:", len(app.clients))
    Arduino.start_socket_interval_readings(SOCKET_SAMPLING_INTERVAL)
    emit('connected response', {'socketId': socketId})
    emit('new leader', {'leader':app.clients[0]}, broadcast=True)


@socketio.on('disconnect', namespace='/data')
def socket_disconnect():
    print("Disconnect funciton...")
    current_app.clients.remove(session['socketId'])
    if len(app.clients) < 1: Arduino.stop_socket_interval_readings()
    else: emit('new leader', {'leader':app.clients[0]})
    print('Client disconnected. Active Sockets:', len(app.clients))

@socketio.on_error(namespace='/data')
def data_error_handler(e):
    print('An error has occurred: ' + str(e))

