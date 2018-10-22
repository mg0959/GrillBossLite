__author__ = 'GrMartin'

from .decorators import *
import threading, time, datetime
import serial, csv
from config import *
from app import socketio

##############################
# Arduino Commands
#
# B = Byte
# B1 B2
# 9  9 - Turn off All
# 1  1 - Send current values (read sensors)
# B  0 - Turn off object B
# B  1 - Turn on object  B
# B  X - Set object B to X
#
# Serial calls to Arduino always return all current values
# (message is [2*number of elements, 18] bytes long)
##############################

class SocketTracker():
    def __init__(self):
        self.sockets=[]


class ArduinoConnectionError(Exception):
    def __str__(self):
        return "Could not connect to arduino"

class FanSpeedOptionError(Exception):
    def __str__(self):
        return "Fan speed option not valid"

class ArduinoTools:
    def __init__(self, port, baudrate):
        self.serial_lock = threading.RLock()
        self.sessionStartTime = None
        self.lastUpdate = datetime.datetime.now()
        self.dataStorageDir = DATASTORAGEDIR
        self.socketCount = 0

        # keep track of class objects by assigned ID
        self.id_obj_list = {}

        #add arduino elements
        self.fan = Fan("f1", self)
        self.id_obj_list["f1"] = self.fan

        self.thermometers = []
        for i in range(8): # 8 Thermometers
            self.thermometers.append(Thermometer("T"+str(i+1), self))
            self.id_obj_list["T"+str(i+1)] = self.thermometers[i]

        self.intervalRecordReadingStopFlag = threading.Event()
        self.intervalRecordReadingStopFlag.set()

        self.intervalSocketReadingStopFlag = threading.Event()
        self.intervalSocketReadingStopFlag.set()

        self.initiateSerialConnection(port, baudrate)

    def startSession(self):
        if not self.sessionStartTime: self.sessionStartTime = datetime.datetime.now()
        self.start_interval_record_readings(RECORD_SAMPLING_INTERVAL)

    def stopSession(self):
        self.stop_interval_record_readings()
        self.sessionStartTime = None

    def initiateSerialConnection(self, port, baudrate):
        self.ser = serial.Serial(port, baudrate)
        i = 0
        while self.ser.in_waiting < 1:
            time.sleep(0.1)
            i +=1
            if i > 120*10:
                raise ArduinoConnectionError()

        self.ser.write("1111".encode())
        time.sleep(0.5)
        self.ser.flushInput()


    def talk_with_arduino(self, msg):
        self.serial_lock.acquire()
        # send serial msg
        if self.ser.in_waiting > 0 : self.ser.flushInput()
        self.ser.write(msg.encode())
        i = 0
        while self.ser.in_waiting < 1:
            time.sleep(0.1)
            i+=1
            if i > 120*10:
                raise ArduinoConnectionError()
        returnMsg = self.ser.readline().decode() # Read response line
        self.updateArduino(returnMsg)
        self.serial_lock.release()

    def updateArduino(self, updateStr):
        updateDict = dict([x.split(":") for x in updateStr.strip().split(",")])
        self.serial_lock.acquire()
        self.lastUpdate = datetime.datetime.now()
        for key, value in updateDict.items():
            self.id_obj_list[key].updateStatus(value)
        self.serial_lock.release()

    def updateReadings(self):
        # call to update arduino values
        msg = "1111"
        self.talk_with_arduino(msg=msg)

    def turnOffAll(self):
        msg = "0000"
        self.talk_with_arduino(msg)

    def start_interval_record_readings(self, interval):
        if not self.intervalRecordReadingStopFlag.isSet():
            print("Interval record readings already running")
            return 0
        print("Starting Inverval readings")

        @timedLoopCall(interval)
        def sample_status(self, interval):
            print(time.ctime(), "\t", end="")
            if interval < 10:
                if self.serial_lock.acquire(blocking=False):
                    self.updateReadings()
                    self.writeCurrentDataToCSV()
                    self.serial_lock.release()
                else:
                    print("serial locked...")
            else:
                self.updateReadings()
                self.writeCurrentDataToCSV()

        self.intervalRecordReadingStopFlag =  sample_status(self, interval) #Return stop flag

    def stop_interval_record_readings(self):
        self.intervalRecordReadingStopFlag.set()

    def start_socket_interval_readings(self, interval):
        if not self.intervalSocketReadingStopFlag.isSet():
            print("Interval readings already running")
            return 0
        print("Starting Inverval readings")

        @timedLoopCall(interval)
        def sample_status(self):
            print(time.ctime(), "\t", end="")
            self.updateReadings()
            socketio.emit('statusData', self.makeStatusDict(), broadcast=True, namespace='/data')
            print("socketio emit from thread")

        self.intervalSocketReadingStopFlag =  sample_status(self) #Return stop flag

    def stop_socket_interval_readings(self):
        self.intervalSocketReadingStopFlag.set()

    def writeCurrentDataToCSV(self):
        data = [self.lastUpdate.strftime("%Y-%m-%d %H:%M:%S"),
                self.fan.status]

        for thermo in self.thermometers:
            data.append(thermo.temp)

        datafileDir = os.path.join(self.dataStorageDir, str(self.lastUpdate.year), str(self.lastUpdate.month))
        if not os.path.exists(datafileDir):
            os.makedirs(datafileDir)
        dataFilename = os.path.join(datafileDir, "%02d.csv") % self.lastUpdate.day

        try:
            if not os.path.isfile(dataFilename):
                f = open(dataFilename, "w", newline="\n", encoding="utf-8")
                f.write("Local Time,fan speed")
                for i in range(len(self.thermometers)):
                    f.write(",T"+str(i+1))
                f.write("\n")
            else:
                f = open(dataFilename, "a", newline="\n", encoding="utf-8")
            csvF = csv.writer(f, delimiter=",")
            csvF.writerow(data)
            f.close()
        except:
            print("Unable to write to csv!")

    def makeStatusDict(self):
        self.serial_lock.acquire()
        statusDict = {"sessionStartTime": "off",
                      "time": self.lastUpdate.strftime("%Y-%m-%d %H:%M:%S"),
                      "FAN": self.fan.status}
        if self.sessionStartTime is not None:
            statusDict["sessionStartTime"] = self.sessionStartTime.strftime("%Y-%m-%d %H:%M:%S")
        for i in range(8):
            statusDict["T" + str(i + 1)] = self.thermometers[i].temp
        self.serial_lock.release()

        return statusDict

    def superceded_getDataFromSessionStart(self):
        print("\n\n****************Getting Session Data")
        if not self.sessionStartTime:
            print("No Session Running")
            return []


        datapoints = []
        max_days = 5
        for day_count in range(max_days):

            file_date = self.sessionStartTime + datetime.timedelta(day_count,0)
            if file_date > datetime.datetime.now(): break# file date is in the future
            else:
                datafileDir = os.path.join(self.dataStorageDir, str(file_date.year), str(file_date.month))
                dataFilename = os.path.join(datafileDir, "%02d.csv") % (file_date.day)
                if not os.path.exists(dataFilename):
                    print(dataFilename, "does not exist.... skipping")
                else:
                    with open(dataFilename, "r") as csvFile:
                        i=1
                        for row in csv.reader(csvFile):
                            if i > 1: # not the header row
                                datapoint_datetime = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                                if self.sessionStartTime < datapoint_datetime: # time is in session time
                                    datapoint = {"time": datapoint_datetime.strftime("%Y-%m-%d %H:%M:%S")}
                                    for j in range(8):
                                        datapoint["T" + str(j + 1)] = row[j+2]
                                    datapoints.append(datapoint)
                                else: pass # skip this line since its out of session time
                            i += 1
        return datapoints

    def getDataFromSessionStart(self):
        print("\n\n****************Getting Session Data")
        if not self.sessionStartTime:
            print("No Session Running")
            return []


        datasets = {}
        for i in range(1,9):
            datasets["T"+str(i)] = []
        max_days = 5
        for day_count in range(max_days):
            file_date = self.sessionStartTime + datetime.timedelta(day_count,0)
            if file_date > datetime.datetime.now(): break# file date is in the future
            else:
                datafileDir = os.path.join(self.dataStorageDir, str(file_date.year), str(file_date.month))
                dataFilename = os.path.join(datafileDir, "%02d.csv") % (file_date.day)
                if not os.path.exists(dataFilename):
                    print(dataFilename, "does not exist.... skipping")
                else:
                    with open(dataFilename, "r") as csvFile:
                        i=1
                        for row in csv.reader(csvFile):
                            if i > 1: # not the header row
                                datapoint_datetime = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                                if self.sessionStartTime < datapoint_datetime: # time is in session time
                                    time_pt = datapoint_datetime.strftime("%Y-%m-%d %H:%M:%S")
                                    for j in range(1, 9):
                                        datasets["T" + str(j)].append({"t":time_pt, "y": row[j+1]})
                                else: pass # skip this line since its out of session time
                            i += 1
        return datasets



