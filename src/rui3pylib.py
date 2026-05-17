import logging
import serial
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

    def setDeviceAlias(self, alias: str):
        response, ok = checkSuccess(self, f"AT+ALIAS={alias}")
        return response

    def getSystemVoltage(self):
        response, ok = checkSuccess(self, "AT+SYSV=?")
        return response

