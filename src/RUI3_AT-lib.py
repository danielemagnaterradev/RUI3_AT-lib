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
    return response, ok


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

    def Attention(self):
        response, ok = checkSuccess(self, "AT",)
        log.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")
        return response

    def help(self):
        response, ok = checkSuccess(self, "AT?",)
        log.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")
        return response

    def toggleCommandEcho(self):
        response, ok = checkSuccess(self, "ATE")
        log.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")

    def reset(self):
        response, ok = checkSuccess(self, "ATZ")
        log.info(f"Module reset {response} {ok:{"OK" if ok else "FAILED"}}")
        return response

    def restoreDefault(self):
        response, ok = checkSuccess(self, "ATR")
        log.info(f"Restored default values {response}")
        return response

    def getSerialNumber(self):
        serial_number, ok = checkSuccess(self, "AT+SN=?")
        log.info(f"{serial_number} {ok:{"OK" if ok else "FAILED"}}")
        return serial_number

    def getBatteryLevel(self):
        battery_level, ok = checkSuccess(self, "AT+BAT")
        log.info(f"{battery_level} {ok:{"OK" if ok else "FAILED"}}")
        return battery_level

    def getBuildTime(self):
        response, ok = checkSucces(self, "AT+BUILDTIME=?")
        log.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")
        return response

    def getRepoInfo(self):
        repo_info = checkSuccess(self, "AT_REPOINFO=?")
        log.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")
        return repo_info

    def getFirmVersion(self):
        firmware_version = checkSuccess(self, "AT+VER=?")
        log.info(f"{firmware_version} {ok:{"OK" if ok else "FAILED"}}")
        return firmware_version

    def getATVersion(self):
        at_version = checkSuccess(self, "AT+CLIVER=?")
        log.info(f"{at_version} {ok:{"OK" if ok else "FAILED"}}")
        return AT_version

    def getAPIVersion(self):
        api_version = checkSuccess(self, "AT+APIVER=?")
        log.info(f"{api_version} {ok:{"OK" if ok else "FAILED"}}")
        return api_version

    def getHWModel(self):
        hardware_model = checkSuccess(self, "AT+HWMODEL=?")
        log.info(f"{hardware_model} {ok:{"OK" if ok else "FAILED"}}")
        return hardware_model

    def getHWID(self):
        hardware_ID = checkSuccess(self, "AT+HWID=?")
        log.info(f"{hardware_ID} {ok:{"OK" if ok else "FAILED"}}")
        return hardware_ID

    def getDeviceAlias(self):
        device_alias = checkSuccess(self, "AT+ALIAS=?")
        log.info(f"{device_alias} {ok:{"OK" if ok else "FAILED"}}")
        return device_alias

    def setDeviceAlias(alias: str):
        response, ok = checkSuccess(self, f"AT+ALIAS={alias}")
        log.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")
        return response

    def getSystemVoltage(self):
        response, ok = checkSuccess(self, "AT+SYSV=?")
        log.info(f"{response} {ok:{"OK" if ok else "FAILED"}}")
        return response
