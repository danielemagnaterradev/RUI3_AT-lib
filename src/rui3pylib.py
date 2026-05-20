import logging
import re
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
    response = "\n".join(
        line for line in response.splitlines()
        if not line.startswith("[APP]")
    )
    return response


def checkSuccess(serial: serial.Serial, cmd: str, wait: float = 3.0):
    response = sendCommand(serial, cmd, wait)
    ok = "OK" in response
    clean = response.replace("OK", "").strip()
    logging.info(f"[{_status(ok)}] {cmd}" + (f" -> {clean}" if clean else ""))
    return response, ok

# This class contains all of the RUI3 commands as methods.
# When initialized, it will try to connect automatically and, if a port was not directly passed,
# it will automatically find the RUI3 compatible device for you.


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
        else:
            try:
                self.open()
                if self.tryConnect():
                    logging.info(f"Connected to port {self.port}")
                else:
                    self.close()
            except serial.serialutil.SerialException as e:
                logging.info(f"SerialException on {self.port}: {e}")
                if self.is_open:
                    self.close()

    def tryConnect(self):
        try:
            _, ok = checkSuccess(self, "AT", 5.0)
            return ok
        except serial.serialutil.PortNotOpenError:
            logging.info("Port not open")
            return False

    #####################################
    ######### GENERAL COMMANDS ##########
    #####################################

    def ping(self):
        response, ok = checkSuccess(self, "AT")
        if ok:
            return response

    def help(self):
        response, ok = checkSuccess(self, "AT?")
        if ok:
            return response

    def toggleCommandEcho(self):
        response, ok = checkSuccess(self, "ATE")
        if ok:
            return response

    def reset(self):
        response, ok = checkSuccess(self, "ATZ")
        if ok:
            logging.info("Module reset")
            return response

    def restoreDefault(self):
        response, ok = checkSuccess(self, "ATR")
        if ok:
            logging.info("Restored default values")
            return response

    def getSerialNumber(self):
        response, ok = checkSuccess(self, "AT+SN=?")
        if ok:
            return response

    def getBatteryLevel(self):
        response, ok = checkSuccess(self, "AT+BAT=?")
        if ok:
            return response

    def getBuildTime(self):
        response, ok = checkSuccess(self, "AT+BUILDTIME=?")
        if ok:
            return response

    def getRepoInfo(self):
        response, ok = checkSuccess(self, "AT+REPOINFO=?")
        if ok:
            return response

    def getFirmVersion(self):
        response, ok = checkSuccess(self, "AT+VER=?")
        if ok:
            return response

    def getATVersion(self):
        response, ok = checkSuccess(self, "AT+CLIVER=?")
        if ok:
            return response

    def getAPIVersion(self):
        response, ok = checkSuccess(self, "AT+APIVER=?")
        if ok:
            return response

    def getHWModel(self):
        response, ok = checkSuccess(self, "AT+HWMODEL=?")
        if ok:
            return response

    def getHWID(self):
        response, ok = checkSuccess(self, "AT+HWID=?")
        if ok:
            return response

    def getDeviceAlias(self):
        response, ok = checkSuccess(self, "AT+ALIAS=?")
        if ok:
            return response

    def getSystemVoltage(self):
        response, ok = checkSuccess(self, "AT+SYSV=?")
        if ok:
            return response

    def getBLEMac(self):
        response, ok = checkSuccess(self, "AT+BLEMAC=?")
        if ok:
            return response

    def setBLEMac(self, mac: str):
        # the string MUST be 12 characters
        if all(char in string.hexdigits for char in mac) and len(mac) == 12:
            # forcing correct mac formatting from an unformatted hexstring
            formatted = re.sub(f"(.{{{2}}})", f"\\1{":"}", mac)
            response, ok = checkSuccess(
                self, f"AT+BLEMAC={formatted[:-1].lower()}")
            if ok:
                return response
        else:
            logging.info("invalid format: it should be like 001122334455")

    def getBootVer(self):
        response, ok = checkSuccess(self, "AT+BOOTVER=?")
        if ok:
            return response

    ######################################
    ######### LOW POWER COMMANDS #########
    ######################################

    def atSleep(self, time: int):
        # time is in milliseconds
        response, ok = checkSuccess(self, f"AT+SLEEP={time}")
        if ok:
            return response

    def getLowPowerMode(self):
        response, ok = checkSuccess(self, "AT+LPM=?")
        if ok:
            return response

    def setLowPowerMode(self, on: bool):
        mode = 1 if on else 0
        response, ok = checkSuccess(self, f"AT+LPM={mode}")
        if ok:
            return response

    ######################################
    ######### SERIAL AT COMMANDS #########
    ######################################

    def lockSerial(self):
        # This method locks the serial port and it will require a password to access it
        # The default password is 00000000
        # You can change the password with the setPassword method
        # The command doesn't return OK
        _ = sendCommand(self, "AT+LOCK")
        logging.info(f"Serial port {self.port} is now locked")

    def setPassword(self, password: str):
        if len(password) < 1 or len(password) > 8:
            logging.info(
                "Password must be between 1 and 8 characters of length")
        else:
            response, ok = checkSuccess(self, f"AT+PWORD={password}")
            if ok:
                return response

    #######################################
    ######### BOOTLOADER COMMANDS #########
    #######################################

    # These methods, with the exception of the first one, only work in boot mode

    def setBootMode(self):
        # This method sets the device in boot mode
        # boot mode can be interrupted with the run method
        # AT_BUSY_ERROR is returned when the bootloader process is already running
        response, ok = checkSuccess(self, "AT+BOOT")
        if ok:
            return response

    def getBootloaderVer(self):
        response, ok = checkSuccess(self, "AT+VER=?")
        if ok:
            return response

    def getBootloaderStatus(self):
        response, ok = checkSuccess(self, "AT+BOOTSTATUS")
        if ok:
            return response

    def atRun(self):
        # This methods makes the device leave boot mode and boots into the application
        response, ok = checkSuccess(self, "AT+RUN")
        if ok:
            return response

    def bootReset(self):
        response, ok = checkSuccess(self, "AT+RESET")
        if ok:
            return response

    def bootUpdate(self):
        # Starts Y-modem receiving process
        response, ok = checkSuccess(self, "AT+UPDATE")
        if ok:
            return response

    #######################################
    ######### LORAWAN KEYS AND ID #########
    #######################################

    def getDeviceEUI(self):
        response, ok = checkSuccess(self, "AT+DEVEUI=?")
        if ok:
            return response

    def setDeviceEui(self, deveui: str):
        # Check if the string is comprised of precisely 16 hexdigits
        if all(char in string.hexdigits for char in deveui) and len(deveui) == 16:
            response, ok = checkSuccess(self, f"AT+DEVEUI={deveui}")
            if ok:
                return response
        else:
            # String is malformed and will return AT_PARAM_ERROR
            logging.info("AT_PARAM_ERROR")

    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    # The specifications and errors for the above method are valid for all the
    # methods in this section

    def getAppEUI(self):
        response, ok = checkSuccess(self, "AT+APPEUI=?")
        if ok:
            return response

    def setAppEUI(self, appeui: str):
        if all(char in string.hexdigits for char in appeui) and len(appeui) == 16:
            response, ok = checkSuccess(self, f"AT+APPEUI={appeui}")
            if ok:
                return response
        else:
            logging.info("AT_PARAM_ERROR")

    def getAppKey(self):
        response, ok = checkSuccess(self, "AT+APPKEY=?")
        if ok:
            return response

    def setAppKey(self, appkey: str):
        # Must be 32 hexdigits
        if all(char in string.hexdigits for char in appkey) and len(appkey) == 32:
            response, ok = checkSuccess(self, f"AT+APPKEY={appkey}")
            if ok:
                return response
        else:
            logging.info("AT_PARAM_ERROR")

    def getDevAddr(self):
        response, ok = checkSuccess(self, "AT+DEVADDR=?")
        if ok:
            return response

    def setDevAddr(self, devaddr: str):
        # Must be 8 hexdigits
        if all(char in string.hexdigits for char in devaddr) and len(devaddr) == 8:
            response, ok = checkSuccess(self, f"AT+DEVADDR={devaddr}")
            if ok:
                return response
        else:
            logging.info("AT_PARAM_ERROR")

    def getAppSKey(self):
        response, ok = checkSuccess(self, "AT+APPSKEY=?")
        if ok:
            return response

    def setAppSKey(self, appskey: str):
        # Must be 32 hexdigits
        if all(char in string.hexdigits for char in appskey) and len(appskey) == 32:
            response, ok = checkSuccess(self, f"AT+APPSKEY={appskey}")
            if ok:
                return response
        else:
            logging.info("AT_PARAM_ERROR")

    def getNetworkSKey(self):
        response, ok = checkSuccess(self, "AT+NWKSKEY=?")
        if ok:
            return response

    def setNetworkSKey(self, netskey: str):
        # Must be 32 hexdigits
        if all(char in string.hexdigits for char in netskey) and len(netskey) == 32:
            response, ok = checkSuccess(self, f"AT+NWKSKEY={netskey}")
            if ok:
                return response
        else:
            logging.info("AT_PARAM_ERROR")

    def getNetworkID(self):
        response, ok = checkSuccess(self, "AT+NETID=?")
        if ok:
            return response

    def setNetworkID(self, netid: str):
        # Must be 6 hexdigits
        if all(char in string.hexdigits for char in netid) and len(netid) == 6:
            response, ok = checkSuccess(self, f"AT+NETID={netid}")
            if ok:
                return response
        else:
            logging.info("AT_PARAM_ERROR")

    def getMulticastRootKey(self):
        response, ok = checkSuccess(self, "AT+MCROOTKEY=?")
        if ok:
            return response

    ###############################################
    ######### LORAWAN JOINING AND SENDING #########
    ###############################################

    def setConfirmMode(self, on: bool):
        # This method is used to configure the uplink payload to be confirmed or unconfirmed type
        mode = 1 if on else 0
        response, ok = checkSuccess(self, f"AT+CFM={mode}")
        if ok:
            return response

    def getConfirmStatus(self):
        # This command is used to access the status of the last SEND command
        response, ok = checkSuccess(self, "AT+CFS=?")
        if ok:
            return response

    def getJoinParams(self):
        response, ok = checkSuccess(self, "AT+JOIN=?")
        if ok:
            return response

    def tryJoin(self, join: bool = True, auto_join: bool = False, interval: int = 8, join_attempts: int = 0):
        # paramaters are formatted like *:*:*:*
        # if nothing is passed, default values will be used
        # The command is asynchronous and it will return OK if the device is joining
        # The completion of the join can be verified with the getNetworkJoinStatus method
        # Join = 1 for joining the network, 0 for stop joining
        join_bin = 1 if join else 0
        # Auto_join = 1 for auto-join on power-up, 0 for no aut-join
        auto_join_bin = 1 if auto_join else 0
        # Reattempt interval in second, default is 8
        if interval < 7 or interval > 255:
            logging.info("Reattempt value must be within 7 and 255")
        # No. of join attempts, must be within 0 and 255
        if join_attempts < 0 and join_attempts > 255:
            logging.info("No. of join attempts must be within 0 and 255")
        response, ok = checkSuccess(
            self, f"AT+JOIN={join_bin}:{auto_join_bin}:{interval}:{join_attempts}")
        if ok:
            return response

    def getNetworkJoinMode(self):
        response, ok = checkSuccess(self, "AT+NJM=?")
        if ok:
            return response

    def setNetworkJoinMode(self, mode: int = 0):
        # 0 = ABP mode
        # 1 = OTAA mode
        if mode != 0 and mode != 1:
            logging.info("Parameter must be either 0 (ABP) or 1 (OTAA)")
        else:
            response, ok = checkSuccess(self, f"AT+NJM={mode}")
            if ok:
                return response

    def getNetworkJoinStatus(self):
        response, ok = checkSuccess(self, "AT+NJS=?")
        if ok:
            return response

    def getLastReceivedData(self):
        # This command returns the last received data alog with the port it was received from
        # Format is like <port>:<payload><CR><LR>
        response, ok = checkSuccess(self, "AT+RECV=?")
        if ok:
            return response

    def sendData(self, port: int, payload: str):
        # Port number must be within 1 and 233
        # Payload must  be within 2 and 500 digit length, to represent
        # 1 to 256 hexadecimal numbers
        if port < 1 or port > 233:
            logging.info("Invalid port")
        if all(char in string.hexdigits for char in payload):
            if len(payload) > 2 and len(payload) < 500 and len(payload) % 2 == 0:
                response, ok = checkSuccess(self, f"AT+SEND={port}:{payload}")
                if ok:
                    return response
            else:
                logging.info("Invalid payload size")
        else:
            logging.info("Invalid payload format")

    def sendLongPacketData(self, port:int, ack: bool, payload: str):
        # Same as above except the packet can be up to 1000 bytes long
        # This is an asynchronous command and will return OK when the device starts to send
        # Long Packet mode only works for uplink packets. Downlink packet cannot have the long packet data format
        ack_bool = 1 if ack else 0
        if port < 1 or port > 233:
            logging.info("Invalid port")
        if all(char in string.hexdigits for char in payload):
            if len(payload) > 2 and len(payload) < 2000 and len(payload) % 2 == 0:
                response, ok = checkSuccess(self, f"AT+LPSEND={port}:{ack_bool}:{payload}")
                if ok:
                    return response
            else:
                logging.info("Invalid payload size")
        else:
            logging.info("Invalid payload format")

    def setConfirmPacketRetransmission(self, tries: int):
        # Sets the number of of retries for confirm packets
        # must be within 0 and 7
        if tries < 0 or tries > 7:
            logging.info("Invalid number: must be within 0 and 7")
        else:
            response, ok = checkSuccess(self, f"AT+RETY={tries}")
            if ok:
                return response

    def getConfirmPacketRetransmission(self):
        response, ok = checkSuccess(self, "AT+RETY=?")
        if ok:
            return response
