__author__ = 'GrMartin'

import unittest, random
from coverage import coverage
cov = coverage(branch=True, omit=["GB_venv/*", "tests.py"])
cov.start()

from app import controls
import time
from config import *

class TestCase(unittest.TestCase):
    def setUp(self):
        pass

class testArd(controls.ArduinoTools):
    def __init__(self):
        controls.ArduinoTools.__init__(self, None, None)
        self.dataStorageDir = os.path.join(basedir, "test files\\data")
        self.ids_options_dict={}
        for key in self.id_obj_list.keys():
            if key == "f1": self.ids_options_dict[key] = [0, 1, 2, 3] # Fan speeds (off, low, med, high)
            else: self.ids_options_dict[key] = range(100,200)

    def initiateSerialConnection(self, port, baudrate):
        pass

    def talk_with_arduino(self, msg):
        if self.serial_lock.acquire():
            time.sleep(1)
            print("Fake ard response to", repr(msg))
            response = ""
            for key in self.ids_options_dict.keys():
                if key == "f1":
                    if msg == "0000": # turn off all
                        response += "f1:0"
                    elif self.id_obj_list[key].status == "high":
                        response += "f1:3"
                    elif self.id_obj_list[key].status == "med":
                        response += "f1:2"
                    elif self.id_obj_list[key].status == "low":
                        response += "f1:1"
                    else:
                        response += "f1:0"
                else:
                    response += key + ":" +str(random.choice(self.ids_options_dict[key]))
                response +=","
            response = response[:-1]
            print("response", response)
            self.updateArduino(response)
            self.serial_lock.release()
        else: print("serial_lock is locked; Pass on talking")
