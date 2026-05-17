import logging
import serial
import string
import time
from serial.tools.list_ports import comports

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def _status(ok: bool) -> str:
    return "OK" if ok else "FAILED"


def sendCommand(serial: serial.Serial, cmd: str, wait: float = 3.0):
    serial.reset_input_buffer()
    full_cmd = cmd.strip() + "\r\n"
    serial.write(full_cmd.encode(errors="replace"))
    time.sleep(wait)

    response = ""
    while serial.in_waiting:
        response += serial.read(serial.in_waiting).decode(errors="replace")
        time.sleep(1.0)

    # Filter out firmware debug lines
    filtered = "\n".join(
        line for line in response.splitlines()
        if not line.startswith("[APP]")
    )
    return filtered


def checkSuccess(serial: serial.Serial, cmd: str, wait: float = 3.0):
    response = sendCommand(serial, cmd, wait)
    ok = "OK" in response
    clean = response.replace("OK", "").strip()
    logging.info(f"[{_status(ok)}] {cmd}" + (f" -> {clean}" if clean else ""))
    return response, ok


class RUI3node(serial.Serial):
    def __init__(self, port: str | None = None, baudrate: int = 115200, timeout: float = 3.0):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        if port is None:
            for interface in comports():
                try:
                    self.port = interface.name
                    self.open()
                    if self.tryConnect():
                        logging.info(f"Connected to port {self.port}")
                        break
                    else:
                        self.close()
                except serial.serialutil.SerialException as e:
                    logging.info(f"SerialException on {self.port}: {e}")
                    if self.is_open:
                        self.close()

    def tryConnect(self):
        try:
            response, ok = checkSuccess(self, "AT", 5.0)
            return ok
        except serial.serialutil.PortNotOpenError:
            logging.info("Port not open")
            return False

    def tryClose(self):
        super().close()

    #####################################
    ######### GENERAL COMMANDS ##########
    #####################################

    def attention(self):
        response, ok = checkSuccess(self, "AT")
        return response

    def help(self):
        response, ok = checkSuccess(self, "AT?")
        return response

    def toggleCommandEcho(self):
        response, ok = checkSuccess(self, "ATE")
        return response

    def reset(self):
        response, ok = checkSuccess(self, "ATZ")
        logging.info("Module reset")
        return response

    def restoreDefault(self):
        response, ok = checkSuccess(self, "ATR")
        logging.info("Restored default values")
        return response

    def getSerialNumber(self):
        serial_number, ok = checkSuccess(self, "AT+SN=?")
        return serial_number

    def getBatteryLevel(self):
        battery_level, ok = checkSuccess(self, "AT+BAT=?")
        return battery_level

    def getBuildTime(self):
        response, ok = checkSuccess(self, "AT+BUILDTIME=?")
        return response

    def getRepoInfo(self):
        repo_info, ok = checkSuccess(self, "AT+REPOINFO=?")
        return repo_info

    def getFirmVersion(self):
        firmware_version, ok = checkSuccess(self, "AT+VER=?")
        return firmware_version

    def getATVersion(self):
        at_version, ok = checkSuccess(self, "AT+CLIVER=?")
        return at_version

    def getAPIVersion(self):
        api_version, ok = checkSuccess(self, "AT+APIVER=?")
        return api_version

    def getHWModel(self):
        hardware_model, ok = checkSuccess(self, "AT+HWMODEL=?")
        return hardware_model

    def getHWID(self):
        hardware_ID, ok = checkSuccess(self, "AT+HWID=?")
        return hardware_ID

    def getDeviceAlias(self):
        device_alias, ok = checkSuccess(self, "AT+ALIAS=?")
        return device_alias

    def getSystemVoltage(self):
        response, ok = checkSuccess(self, "AT+SYSV=?")
        return response

    def getBLEMac(self):
        response, ok = checkSuccess(self, "AT+BLEMAC=?")
        return response

    def setBLEMac(self, mac: str):
        # the string MUST be 12 characters
        if len(mac) > 12:
            mac = mac[:12]
        else:
            mac = mac.ljust(12)
        response, ok = checkSuccess(self, f"AT+BLEMAC={mac}")
        return response

    def getBootVer(self):
        response, ok = checkSuccess(self, "AT+BOOTVER=?")
        return response

    ######################################
    ######### LOW POWER COMMANDS #########
    ######################################

    def atSleep(self, time: int):
        # time is in milliseconds
        response, ok = checkSuccess(self, f"AT+SLEEP={time}")
        return response

    def getLowPowerMode(self):
        response, ok = checkSuccess(self, "AT+LPM=?")
        return response

    def setLowPowerMode(self, on: bool):
        if on is True:
            mode = 1
        else:
            mode = 0
        response, ok = checkSuccess(self, f"AT+LPM={mode}")
        return response

    ######################################
    ######### SERIAL AT COMMANDS #########
    ######################################

    def lockSerial(self):
        # This method locks the serial port and it will require a password to access it
        # The default password is 00000000
        # You can change the password with the setPassword method
        response, ok = checkSuccess(self, "AT+LOCK")
        if ok:
            print(f"Serial port {self.port} is now locked")
        else:
            return response

    def setPassword(self, password: str):
        if len(password) < 1 or len(password) > 8:
            print("Password must be between 1 and 8 characters of length")
        else:
            response, ok = checkSuccess(self, f"AT+PWORD={password}")

        return response

    #######################################
    ######### BOOTLOADER COMMANDS #########
    #######################################

    # These methods, with the exception of the first, one only work in boot mode

    def setBootMode(self):
        # This method sets the device in boot mode
        # boot mode can be interrupted with the run method
        # AT_BUSY_ERROR is returned when the bootloader process is already running
        response, ok = checkSuccess(self, "AT+BOOT")
        return response

    def getBootloadeVer(self):
        response, ok = checkSuccess(self, "AT+VER=?")
        return response

    def getBootloadeStatus(self):
        response, ok = checkSuccess(self, "AT+BOOTSTATUS")
        return response

    def atRun(self):
        # This methods makes the device leave boot mode and boots into the application
        response, ok = checkSuccess(self, "AT+RUN")
        return response

    def bootReset(self):
        response, ok = checkSuccess(self, "AT+RESET")
        return response

    def bootUpdate(self):
        # Starts Y-modem receiving process
        response, ok = checkSuccess(self, "AT+UPDATE")
        return response

    #######################################
    ######### LORAWAN KEYS AND ID #########
    #######################################

    def getDeviceEUI(self):
        response, ok = checkSuccess(self, "AT+DEVEUI=?")
        return response

    def setDeviceEui(self, deveui: str):
        # Check if the string is comprised of precisely 16 hexdigits
        if all(char in string.hexdigits for char in deveui) and len(deveui) == 16:
            response, ok = checkSuccess(self, f"AT+DEVEUI={deveui}")
            return response
        else:
            # String is malformed and will return AT_PARAM_ERROR
            logging.info("AT_PARAM_ERROR")

    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    # The specifications and errors for the above method are valid for all the
    # methods in this section

    def getAppEUI(self):
        response, ok = checkSuccess(self, "AT+APPEUI=?")
        return response

    def setAppEUI(self, appeui: str):
        if all(char in string.hexdigits for char in appeui) and len(appeui) == 16:
            response, ok = checkSuccess(self, f"AT+APPEUI={appeui}")
            return response
        else:
            logging.info("AT_PARAM_ERROR")

    def getAppKey(self):
        response, ok = checkSuccess(self, "AT+APPKEY=?")
        return response

    def setAppKey(self, appkey: str):
        # Must be 32 hexdigits
        if all(char in string.hexdigits for char in appkey) and len(appkey) == 32:
            response, ok = checkSuccess(self, f"AT+APPKEY={appkey}")
            return response
        else:
            logging.info("AT_PARAM_ERROR")

    def getDevAddr(self):
        response, ok = checkSuccess(self, "AT+DEVADDR=?")
        return response

    def setDevAddr(self, devaddr: str):
        # Must be 4 hexdigits
        if all(char in string.hexdigits for char in devaddr) and len(devaddr) == 4:
            response, ok = checkSuccess(self, f"AT+APPKEY={devaddr}")
            return response
        else:
            logging.info("AT_PARAM_ERROR")

    def getAppSKey(self):
        response, ok = checkSuccess(self, "AT+APPSKEY=?")
        return response

    def setAppSKey(self, appskey: str):
        # Must be 32 hexdigits
        if all(char in string.hexdigits for char in appskey) and len(appskey) == 32:
            response, ok = checkSuccess(self, f"AT+APPSKEY={appskey}")
            return response
        else:
            logging.info("AT_PARAM_ERROR")

    def getNetworkSKey(self):
        response, ok = checkSuccess(self, "AT+NWKSKEY=?")
        return response

    def setNetworkSKey(self, netskey: str):
        # Must be 32 hexdigits
        if all(char in string.hexdigits for char in netskey) and len(netskey) == 32:
            response, ok = checkSuccess(self, f"AT+APPSKEY={netskey}")
            return response
        else:
            logging.info("AT_PARAM_ERROR")

    def getNetworkID(self):
        response, ok = checkSuccess(self, "AT+NETID=?")
        return response

    def setNetworkID(self, netid: str):
        # Must be 6 hexdigits
        if all(char in string.hexdigits for char in netid) and len(netid) == 6:
            response, ok = checkSuccess(self, f"AT+APPSKEY={netid}")
            return response
        else:
            logging.info("AT_PARAM_ERROR")

    def getMulticastRootKey(self):
        response, ok = checkSuccess(self, "AT+MCROOTKEY=?")
        return response
