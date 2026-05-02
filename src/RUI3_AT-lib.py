import logging
import openpyxl
import serial
import time
from typing import Optional

def sendCommand(serial: serial.Serial, cmd: str, wait: float = 0.5):
    serial.reset_input_buffer()
    full_cmd = cdm.strip() + "\r\n"
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
    log.info(f"{status}     {cmd} -> {response}")
    return ok


class RUI3node:
    def __init__ (self, port: str, baudrate: int = 115200, timeout: float = 3.0):
        self. port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None

    def connect(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout = self.timeout)
        time.sleep(1)
        self.ser.open()
        log.info(f"Connected to port: {self.port}")

    def close(self):
        if self.ser && self.ser.is_open:
            self.ser.close()
            log.info("Serial port closed")

    def Attention():
        response = sendCommand(self, "AT",)
        log.info(f"{response.strip()")

    def help():
        response = sendCommand(self, "AT?",)
        log.info(f"{response.strip()")

    def toggleCommandEcho():
        response = sendCommand(self, "ATE")
        log.info(f"{response.strip()")

    def reset():
        response = sendCommand(self, "ATZ")
        log.info("Module reset")

    def restoreDefault():
        response = sendCommand(self, "ATR")
        log.info("Restored default values")

    def getSerialNumber():
        serial_number = sendCommand(self, "AT+SN=?")
        log.info(f"{serial_number}")
        return serial_number

    def getBatteryLevel():
        battery_level = sendCommand(self, "AT+BAT")
        log.info(f"{battery_level}")
        return battery_level

    def getBuildTime():
        response = sendCommand(self, "AT+BUILDTIME=?")
        log.info(f"{response}")
        return response

    def getRepoInfo():
        repo_info = sendCommand(self, "AT_REPOINFO=?")
        log.info(f"{response}")
        return repo_info

    def getFirmVersion():
        firmware_version = sendCommand(self, "AT+VER=?")
        log.info(f"{firmware_version}")
        return firmware_version

    def getATVersion():
        AT_version = sendCommand(self, "AT+CLIVER=?")
        log.info(f"{AT_version}")
        return AT_version

    def getAPIVersion():
        API_version = sendCommand(self, "AT+APIVER=?")
        log.info(f"{API_version}")
        return API_version

    def getHWModel():
        hardware_model = sendCommand(self, "AT+HWMODEL=?")
        log.info(f"{hardware_model}")
        return hardware_model

    def getHWID():
        hardware_ID = sendCommand(self, "AT+HWID=?")
        log.info(f"{hardware_ID}")
        return hardware_ID

    def getDeviceAlias():
        device_alias = sendCommand(self, "AT+ALIAS=?")
        log.info(f"{device_alias}")
        return device_alias

    def setDeviceAlias(alias: str):
        response = sendCommand(self, f"AT+ALIAS={alias}")
        log.info(f"{response}")
        return response

    def getSystemVoltage():
        response = sendCommand(self, "AT+SYSV=?")
        log.info(f"{response}")
        return response