# Combination Elements

class FireBox:
    def __init__(self, ard_ids, ard_parent):
        self.heatingElement = HeatingElement(ard_ids[0], ard_parent)
        self.woodAuger = WoodAuger(ard_ids[1], ard_parent)

    def returnIdObj(self, ard_id):
        if self.heatingElement.id == ard_id:
            return self.heatingElement
        elif self.woodAuger.id == ard_id:
            return self.woodAuger
        else: return None

class ColdSmoker:
    def __init__(self, ard_ids, ard_parent):
        self.heatingElementBottom = HeatingElement(ard_ids[0], ard_parent)
        self.heatingElementTop = HeatingElement(ard_ids[1], ard_parent)
        self.airPump = AirPump(ard_ids[2], ard_parent)

    def returnIdObj(self, ard_id):
        if self.heatingElementBottom.id == ard_id:
            return self.heatingElementBottom
        elif self.heatingElementTop.id == ard_id:
            return self.heatingElementTop
        elif self.airPump.id == ard_id:
            return self.airPump
        return None

# Base Elements

class Thermometer:
    def __init__(self, ard_id, ard_parent):
        assert len(ard_id) <= 2
        self.id = ard_id
        self.ard_parent = ard_parent
        self.temp = -1

    def updateStatus(self, ardReturnVal):
        # read thermometers... need to add the voltage conversion algorithm here
        ardReturnVal = int(ardReturnVal)/1023
        self.temp = round((866.88*ardReturnVal**3 - 1263.2*ardReturnVal**2+653.62*ardReturnVal - 0.58)*1.8 + 32)

