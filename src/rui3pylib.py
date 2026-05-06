import logging
import serial
import time
from typing import Optional

def sendCommand(serial: serial.Serial, cmd: str, wait: float = 0.5):
    serial.reset_input_buffer()
    full_cmd = cmd.strip() + "\r\n"
    serial.write(full_cmd.encode())
    time.sleep(wait)

    response = ""
    while serial.in_waiting:
            response += serial.read(serial.in_waiting).decode(errors="replace")
            time.sleep(0.1)

    return response.strip()

def checkSuccess(serial: serial.Serial, cmd: str, wait: float = 0.5):
    response = sendCommand(serial, cmd, wait)
    ok = "OK" in response
    status = "ok" if ok else "failed"
    logging.info(f"{status}     {cmd} -> {response}")
    return response, ok


class serialInterface(serial.Serial):
    def __init__():
        pass 

    def connect():
        pass

    def close():
        pass

class RUI3node(serialInterface):
    def __init__ (self, port: str, baudrate: int = 115200, timeout: float = 3.0):
        self. port = port
        self.baudrate = baudrate
        self.timeout = timeout

#    def connect(self):
 #       self.ser = serial.Serial(self.port, self.baudrate, timeout = self.timeout)
  #      time.sleep(1)
   #     self.ser.open()
    #    logging.info(f"Connected to port: {self.port}")
#
 #   def close(self):
  #      if self.ser & self.ser.is_open:
   #         self.ser.close()
    #        logging.info("Serial port closed")
     #       
    def Attention(self):
        response, ok = checkSuccess(self, "AT",)
        logging.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")
        return response

    def help(self):
        response, ok = checkSuccess(self, "AT?",)
        logging.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")
        return response

    def toggleCommandEcho(self):
        response, ok = checkSuccess(self, "ATE")
        logging.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")
        return response

    def reset(self):
        response, ok = checkSuccess(self, "ATZ")
        logging.info(f"Module reset {response} {ok:{"OK" if ok else "FAILED"}}")
        return response

    def restoreDefault(self):
        response, ok = checkSuccess(self, "ATR")
        logging.info(f"Restored default values {response}")
        return response

    def getSerialNumber(self):
        serial_number, ok = checkSuccess(self, "AT+SN=?")
        logging.info(f"{serial_number} {ok:{"OK" if ok else "FAILED"}}")
        return serial_number

    def getBatteryLevel(self):
        battery_level, ok = checkSuccess(self, "AT+BAT")
        logging.info(f"{battery_level} {ok:{"OK" if ok else "FAILED"}}")
        return battery_level

    def getBuildTime(self):
        response, ok = checkSuccess(self, "AT+BUILDTIME=?")
        logging.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")
        return response

    def getRepoInfo(self):
        repo_info, ok = checkSuccess(self, "AT_REPOINFO=?")
        logging.info(f"{repo_info} {ok:{"OK" if ok else "FAILED"}}")
        return repo_info

    def getFirmVersion(self):
        firmware_version, ok = checkSuccess(self, "AT+VER=?")
        logging.info(f"{firmware_version} {ok:{"OK" if ok else "FAILED"}}")
        return firmware_version

    def getATVersion(self):
        at_version, ok = checkSuccess(self, "AT+CLIVER=?")
        logging.info(f"{at_version} {ok:{"OK" if ok else "FAILED"}}")
        return at_version

    def getAPIVersion(self):
        api_version, ok = checkSuccess(self, "AT+APIVER=?")
        logging.info(f"{api_version} {ok:{"OK" if ok else "FAILED"}}")
        return api_version

    def getHWModel(self):
        hardware_model, ok = checkSuccess(self, "AT+HWMODEL=?")
        logging.info(f"{hardware_model} {ok:{"OK" if ok else "FAILED"}}")
        return hardware_model

    def getHWID(self):
        hardware_ID, ok = checkSuccess(self, "AT+HWID=?")
        logging.info(f"{hardware_ID} {ok:{"OK" if ok else "FAILED"}}")
        return hardware_ID

    def getDeviceAlias(self):
        device_alias, ok = checkSuccess(self, "AT+ALIAS=?")
        logging.info(f"{device_alias} {ok:{"OK" if ok else "FAILED"}}")
        return device_alias

    def setDeviceAlias(self, alias: str):
        response, ok = checkSuccess(self, f"AT+ALIAS={alias}")
        logging.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")
        return response

    def getSystemVoltage(self):
        response, ok = checkSuccess(self, "AT+SYSV=?")
        logging.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")
        return response
