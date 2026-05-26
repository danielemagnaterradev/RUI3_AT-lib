import logging
import re
import serial
import string
import time
from serial.tools.list_ports import comports

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
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
        line for line in response.splitlines() if not line.startswith("[APP]")
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
    def __init__(
        self, port: str | None = None, baudrate: int = 115200, timeout: float = 3.0
    ):
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
            formatted = re.sub(f"(.{{{2}}})", f"\\1{':'}", mac)
            response, ok = checkSuccess(self, f"AT+BLEMAC={formatted[:-1].lower()}")
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

    def getLowPowerModeLevel(self):
        # NOTE: only effective on RAK3172; has no effect on other modules.
        # Stop1 Mode allows wakeup via both UART1 and UART2.
        # Stop2 Mode is more power-efficient but only UART2 can wake the device.
        response, ok = checkSuccess(self, "AT+LPMLVL=?")
        if ok:
            return response

    def setLowPowerModeLevel(self, level: int):
        # NOTE: only effective on RAK3172; has no effect on other modules.
        # level 1 = STOP1 Mode, level 2 = STOP2 Mode
        if level != 1 and level != 2:
            logging.warning("Level must be either 1 (STOP1) or 2 (STOP2)")
            return None
        response, ok = checkSuccess(self, f"AT+LPMLVL={level}")
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
            logging.info("Password must be between 1 and 8 characters of length")
        else:
            response, ok = checkSuccess(self, f"AT+PWORD={password}")
            if ok:
                return response

    def getBaudRate(self):
        response, ok = checkSuccess(self, "AT+BAUD=?")
        if ok:
            return response

    def setBaudRate(self, baudrate: int):
        # Valid values: standard serial baud rates (e.g. 9600, 115200, etc.)
        # The last configured baudrate is retained even after reset or power recycle.
        response, ok = checkSuccess(self, f"AT+BAUD={baudrate}")
        if ok:
            return response

    def switchToATMode(self):
        # Switches the device back to AT command mode (default mode)
        response, ok = checkSuccess(self, "AT+ATM")
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
        # Only works in boot mode. Returns the bootloader version string.
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
            logging.info("Device eui must be exactly 16 hexdigits")

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
            logging.info("App eui must be exactly 16 hexdigits")

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
            logging.info("App Key must be exactly 32 hexdigits")

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
            logging.info("")

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
            logging.info("App seecurity key must be exactly 32 hexdigits")

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
            logging.info("Network security key must be exactly 32 hexdigits")

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
            logging.info("Network ID must be exactly 6 hexdigits")

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

    def tryJoin(
        self,
        join: bool = True,
        auto_join: bool = False,
        interval: int = 8,
        join_attempts: int = 0,
    ):
        # parameters are formatted like *:*:*:*
        # if nothing is passed, default values will be used
        # The command is asynchronous and it will return OK if the device is joining
        # The completion of the join can be verified with the getNetworkJoinStatus method
        # Join = 1 for joining the network, 0 for stop joining
        join_bin = 1 if join else 0
        # Auto_join = 1 for auto-join on power-up, 0 for no auto-join
        auto_join_bin = 1 if auto_join else 0
        # Reattempt interval in seconds, must be within 7 and 255
        if interval < 7 or interval > 255:
            logging.warning("Reattempt value must be within 7 and 255")
            return None
        # No. of join attempts, must be within 0 and 255
        if join_attempts < 0 or join_attempts > 255:
            logging.warning("No. of join attempts must be within 0 and 255")
            return None
        response, ok = checkSuccess(
            self, f"AT+JOIN={join_bin}:{auto_join_bin}:{interval}:{join_attempts}"
        )
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
        # This command returns the last received data along with the port it was received from
        # Format is like <port>:<payload><CR><LF>
        response, ok = checkSuccess(self, "AT+RECV=?")
        if ok:
            return response

    def sendData(self, port: int, payload: str):
        # Port number must be within 1 and 233
        # Payload must be within 2 and 500 digit length (even number), representing 1 to 256 hex bytes
        if port < 1 or port > 233:
            logging.info("Invalid port")
            return None
        if not all(char in string.hexdigits for char in payload):
            logging.info("Invalid payload format")
            return None
        if len(payload) < 2 or len(payload) > 500 or len(payload) % 2 != 0:
            logging.info("Invalid payload size")
            return None
        response, ok = checkSuccess(self, f"AT+SEND={port}:{payload}")
        if ok:
            return response

    def sendLongPacketData(self, port: int, ack: bool, payload: str):
        # Same as above except the packet can be up to 1000 bytes long
        # This is an asynchronous command and will return OK when the device starts to send
        # Long Packet mode only works for uplink packets. Downlink packet cannot have the long packet data format
        ack_bool = 1 if ack else 0
        if port < 1 or port > 233:
            logging.info("Invalid port")
            return None
        if not all(char in string.hexdigits for char in payload):
            logging.info("Invalid payload format")
            return None
        if len(payload) < 2 or len(payload) > 2000 or len(payload) % 2 != 0:
            logging.info("Invalid payload size")
            return None
        response, ok = checkSuccess(self, f"AT+LPSEND={port}:{ack_bool}:{payload}")
        if ok:
            return response

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

    ###############################################
    ######### LORAWAN Network Management ##########
    ###############################################

    def getAdaptiveRate(self):
        response, ok = checkSuccess(self, "AT+ADR=?")
        if ok:
            return response

    def setAdaptiveRate(self, on: bool):
        mode = 1 if on else 0
        response, ok = checkSuccess(self, f"AT+ADR={mode}")
        if ok:
            return response

    def getLorawanClass(self):
        response, ok = checkSuccess(self, "AT+CLASS=?")
        if ok:
            return response

    def setLorawanClass(self, lorawan_class: str):
        # The value of class must be either A, B or C
        if lorawan_class not in ("A", "B", "C"):
            logging.info("LoRaWAN class must be either A, B or C")
        else:
            response, ok = checkSuccess(self, f"AT+CLASS={lorawan_class}")
            if ok:
                return response

    def getDutyCycle(self):
        response, ok = checkSuccess(self, "AT+DCS=?")
        if ok:
            return response

    def setDutyCycle(self, on: bool):
        # Be very careful with the regulation in your country since in some places it's mandatory
        mode = 1 if on else 0
        response, ok = checkSuccess(self, f"AT+DCS={mode}")
        if ok:
            return response

    def getDataRate(self):
        response, ok = checkSuccess(self, "AT+DR=?")
        if ok:
            return response

    def setDataRate(self, data_rate: int):
        # Must be between 0 and 7
        # Also be careful with your country's regulation
        if data_rate < 0 or data_rate > 7:
            logging.info("data rate must be between 0 and 7")
        else:
            response, ok = checkSuccess(self, f"AT+DR={data_rate}")
            if ok:
                return response

    def getJoinDelayRXWindow1(self):
        response, ok = checkSuccess(self, "AT+JN1DL=?")
        if ok:
            return response

    def setJoinDelayRXWindow1(self, value: int):
        # Value must be within 1 and 14
        if value < 1 or value > 14:
            logging.info("Value must be within 1 and 14")
        else:
            response, ok = checkSuccess(self, f"AT+JN1DL={value}")
            if ok:
                return response

    def getJoinDelayRXWindow2(self):
        response, ok = checkSuccess(self, "AT+JN2DL=?")
        if ok:
            return response

    def setJoinDelayRXWindow2(self, value: int):
        # This value must be greater than JoinDelayRXWindow1
        if value < 2 or value > 15:
            logging.info("Value must be within 2 and 15")
        else:
            response, ok = checkSuccess(self, f"AT+JN2DL={value}")
            if ok:
                return response

    def getPublicNetworkMode(self):
        response, ok = checkSuccess(self, "AT+PNM=?")
        if ok:
            return response

    def setPublicNetworkMode(self, on: bool):
        mode = 1 if on else 0
        response, ok = checkSuccess(self, f"AT+PNM={mode}")
        if ok:
            return response

    def getReceiveWindow1Delay(self):
        response, ok = checkSuccess(self, "AT+RX1DL=?")
        if ok:
            return response

    def setReceiveWindow1Delay(self, value: int):
        if value < 1 or value > 15:
            logging.info("Value must be between 1 and 15")
        else:
            response, ok = checkSuccess(self, f"AT+RX1DL={value}")
            if ok:
                return response

    def getReceiveWindow2Delay(self):
        response, ok = checkSuccess(self, "AT+RX2DL=?")
        if ok:
            return response

    def setReceiveWindow2Delay(self, value: int):
        if value < 2 or value > 15:
            logging.info("Value must be between 2 and 15")
        else:
            response, ok = checkSuccess(self, f"AT+RX2DL={value}")
            if ok:
                return response

    def getReceiveWindow2DataRate(self):
        response, ok = checkSuccess(self, "AT+RX2DR=?")
        if ok:
            return response

    def setReceiveWindow2DataRate(self, value: int):
        # Be careful with your geographical location since some locations have entirely different data rates possible
        if value < 0 or value > 13:
            logging.info("Value must be between 0 and 13")
        else:
            response, ok = checkSuccess(self, f"AT+RX2DR={value}")
            if ok:
                return response

    def getReceiveWindow2Freq(self):
        response, ok = checkSuccess(self, "AT+RX2FQ=?")
        if ok:
            return response

    def setReceiveWindow2Freq(self, freq: int):
        # This is the receive frequency in Hz
        response, ok = checkSuccess(self, f"AT+RX2FQ={freq}")
        if ok:
            return response

    def getTransmitPower(self):
        response, ok = checkSuccess(self, "AT+TXP=?")
        if ok:
            return response

    def setTransmitPower(self, value: int):
        # Be careful with your country's regulation.
        # Valid range depends on region:
        #   EU433: 0-5 | EU868/CN470/KR920/AS923/RU864: 0-7
        #   IN865: 0-10 | US915/AU915: 0-14
        if value < 0 or value > 14:
            logging.info("Value must between 0 and 14")
        else:
            response, ok = checkSuccess(self, f"AT+TXP={value}")
            if ok:
                return response

    def getLinkCheck(self):
        response, ok = checkSuccess(self, "AT+LINKCHECK=?")
        if ok:
            return response

    def setLinkCheck(self, value: int):
        # 0 - Disable link check
        # 1 - Execute link check just once on the next payload uplink
        # 2 - Module will automatically execute one-time link check after every payload uplink
        if value not in (0, 1, 2):
            logging.info("Value must be either 0, 1 or 2")
        else:
            response, ok = checkSuccess(self, f"AT+LINKCHECK={value}")
            if ok:
                return response

    def getListenBeforeTalk(self):
        response, ok = checkSuccess(self, "AT+LBT=?")
        if ok:
            return response

    def setListenBeforeTalk(self, on: bool):
        mode = 1 if on else 0
        response, ok = checkSuccess(self, f"AT+LBT={mode}")
        if ok:
            return response

    def getListenBeforeTalkRSSI(self):
        response, ok = checkSuccess(self, "AT+LBTRSSI=?")
        if ok:
            return response

    def setListenBeforeTalkRSSI(self, value: int):
        # Honestly, it's not entirely clear how this is supposed to be handled from the docs
        response, ok = checkSuccess(self, f"AT+LBTRSSI={value}")
        if ok:
            return response

    def getListenBeforeTalkScanTime(self):
        response, ok = checkSuccess(self, "AT+LBTSCANTIME=?")
        if ok:
            return response

    def setListenBeforeTalkScanTime(self, value: int):
        # Again, not entirely clear. I think the value is expressed in seconds
        response, ok = checkSuccess(self, f"AT+LBTSCANTIME={value}")
        if ok:
            return response

    def getTimeReq(self):
        response, ok = checkSuccess(self, "AT+TIMEREQ=?")
        if ok:
            return response

    def setTimeReq(self, on: bool):
        mode = 1 if on else 0
        response, ok = checkSuccess(self, f"AT+TIMEREQ={mode}")
        if ok:
            return response

    def getLocalTime(self):
        response, ok = checkSuccess(self, "AT+LTIME=?")
        if ok:
            return response

    ################################
    ######### Class B Mode #########
    ################################

    def getPeriodicity(self):
        response, ok = checkSuccess(self, "AT+PGSLOT=?")
        if ok:
            return response

    def setPeriodicity(self, value: int):
        if value < 0 or value > 7:
            logging.info("Value must be between 0 and 7")
        else:
            response, ok = checkSuccess(self, f"AT+PGSLOT={value}")
            if ok:
                return response

    def getBeaconFreq(self):
        response, ok = checkSuccess(self, "AT+BFREQ=?")
        if ok:
            return response

    def getBeaconTime(self):
        response, ok = checkSuccess(self, "AT+BTIME=?")
        if ok:
            return response

    def getGWInfo(self):
        response, ok = checkSuccess(self, "AT+BGW=?")
        if ok:
            return response

    #######################################
    ######### LoRaWAN Information #########
    #######################################

    def getRSSI(self):
        response, ok = checkSuccess(self, "AT+RSSI=?")
        if ok:
            return response

    def getAllChannelRSSI(self):
        response, ok = checkSuccess(self, "AT+ARSSI=?")
        if ok:
            return response

    def getSignalToNoiseRatio(self):
        response, ok = checkSuccess(self, "AT+SNR=?")
        if ok:
            return response

    #############################################
    ######### LoRaWAN Regional Commands #########
    #############################################

    # These commands are very technical and concern your country's regulation and the frequency band you
    # are operating at, so proceed with caution. Keep in mind the format checking in the methods below won't
    # be as strict so there might be more errors.

    def getMask(self):
        response, ok = checkSuccess(self, "AT+MASK=?")
        if ok:
            return response

    def setMask(self, mask: str):
        # This must be a 4 digit hexdigit mask, representing a 16 bit bitmask
        if all(char in string.hexdigits for char in mask) and len(mask) == 4:
            response, ok = checkSuccess(self, f"AT+MASK={mask}")
            if ok:
                return response
        else:
            logging.info("This must a be a 4 digit hexdigit mask")

    def getEightChannelMode(self):
        response, ok = checkSuccess(self, "AT+CHE=?")
        if ok:
            return response

    def setEightChannelMode(
        self, value1: int = 0, value2: int = 0, value3: int = 0, value4: int = 0
    ):
        # This mode is only for US915, AU915, CN470 AND LA915
        # Each of these regions has specific ranges of values so keep that in mind
        # These value must be between 0 and 9 or 0 and 12 for CN470
        response, ok = checkSuccess(self, f"AT+CHE={value1}:{value2}:{value3}:{value4}")
        if ok:
            return response

    def getSingleChannelModeFreq(self):
        response, ok = checkSuccess(self, "AT+CHS=?")
        if ok:
            return response

    def setSingleChannelModeFreq(self, freq: int):
        response, ok = checkSuccess(self, f"AT+CHS={freq}")
        if ok:
            return response

    def getFreqBand(self):
        response, ok = checkSuccess(self, "AT+BAND=?")
        if ok:
            return response

    def setFreqBand(self, band: int):
        # value must be between 0 and 12
        if band < 0 or band > 12:
            logging.info("Value must be between 0 and 12")
        else:
            response, ok = checkSuccess(self, f"AT+BAND={band}")
            if ok:
                return response

    ####################################################
    ######### LoRaWAN Multicast Group Commands #########
    ####################################################

    def setMulticastGroup(
        self,
        classL: str,
        dev_addr: str,
        nwk_s_key: str,
        app_s_key: str,
        freq: int,
        datarate: int,
        periodicity: int,
    ):
        if classL not in ("B", "C"):
            logging.warning("Multicast class must be either B or C")
            return None
        if not (
            all(char in string.hexdigits for char in dev_addr) and len(dev_addr) == 8
        ):
            logging.warning("dev_addr must be exactly 8 hexdigits")
            return None
        if not (
            all(char in string.hexdigits for char in nwk_s_key) and len(nwk_s_key) == 32
        ):
            logging.warning("Network key must be exactly 32 hexdigits")
            return None
        if not (
            all(char in string.hexdigits for char in app_s_key) and len(app_s_key) == 32
        ):
            logging.warning("App key must be exactly 32 hexdigits")
            return None
        if datarate < 0 or datarate > 7:
            logging.warning("Datarate must be between 0 and 7")
            return None
        if periodicity < 0 or periodicity > 7:
            logging.warning("Periodicity must be between 0 and 7")
            return None
        response, ok = checkSuccess(
            self,
            f"AT+ADDMULC={classL}:{dev_addr}:{nwk_s_key}:{app_s_key}:{freq}:{datarate}:{periodicity}",
        )
        if ok:
            return response

    def removeMulticastGroup(self, dev_addr: str):
        if all(char in string.hexdigits for char in dev_addr) and len(dev_addr) == 8:
            response, ok = checkSuccess(self, f"AT+RMVMULC={dev_addr}")
            if ok:
                return response
        else:
            logging.info("Device address must be exactly 8 hexdigits")

    def getMulticastGroup(self):
        response, ok = checkSuccess(self, "AT+LSTMULC=?")
        if ok:
            return response

    ####################################
    ######### P2P Instructions #########
    ####################################