class onOffElement:
    def __init__(self, ard_id, ard_parent):
        assert len(ard_id) <= 2
        self.id = ard_id
        self.ard_parent = ard_parent
        self.status = "off"

    def turnOn(self):
        # Turn on Heating Element
        msg = self.id + "-1"
        self.ard_parent.talk_with_arduino(msg)

    def turnOff(self):
        # Turn off Heating Element
        msg = self.id + "-0"
        self.ard_parent.talk_with_arduino(msg)

    def updateStatus(self, ardReturnVal):
        ardReturnVal = int(ardReturnVal)
        if ardReturnVal == 1:
            self.status = "on"
        else:
            self.status = "off"

class Fan(onOffElement):
    def __init__(self, ard_id, ard_parent):
        '''fan args=(ard_id, ard_parent)'''
        onOffElement.__init__(self, ard_id, ard_parent)

    def adjustSpeed(self, speed="off"):
        msg = chr(self.id)
        if speed == "off":
            msg += "-0"
        elif speed == "low":
            msg += "-1"
        elif speed == "med":
            msg += "-2"
        elif speed == "high":
            msg += "-3"
        else:
            # Raise Error
            print("speed {!r} not a valid option!".format(speed))
            raise FanSpeedOptionError()
        self.ard_parent.talk_with_arduino(msg)

    def updateStatus(self, ardReturnVal):
        ardReturnVal = int(ardReturnVal)
        if ardReturnVal == 3:
            self.status = "high"
        elif ardReturnVal == 2:
            self.status = "med"
        elif ardReturnVal == 1:
            self.status = "low"
        elif ardReturnVal == 0:
            self.status = "off"
        else:
            print("No valid status returned for fan")

class HeatingElement(onOffElement):
    def __init__(self, ard_id, ard_parent):
        '''heating element args=(ard_id, ard_parent)'''
        onOffElement.__init__(self, ard_id, ard_parent)

class WoodAuger(onOffElement):
    def __init__(self, ard_id, ard_parent):
        '''wood auger element args=(ard_id, ard_parent)'''
        onOffElement.__init__(self, ard_id, ard_parent)

class AirPump(onOffElement):
    def __init__(self, ard_id, ard_parent):
        '''air pump element args=(ard_id, ard_parent)'''
        onOffElement.__init__(self, ard_id, ard_parent)

