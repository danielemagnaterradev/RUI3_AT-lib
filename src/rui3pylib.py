import logging
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


# This class wraps all RUI3 AT commands as methods.
# On initialization, if no port is specified, it scans all available serial ports
# and connects to the first RUI3-compatible device found.


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
        # ATZ does not return OK: the module resets immediately without a return code.
        # sendCommand is used directly instead of checkSuccess.
        sendCommand(self, "ATZ")
        logging.info("Module reset")

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

    def setDeviceAlias(self, alias: str):
        # Must be between 1 and 16 characters.
        if len(alias) < 1 or len(alias) > 16:
            logging.warning("Alias must be between 1 and 16 characters")
            return None
        response, ok = checkSuccess(self, f"AT+ALIAS={alias}")
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
        # Input must be exactly 12 hexadecimal characters (e.g. 001122334455),
        # which are formatted internally as colon-separated pairs (e.g. 00:11:22:33:44:55).
        if all(char in string.hexdigits for char in mac) and len(mac) == 12:
            formatted = ":".join(mac[i : i + 2] for i in range(0, 12, 2))
            response, ok = checkSuccess(self, f"AT+BLEMAC={formatted.lower()}")
            if ok:
                return response
        else:
            logging.warning("Invalid format: it should be like 001122334455")

    def getBootVer(self):
        response, ok = checkSuccess(self, "AT+BOOTVER=?")
        if ok:
            return response

    ######################################
    ######### LOW POWER COMMANDS #########
    ######################################

    def atSleep(self, duration_ms: int):
        response, ok = checkSuccess(self, f"AT+SLEEP={duration_ms}")
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
        # Only effective on RAK3172; has no effect on other modules.
        # Stop1 Mode allows wakeup via both UART1 and UART2.
        # Stop2 Mode is more power-efficient but only UART2 can wake the device.
        response, ok = checkSuccess(self, "AT+LPMLVL=?")
        if ok:
            return response

    def setLowPowerModeLevel(self, level: int):
        # Only effective on RAK3172; has no effect on other modules.
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
        # Locks the serial port; a password is required to unlock it.
        # The default password is 00000000 and can be changed with setPassword().
        # AT+LOCK does not return OK.
        _ = sendCommand(self, "AT+LOCK")
        logging.info(f"Serial port {self.port} is now locked")

    def setPassword(self, password: str):
        if len(password) < 1 or len(password) > 8:
            logging.warning("Password must be between 1 and 8 characters")
            return None
        response, ok = checkSuccess(self, f"AT+PWORD={password}")
        if ok:
            return response

    def getBaudRate(self):
        response, ok = checkSuccess(self, "AT+BAUD=?")
        if ok:
            return response

    def setBaudRate(self, baudrate: int):
        # The configured baud rate is retained even after reset or power recycle.
        response, ok = checkSuccess(self, f"AT+BAUD={baudrate}")
        if ok:
            return response

    def switchToATMode(self):
        response, ok = checkSuccess(self, "AT+ATM")
        if ok:
            return response

    #######################################
    ######### BOOTLOADER COMMANDS #########
    #######################################

    # All methods in this section except setBootMode() only work while in boot mode.

    def setBootMode(self):
        # Enters bootloader mode for firmware upgrade.
        # To leave boot mode, call atRun().
        # AT_BUSY_ERROR is returned if the bootloader process is already running.
        response, ok = checkSuccess(self, "AT+BOOT")
        if ok:
            return response

    def getBootloaderVer(self):
        # Uses AT+VERSION (boot mode only), which is distinct from AT+VER=? used by getFirmVersion() in normal mode.
        return sendCommand(self, "AT+VERSION")

    def getBootloaderStatus(self):
        # AT+BOOTSTATUS does not return OK; sendCommand is used directly.
        return sendCommand(self, "AT+BOOTSTATUS")

    def atRun(self):
        # AT+RUN does not return OK; sendCommand is used directly.
        return sendCommand(self, "AT+RUN")

    def bootReset(self):
        # AT+RESET does not return OK; sendCommand is used directly.
        return sendCommand(self, "AT+RESET")

    def bootUpdate(self):
        # Starts Y-modem receiving process.
        # AT+UPDATE does not return OK; sendCommand is used directly.
        return sendCommand(self, "AT+UPDATE")

    #######################################
    ######### LORAWAN KEYS AND IDs ########
    #######################################

    def getDeviceEUI(self):
        response, ok = checkSuccess(self, "AT+DEVEUI=?")
        if ok:
            return response

    def setDeviceEUI(self, deveui: str):
        # Must be exactly 16 hexadecimal characters, representing 8 bytes (MSB first).
        if all(char in string.hexdigits for char in deveui) and len(deveui) == 16:
            response, ok = checkSuccess(self, f"AT+DEVEUI={deveui}")
            if ok:
                return response
        else:
            logging.warning("Device EUI must be exactly 16 hexdigits")
            return None

    # The format rules above (only hexadecimal characters, MSB first) apply to all setter methods in this section.

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
            logging.warning("App EUI must be exactly 16 hexdigits")
            return None

    def getAppKey(self):
        response, ok = checkSuccess(self, "AT+APPKEY=?")
        if ok:
            return response

    def setAppKey(self, appkey: str):
        if all(char in string.hexdigits for char in appkey) and len(appkey) == 32:
            response, ok = checkSuccess(self, f"AT+APPKEY={appkey}")
            if ok:
                return response
        else:
            logging.warning("App key must be exactly 32 hexdigits")
            return None

    def getDevAddr(self):
        response, ok = checkSuccess(self, "AT+DEVADDR=?")
        if ok:
            return response

    def setDevAddr(self, devaddr: str):
        if all(char in string.hexdigits for char in devaddr) and len(devaddr) == 8:
            response, ok = checkSuccess(self, f"AT+DEVADDR={devaddr}")
            if ok:
                return response
        else:
            logging.warning("Device address must be exactly 8 hexdigits")
            return None

    def getAppSKey(self):
        response, ok = checkSuccess(self, "AT+APPSKEY=?")
        if ok:
            return response

    def setAppSKey(self, appskey: str):
        if all(char in string.hexdigits for char in appskey) and len(appskey) == 32:
            response, ok = checkSuccess(self, f"AT+APPSKEY={appskey}")
            if ok:
                return response
        else:
            logging.warning("App security key must be exactly 32 hexdigits")
            return None

    def getNetworkSKey(self):
        response, ok = checkSuccess(self, "AT+NWKSKEY=?")
        if ok:
            return response

    def setNetworkSKey(self, netskey: str):
        if all(char in string.hexdigits for char in netskey) and len(netskey) == 32:
            response, ok = checkSuccess(self, f"AT+NWKSKEY={netskey}")
            if ok:
                return response
        else:
            logging.warning("Network security key must be exactly 32 hexdigits")
            return None

    def getNetworkID(self):
        response, ok = checkSuccess(self, "AT+NETID=?")
        if ok:
            return response

    def setNetworkID(self, netid: str):
        if all(char in string.hexdigits for char in netid) and len(netid) == 6:
            response, ok = checkSuccess(self, f"AT+NETID={netid}")
            if ok:
                return response
        else:
            logging.warning("Network ID must be exactly 6 hexdigits")
            return None

    def getMulticastRootKey(self):
        response, ok = checkSuccess(self, "AT+MCROOTKEY=?")
        if ok:
            return response

    ###############################################
    ######### LORAWAN JOINING AND SENDING #########
    ###############################################

    def getConfirmMode(self):
        response, ok = checkSuccess(self, "AT+CFM=?")
        if ok:
            return response

    def setConfirmMode(self, on: bool):
        # Configures uplink payload as confirmed (True) or unconfirmed (False).
        mode = 1 if on else 0
        response, ok = checkSuccess(self, f"AT+CFM={mode}")
        if ok:
            return response

    def getConfirmStatus(self):
        # Returns the confirmation status of the last AT+SEND command (0 = failed, 1 = success).
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
        # Sends AT+JOIN=<join>:<auto_join>:<interval>:<join_attempts>.
        # This is an asynchronous command; OK means the join process has started.
        # Use getNetworkJoinStatus() to poll for the result.
        # interval: reattempt interval in seconds (7–255).
        # join_attempts: number of join attempts (0–255); 0 means unlimited.
        join_bin = 1 if join else 0
        auto_join_bin = 1 if auto_join else 0
        if interval < 7 or interval > 255:
            logging.warning("Reattempt value must be within 7 and 255")
            return None
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
            logging.warning("Parameter must be either 0 (ABP) or 1 (OTAA)")
            return None
        response, ok = checkSuccess(self, f"AT+NJM={mode}")
        if ok:
            return response

    def getNetworkJoinStatus(self):
        response, ok = checkSuccess(self, "AT+NJS=?")
        if ok:
            return response

    def getLastReceivedData(self):
        # Returns the last received downlink as <port>:<payload>.
        # Returns "0:" if no data has been received since the last call.
        response, ok = checkSuccess(self, "AT+RECV=?")
        if ok:
            return response

    def sendData(self, port: int, payload: str):
        # Port number must be within 1 and 233
        # Payload must be within 2 and 500 digit length (even number), representing 1 to 256 hex bytes
        if port < 1 or port > 233:
            logging.warning("Port must be between 1 and 233")
            return None
        if not all(char in string.hexdigits for char in payload):
            logging.warning("Payload must only contain hexadecimal characters")
            return None
        if len(payload) < 2 or len(payload) > 500 or len(payload) % 2 != 0:
            logging.warning("Payload length must be an even number between 2 and 500")
            return None
        response, ok = checkSuccess(self, f"AT+SEND={port}:{payload}")
        if ok:
            return response

    def sendLongPacketData(self, port: int, ack: bool, payload: str):
        # Sends a long packet payload (up to 1000 bytes) on the given port.
        # This is an asynchronous command; OK means the send process has started.
        # Only supported for uplink packets and requires a WisGate Edge gateway.
        ack_bool = 1 if ack else 0
        if port < 1 or port > 233:
            logging.warning("Port must be between 1 and 233")
            return None
        if not all(char in string.hexdigits for char in payload):
            logging.warning("Payload must only contain hexadecimal characters")
            return None
        if len(payload) < 2 or len(payload) > 2000 or len(payload) % 2 != 0:
            logging.warning("Payload length must be an even number between 2 and 2000")
            return None
        response, ok = checkSuccess(self, f"AT+LPSEND={port}:{ack_bool}:{payload}")
        if ok:
            return response

    def getConfirmPacketRetransmission(self):
        response, ok = checkSuccess(self, "AT+RETY=?")
        if ok:
            return response

    def setConfirmPacketRetransmission(self, tries: int):
        if tries < 0 or tries > 7:
            logging.warning("Invalid number: must be within 0 and 7")
            return None
        response, ok = checkSuccess(self, f"AT+RETY={tries}")
        if ok:
            return response

    ###############################################
    ######### LORAWAN NETWORK MANAGEMENT ##########
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
        if lorawan_class.upper() not in ("A", "B", "C"):
            logging.warning("LoRaWAN class must be either A, B or C")
            return None
        response, ok = checkSuccess(self, f"AT+CLASS={lorawan_class.upper()}")
        if ok:
            return response

    def getDutyCycle(self):
        response, ok = checkSuccess(self, "AT+DCS=?")
        if ok:
            return response

    def setDutyCycle(self, on: bool):
        # Duty cycle enforcement is mandatory in some regions (e.g. EU868); disable with caution.
        mode = 1 if on else 0
        response, ok = checkSuccess(self, f"AT+DCS={mode}")
        if ok:
            return response

    def getDataRate(self):
        response, ok = checkSuccess(self, "AT+DR=?")
        if ok:
            return response

    def setDataRate(self, data_rate: int):
        # Valid range varies by region; 0–7 is the widest possible range across all supported bands.
        if data_rate < 0 or data_rate > 7:
            logging.warning("Data rate must be between 0 and 7")
            return None
        response, ok = checkSuccess(self, f"AT+DR={data_rate}")
        if ok:
            return response

    def getJoinDelayRXWindow1(self):
        response, ok = checkSuccess(self, "AT+JN1DL=?")
        if ok:
            return response

    def setJoinDelayRXWindow1(self, value: int):
        if value < 1 or value > 14:
            logging.warning("Value must be within 1 and 14")
            return None
        response, ok = checkSuccess(self, f"AT+JN1DL={value}")
        if ok:
            return response

    def getJoinDelayRXWindow2(self):
        response, ok = checkSuccess(self, "AT+JN2DL=?")
        if ok:
            return response

    def setJoinDelayRXWindow2(self, value: int):
        # Must be greater than the value set by setJoinDelayRXWindow1(); range is 2–15 seconds.
        if value < 2 or value > 15:
            logging.warning("Value must be within 2 and 15")
            return None
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
            logging.warning("Value must be between 1 and 15")
            return None
        response, ok = checkSuccess(self, f"AT+RX1DL={value}")
        if ok:
            return response

    def getReceiveWindow2Delay(self):
        response, ok = checkSuccess(self, "AT+RX2DL=?")
        if ok:
            return response

    def setReceiveWindow2Delay(self, value: int):
        if value < 2 or value > 15:
            logging.warning("Value must be between 2 and 15")
            return None
        response, ok = checkSuccess(self, f"AT+RX2DL={value}")
        if ok:
            return response

    def getReceiveWindow2DataRate(self):
        response, ok = checkSuccess(self, "AT+RX2DR=?")
        if ok:
            return response

    def setReceiveWindow2DataRate(self, value: int):
        # Valid range varies by region: 0–5 for EU/AS/KR/CN, 8–13 for US915/AU915/LA915.
        if value < 0 or value > 13:
            logging.warning("Value must be between 0 and 13")
            return None
        response, ok = checkSuccess(self, f"AT+RX2DR={value}")
        if ok:
            return response

    def getReceiveWindow2Freq(self):
        response, ok = checkSuccess(self, "AT+RX2FQ=?")
        if ok:
            return response

    def setReceiveWindow2Freq(self, freq: int):
        response, ok = checkSuccess(self, f"AT+RX2FQ={freq}")
        if ok:
            return response

    def getTransmitPower(self):
        response, ok = checkSuccess(self, "AT+TXP=?")
        if ok:
            return response

    def setTransmitPower(self, value: int):
        # Valid range depends on region (0 = highest power):
        #   EU433: 0-5 | EU868/CN470/KR920/AS923/RU864: 0-7
        #   IN865: 0-10 | US915/AU915: 0-14
        if value < 0 or value > 14:
            logging.warning("Value must be between 0 and 14")
            return None
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
            logging.warning("Value must be either 0, 1 or 2")
            return None
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
        # Threshold RSSI level (in dBm) below which the channel is considered free.
        response, ok = checkSuccess(self, f"AT+LBTRSSI={value}")
        if ok:
            return response

    def getListenBeforeTalkScanTime(self):
        response, ok = checkSuccess(self, "AT+LBTSCANTIME=?")
        if ok:
            return response

    def setListenBeforeTalkScanTime(self, value: int):
        # Duration (in milliseconds) to scan the channel before transmitting.
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
            logging.warning("Value must be between 0 and 7")
            return None
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

    # These commands are region-specific and govern frequency bands and regulatory compliance.
    # Input validation is minimal; it is the caller's responsibility to pass values
    # that are legal for the target region and deployment.

    def getMask(self):
        response, ok = checkSuccess(self, "AT+MASK=?")
        if ok:
            return response

    def setMask(self, mask: str):
        # Must be exactly 4 hexadecimal characters, representing a 16-bit channel bitmask.
        # Only applicable to US915, AU915, CN470, and LA915 regions.
        if all(char in string.hexdigits for char in mask) and len(mask) == 4:
            response, ok = checkSuccess(self, f"AT+MASK={mask}")
            if ok:
                return response
        else:
            logging.warning("This must be a 4 digit hexdigit mask")
            return None

    def getEightChannelMode(self):
        response, ok = checkSuccess(self, "AT+CHE=?")
        if ok:
            return response

    def setEightChannelMode(
        self, value1: int = 0, value2: int = 0, value3: int = 0, value4: int = 0
    ):
        # Only applicable to US915, AU915, CN470, and LA915 regions.
        # Each parameter selects an 8-channel sub-band; valid range is 0–9 (0–12 for CN470).
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
        if band < 0 or band > 12:
            logging.warning("Value must be between 0 and 12")
            return None
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
        # Class B and Class C use the same command parameters.
        # The periodicity parameter is required even for Class C, where it has no functional effect.
        if classL.upper() not in ("B", "C"):
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
            f"AT+ADDMULC={classL.upper()}:{dev_addr}:{nwk_s_key}:{app_s_key}:{freq}:{datarate}:{periodicity}",
        )
        if ok:
            return response

    def removeMulticastGroup(self, dev_addr: str):
        if all(char in string.hexdigits for char in dev_addr) and len(dev_addr) == 8:
            response, ok = checkSuccess(self, f"AT+RMVMULC={dev_addr}")
            if ok:
                return response
        else:
            logging.warning("Device address must be exactly 8 hexdigits")
            return None

    def getMulticastGroup(self):
        response, ok = checkSuccess(self, "AT+LSTMULC=?")
        if ok:
            return response

    ####################################
    ######### P2P Instructions #########
    ####################################

    def getLoraNetworkMode(self):
        response, ok = checkSuccess(self, "AT+NWM=?")
        if ok:
            return response

    def setLoraNetworkMode(self, mode: int):
        # 0 - P2P_LORA
        # 1 - LoRaWAN
        # 2 - P2P_FSK
        if mode not in (0, 1, 2):
            logging.warning("Mode must be either 0, 1 or 2")
            return None
        response, ok = checkSuccess(self, f"AT+NWM={mode}")
        if ok:
            return response

    def getP2PFreq(self):
        response, ok = checkSuccess(self, "AT+PFREQ=?")
        if ok:
            return response

    def setP2PFreq(self, freq: int):
        response, ok = checkSuccess(self, f"AT+PFREQ={freq}")
        if ok:
            return response

    def getSpreadFactor(self):
        response, ok = checkSuccess(self, "AT+PSF=?")
        if ok:
            return response

    def setSpreadFactor(self, spread: int = 7):
        if spread not in (5, 6, 7, 8, 9, 10, 11, 12):
            logging.warning("Value must be between 5 and 12")
            return None
        response, ok = checkSuccess(self, f"AT+PSF={spread}")
        if ok:
            return response

    def getP2PBand(self):
        response, ok = checkSuccess(self, "AT+PBW=?")
        if ok:
            return response

    def setP2PBand(self, band: int = 0):
        if not 0 <= band <= 9:
            logging.warning("Value must be between 0 and 9")
            return None
        response, ok = checkSuccess(self, f"AT+PBW={band}")
        if ok:
            return response
