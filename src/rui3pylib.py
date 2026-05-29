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


def send_command(port: serial.Serial, cmd: str, wait: float = 3.0):
    port.reset_input_buffer()
    full_cmd = cmd.strip() + "\r\n"
    port.write(full_cmd.encode(errors="replace"))
    time.sleep(wait)

    response = ""
    while port.in_waiting:
        response += port.read(port.in_waiting).decode(errors="replace")
        time.sleep(1.0)

    # Filter out firmware debug lines
    response = "\n".join(
        line for line in response.splitlines() if not line.startswith("[APP]")
    )
    return response


def check_success(port: serial.Serial, cmd: str, wait: float = 3.0):
    response = send_command(port, cmd, wait)
    ok = "OK" in response
    clean = response.replace("OK", "").strip()
    logging.info(f"[{_status(ok)}] {cmd}" + (f" -> {clean}" if clean else ""))
    return response, ok


# This class wraps all RUI3 AT commands as methods.
# On initialization, if no port is specified, it scans all available
# serial ports and connects to the first RUI3-compatible device found.


class RUI3Node(serial.Serial):
    def __init__(
        self,
        port: str | None = None,
        baudrate: int = 115200,
        timeout: float = 3.0,
    ):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        if port is None:
            while True:
                for interface in comports():
                    try:
                        self.port = interface.device
                        self.open()
                        if self.try_connect():
                            logging.info(f"Connected to port {self.port}")
                            break
                        else:
                            self.close()
                            continue
                    except serial.serialutil.SerialException as e:
                        logging.info(f"SerialException on {self.port}: {e}")
                        if self.is_open:
                            self.close()
                            break
                break
        else:
            try:
                self.open()
                if self.try_connect():
                    logging.info(f"Connected to port {self.port}")
                else:
                    self.close()
            except serial.serialutil.SerialException as e:
                logging.info(f"SerialException on {self.port}: {e}")
                if self.is_open:
                    self.close()

    def try_connect(self):
        try:
            _, ok = check_success(self, "AT", 5.0)
            return ok
        except serial.serialutil.PortNotOpenError:
            logging.info("Port not open")
            return False

    # GENERAL COMMANDS

    def ping(self):
        response, ok = check_success(self, "AT")
        if ok:
            return response

    def help(self):
        response, ok = check_success(self, "AT?")
        if ok:
            return response

    def toggle_command_echo(self):
        response, ok = check_success(self, "ATE")
        if ok:
            return response

    def reset(self):
        # ATZ does not return OK: the module resets immediately without
        # a return code. send_command is used directly instead of
        # check_success.
        send_command(self, "ATZ")
        logging.info("Module reset")

    def restore_default(self):
        response, ok = check_success(self, "ATR")
        if ok:
            logging.info("Restored default values")
            return response

    def get_serial_number(self):
        response, ok = check_success(self, "AT+SN=?")
        if ok:
            return response

    def get_battery_level(self):
        response, ok = check_success(self, "AT+BAT=?")
        if ok:
            return response

    def get_build_time(self):
        response, ok = check_success(self, "AT+BUILDTIME=?")
        if ok:
            return response

    def get_repo_info(self):
        response, ok = check_success(self, "AT+REPOINFO=?")
        if ok:
            return response

    def get_firm_version(self):
        response, ok = check_success(self, "AT+VER=?")
        if ok:
            return response

    def get_at_version(self):
        response, ok = check_success(self, "AT+CLIVER=?")
        if ok:
            return response

    def get_api_version(self):
        response, ok = check_success(self, "AT+APIVER=?")
        if ok:
            return response

    def get_hw_model(self):
        response, ok = check_success(self, "AT+HWMODEL=?")
        if ok:
            return response

    def get_hw_id(self):
        response, ok = check_success(self, "AT+HWID=?")
        if ok:
            return response

    def get_device_alias(self):
        response, ok = check_success(self, "AT+ALIAS=?")
        if ok:
            return response

    def set_device_alias(self, alias: str):
        # Must be between 1 and 16 characters.
        if len(alias) < 1 or len(alias) > 16:
            logging.warning("Alias must be between 1 and 16 characters")
            return None
        response, ok = check_success(self, f"AT+ALIAS={alias}")
        if ok:
            return response

    def get_system_voltage(self):
        response, ok = check_success(self, "AT+SYSV=?")
        if ok:
            return response

    def get_ble_mac(self):
        response, ok = check_success(self, "AT+BLEMAC=?")
        if ok:
            return response

    def set_ble_mac(self, mac: str):
        # Input must be exactly 12 hexadecimal characters
        # (e.g. 001122334455), which are formatted internally as
        # colon-separated pairs (e.g. 00:11:22:33:44:55).
        if all(char in string.hexdigits for char in mac) and len(mac) == 12:
            formatted = ":".join(mac[i : i + 2] for i in range(0, 12, 2))
            response, ok = check_success(self, f"AT+BLEMAC={formatted.lower()}")
            if ok:
                return response
        else:
            logging.warning("Invalid format: it should be like 001122334455")

    def get_boot_ver(self):
        response, ok = check_success(self, "AT+BOOTVER=?")
        if ok:
            return response

    # LOW POWER COMMANDS

    def at_sleep(self, duration_ms: int):
        response, ok = check_success(self, f"AT+SLEEP={duration_ms}")
        if ok:
            return response

    def get_low_power_mode(self):
        response, ok = check_success(self, "AT+LPM=?")
        if ok:
            return response

    def set_low_power_mode(self, on: bool):
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+LPM={mode}")
        if ok:
            return response

    def get_low_power_mode_level(self):
        # Only effective on RAK3172; has no effect on other modules.
        # Stop1 Mode allows wakeup via both UART1 and UART2.
        # Stop2 Mode is more power-efficient but only UART2 can wake
        # the device.
        response, ok = check_success(self, "AT+LPMLVL=?")
        if ok:
            return response

    def set_low_power_mode_level(self, level: int):
        # Only effective on RAK3172; has no effect on other modules.
        # level 1 = STOP1 Mode, level 2 = STOP2 Mode
        if level != 1 and level != 2:
            logging.warning("Level must be either 1 (STOP1) or 2 (STOP2)")
            return None
        response, ok = check_success(self, f"AT+LPMLVL={level}")
        if ok:
            return response

    # SERIAL AT COMMANDS

    def lock_serial(self):
        # Locks the serial port; a password is required to unlock it.
        # The default password is 00000000 and can be changed with
        # set_password(). AT+LOCK does not return OK.
        _ = send_command(self, "AT+LOCK")
        logging.info(f"Serial port {self.port} is now locked")

    def set_password(self, password: str):
        if len(password) < 1 or len(password) > 8:
            logging.warning("Password must be between 1 and 8 characters")
            return None
        response, ok = check_success(self, f"AT+PWORD={password}")
        if ok:
            return response

    def get_baud_rate(self):
        response, ok = check_success(self, "AT+BAUD=?")
        if ok:
            return response

    def set_baud_rate(self, baudrate: int):
        # The configured baud rate is retained even after reset or
        # power recycle.
        response, ok = check_success(self, f"AT+BAUD={baudrate}")
        if ok:
            return response

    def switch_to_at_mode(self):
        response, ok = check_success(self, "AT+ATM")
        if ok:
            return response

    # BOOTLOADER COMMANDS
    # All methods in this section except set_boot_mode() only work
    # while in boot mode.

    def set_boot_mode(self):
        # Enters bootloader mode for firmware upgrade.
        # To leave boot mode, call at_run().
        # AT_BUSY_ERROR is returned if the bootloader process is
        # already running.
        response, ok = check_success(self, "AT+BOOT")
        if ok:
            return response

    def get_bootloader_ver(self):
        # Uses AT+VERSION (boot mode only), which is distinct from
        # AT+VER=? used by get_firm_version() in normal mode.
        return send_command(self, "AT+VERSION")

    def get_bootloader_status(self):
        # AT+BOOTSTATUS does not return OK; send_command is used
        # directly.
        return send_command(self, "AT+BOOTSTATUS")

    def at_run(self):
        # AT+RUN does not return OK; send_command is used directly.
        return send_command(self, "AT+RUN")

    def boot_reset(self):
        # AT+RESET does not return OK; send_command is used directly.
        return send_command(self, "AT+RESET")

    def boot_update(self):
        # Starts Y-modem receiving process.
        # AT+UPDATE does not return OK; send_command is used directly.
        return send_command(self, "AT+UPDATE")

    # LORAWAN KEYS AND IDs

    def get_device_eui(self):
        response, ok = check_success(self, "AT+DEVEUI=?")
        if ok:
            return response

    def set_device_eui(self, deveui: str):
        # Must be exactly 16 hexadecimal characters, representing
        # 8 bytes (MSB first).
        if all(char in string.hexdigits for char in deveui) and len(deveui) == 16:
            response, ok = check_success(self, f"AT+DEVEUI={deveui}")
            if ok:
                return response
        else:
            logging.warning("Device EUI must be exactly 16 hexdigits")
            return None

    # The format rules above (only hexadecimal characters, MSB first)
    # apply to all setter methods in this section.

    def get_app_eui(self):
        response, ok = check_success(self, "AT+APPEUI=?")
        if ok:
            return response

    def set_app_eui(self, appeui: str):
        if all(char in string.hexdigits for char in appeui) and len(appeui) == 16:
            response, ok = check_success(self, f"AT+APPEUI={appeui}")
            if ok:
                return response
        else:
            logging.warning("App EUI must be exactly 16 hexdigits")
            return None

    def get_app_key(self):
        response, ok = check_success(self, "AT+APPKEY=?")
        if ok:
            return response

    def set_app_key(self, appkey: str):
        if all(char in string.hexdigits for char in appkey) and len(appkey) == 32:
            response, ok = check_success(self, f"AT+APPKEY={appkey}")
            if ok:
                return response
        else:
            logging.warning("App key must be exactly 32 hexdigits")
            return None

    def get_dev_addr(self):
        response, ok = check_success(self, "AT+DEVADDR=?")
        if ok:
            return response

    def set_dev_addr(self, devaddr: str):
        if all(char in string.hexdigits for char in devaddr) and len(devaddr) == 8:
            response, ok = check_success(self, f"AT+DEVADDR={devaddr}")
            if ok:
                return response
        else:
            logging.warning("Device address must be exactly 8 hexdigits")
            return None

    def get_app_s_key(self):
        response, ok = check_success(self, "AT+APPSKEY=?")
        if ok:
            return response

    def set_app_s_key(self, appskey: str):
        if all(char in string.hexdigits for char in appskey) and len(appskey) == 32:
            response, ok = check_success(self, f"AT+APPSKEY={appskey}")
            if ok:
                return response
        else:
            logging.warning("App security key must be exactly 32 hexdigits")
            return None

    def get_network_s_key(self):
        response, ok = check_success(self, "AT+NWKSKEY=?")
        if ok:
            return response

    def set_network_s_key(self, netskey: str):
        if all(char in string.hexdigits for char in netskey) and len(netskey) == 32:
            response, ok = check_success(self, f"AT+NWKSKEY={netskey}")
            if ok:
                return response
        else:
            logging.warning("Network security key must be exactly 32 hexdigits")
            return None

    def get_network_id(self):
        response, ok = check_success(self, "AT+NETID=?")
        if ok:
            return response

    def set_network_id(self, netid: str):
        if all(char in string.hexdigits for char in netid) and len(netid) == 6:
            response, ok = check_success(self, f"AT+NETID={netid}")
            if ok:
                return response
        else:
            logging.warning("Network ID must be exactly 6 hexdigits")
            return None

    def get_multicast_root_key(self):
        response, ok = check_success(self, "AT+MCROOTKEY=?")
        if ok:
            return response

    # LORAWAN JOINING AND SENDING

    def get_confirm_mode(self):
        response, ok = check_success(self, "AT+CFM=?")
        if ok:
            return response

    def set_confirm_mode(self, on: bool):
        # Configures uplink payload as confirmed (True) or unconfirmed
        # (False).
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+CFM={mode}")
        if ok:
            return response

    def get_confirm_status(self):
        # Returns the confirmation status of the last AT+SEND command
        # (0 = failed, 1 = success).
        response, ok = check_success(self, "AT+CFS=?")
        if ok:
            return response

    def get_join_params(self):
        response, ok = check_success(self, "AT+JOIN=?")
        if ok:
            return response

    def try_join(
        self,
        join: bool = True,
        auto_join: bool = False,
        interval: int = 8,
        join_attempts: int = 0,
    ):
        # Sends AT+JOIN=<join>:<auto_join>:<interval>:<join_attempts>.
        # This is an asynchronous command; OK means the join process
        # has started. Use get_network_join_status() to poll for the
        # result.
        # interval: reattempt interval in seconds (7-255).
        # join_attempts: number of join attempts (0-255); 0 = unlimited.
        join_bin = 1 if join else 0
        auto_join_bin = 1 if auto_join else 0
        if interval < 7 or interval > 255:
            logging.warning("Reattempt value must be within 7 and 255")
            return None
        if join_attempts < 0 or join_attempts > 255:
            logging.warning("No. of join attempts must be between 0 and 255")
            return None
        response, ok = check_success(
            self,
            f"AT+JOIN={join_bin}:{auto_join_bin}:{interval}:{join_attempts}",
        )
        if ok:
            return response

    def get_network_join_mode(self):
        response, ok = check_success(self, "AT+NJM=?")
        if ok:
            return response

    def set_network_join_mode(self, mode: int = 0):
        # 0 = ABP mode
        # 1 = OTAA mode
        if mode != 0 and mode != 1:
            logging.warning("Parameter must be either 0 (ABP) or 1 (OTAA)")
            return None
        response, ok = check_success(self, f"AT+NJM={mode}")
        if ok:
            return response

    def get_network_join_status(self):
        response, ok = check_success(self, "AT+NJS=?")
        if ok:
            return response

    def get_last_received_data(self):
        # Returns the last received downlink as <port>:<payload>.
        # Returns "0:" if no data has been received since the last
        # call.
        response, ok = check_success(self, "AT+RECV=?")
        if ok:
            return response

    def send_data(self, port: int, payload: str):
        # Port number must be within 1 and 233.
        # Payload must be within 2 and 500 digit length (even number),
        # representing 1 to 256 hex bytes.
        if port < 1 or port > 233:
            logging.warning("Port must be between 1 and 233")
            return None
        if not all(char in string.hexdigits for char in payload):
            logging.warning("Payload must only contain hexadecimal characters")
            return None
        if len(payload) < 2 or len(payload) > 500 or len(payload) % 2 != 0:
            logging.warning("Payload length must be an even number between 2 and 500")
            return None
        response, ok = check_success(self, f"AT+SEND={port}:{payload}")
        if ok:
            return response

    def send_long_packet_data(self, port: int, ack: bool, payload: str):
        # Sends a long packet payload (up to 1000 bytes) on the given
        # port. This is an asynchronous command; OK means the send
        # process has started.
        # Only supported for uplink packets and requires a WisGate Edge
        # gateway.
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
        response, ok = check_success(self, f"AT+LPSEND={port}:{ack_bool}:{payload}")
        if ok:
            return response

    def get_confirm_packet_retransmission(self):
        response, ok = check_success(self, "AT+RETY=?")
        if ok:
            return response

    def set_confirm_packet_retransmission(self, tries: int):
        if tries < 0 or tries > 7:
            logging.warning("Invalid number: must be within 0 and 7")
            return None
        response, ok = check_success(self, f"AT+RETY={tries}")
        if ok:
            return response

    # LORAWAN NETWORK MANAGEMENT

    def get_adaptive_rate(self):
        response, ok = check_success(self, "AT+ADR=?")
        if ok:
            return response

    def set_adaptive_rate(self, on: bool):
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+ADR={mode}")
        if ok:
            return response

    def get_lorawan_class(self):
        response, ok = check_success(self, "AT+CLASS=?")
        if ok:
            return response

    def set_lorawan_class(self, lorawan_class: str):
        if lorawan_class.upper() not in ("A", "B", "C"):
            logging.warning("LoRaWAN class must be either A, B or C")
            return None
        response, ok = check_success(self, f"AT+CLASS={lorawan_class.upper()}")
        if ok:
            return response

    def get_duty_cycle(self):
        response, ok = check_success(self, "AT+DCS=?")
        if ok:
            return response

    def set_duty_cycle(self, on: bool):
        # Duty cycle enforcement is mandatory in some regions
        # (e.g. EU868); disable with caution.
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+DCS={mode}")
        if ok:
            return response

    def get_data_rate(self):
        response, ok = check_success(self, "AT+DR=?")
        if ok:
            return response

    def set_data_rate(self, data_rate: int):
        # Valid range varies by region; 0-7 is the widest possible
        # range across all supported bands.
        if data_rate < 0 or data_rate > 7:
            logging.warning("Data rate must be between 0 and 7")
            return None
        response, ok = check_success(self, f"AT+DR={data_rate}")
        if ok:
            return response

    def get_join_delay_rx_window_1(self):
        response, ok = check_success(self, "AT+JN1DL=?")
        if ok:
            return response

    def set_join_delay_rx_window_1(self, value: int):
        if value < 1 or value > 14:
            logging.warning("Value must be within 1 and 14")
            return None
        response, ok = check_success(self, f"AT+JN1DL={value}")
        if ok:
            return response

    def get_join_delay_rx_window_2(self):
        response, ok = check_success(self, "AT+JN2DL=?")
        if ok:
            return response

    def set_join_delay_rx_window_2(self, value: int):
        # Must be greater than the value set by
        # set_join_delay_rx_window_1(); range is 2-15 seconds.
        if value < 2 or value > 15:
            logging.warning("Value must be within 2 and 15")
            return None
        response, ok = check_success(self, f"AT+JN2DL={value}")
        if ok:
            return response

    def get_public_network_mode(self):
        response, ok = check_success(self, "AT+PNM=?")
        if ok:
            return response

    def set_public_network_mode(self, on: bool):
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+PNM={mode}")
        if ok:
            return response

    def get_receive_window_1_delay(self):
        response, ok = check_success(self, "AT+RX1DL=?")
        if ok:
            return response

    def set_receive_window_1_delay(self, value: int):
        if value < 1 or value > 15:
            logging.warning("Value must be between 1 and 15")
            return None
        response, ok = check_success(self, f"AT+RX1DL={value}")
        if ok:
            return response

    def get_receive_window_2_delay(self):
        response, ok = check_success(self, "AT+RX2DL=?")
        if ok:
            return response

    def set_receive_window_2_delay(self, value: int):
        if value < 2 or value > 15:
            logging.warning("Value must be between 2 and 15")
            return None
        response, ok = check_success(self, f"AT+RX2DL={value}")
        if ok:
            return response

    def get_receive_window_2_data_rate(self):
        response, ok = check_success(self, "AT+RX2DR=?")
        if ok:
            return response

    def set_receive_window_2_data_rate(self, value: int):
        # Valid range varies by region: 0-5 for EU/AS/KR/CN,
        # 8-13 for US915/AU915/LA915.
        if value < 0 or value > 13:
            logging.warning("Value must be between 0 and 13")
            return None
        response, ok = check_success(self, f"AT+RX2DR={value}")
        if ok:
            return response

    def get_receive_window_2_freq(self):
        response, ok = check_success(self, "AT+RX2FQ=?")
        if ok:
            return response

    def set_receive_window_2_freq(self, freq: int):
        response, ok = check_success(self, f"AT+RX2FQ={freq}")
        if ok:
            return response

    def get_transmit_power(self):
        response, ok = check_success(self, "AT+TXP=?")
        if ok:
            return response

    def set_transmit_power(self, value: int):
        # Valid range depends on region (0 = highest power):
        #   EU433: 0-5 | EU868/CN470/KR920/AS923/RU864: 0-7
        #   IN865: 0-10 | US915/AU915: 0-14
        if value < 0 or value > 14:
            logging.warning("Value must be between 0 and 14")
            return None
        response, ok = check_success(self, f"AT+TXP={value}")
        if ok:
            return response

    def get_link_check(self):
        response, ok = check_success(self, "AT+LINKCHECK=?")
        if ok:
            return response

    def set_link_check(self, value: int):
        # 0 - Disable link check
        # 1 - Execute link check just once on the next payload uplink
        # 2 - Module will automatically execute one-time link check
        #     after every payload uplink
        if value not in (0, 1, 2):
            logging.warning("Value must be either 0, 1 or 2")
            return None
        response, ok = check_success(self, f"AT+LINKCHECK={value}")
        if ok:
            return response

    def get_listen_before_talk(self):
        response, ok = check_success(self, "AT+LBT=?")
        if ok:
            return response

    def set_listen_before_talk(self, on: bool):
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+LBT={mode}")
        if ok:
            return response

    def get_listen_before_talk_rssi(self):
        response, ok = check_success(self, "AT+LBTRSSI=?")
        if ok:
            return response

    def set_listen_before_talk_rssi(self, value: int):
        # Threshold RSSI level (in dBm) below which the channel is
        # considered free.
        response, ok = check_success(self, f"AT+LBTRSSI={value}")
        if ok:
            return response

    def get_listen_before_talk_scan_time(self):
        response, ok = check_success(self, "AT+LBTSCANTIME=?")
        if ok:
            return response

    def set_listen_before_talk_scan_time(self, value: int):
        # Duration (in milliseconds) to scan the channel before
        # transmitting.
        response, ok = check_success(self, f"AT+LBTSCANTIME={value}")
        if ok:
            return response

    def get_time_req(self):
        response, ok = check_success(self, "AT+TIMEREQ=?")
        if ok:
            return response

    def set_time_req(self, on: bool):
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+TIMEREQ={mode}")
        if ok:
            return response

    def get_local_time(self):
        response, ok = check_success(self, "AT+LTIME=?")
        if ok:
            return response

    # CLASS B MODE

    def get_periodicity(self):
        response, ok = check_success(self, "AT+PGSLOT=?")
        if ok:
            return response

    def set_periodicity(self, value: int):
        if value < 0 or value > 7:
            logging.warning("Value must be between 0 and 7")
            return None
        response, ok = check_success(self, f"AT+PGSLOT={value}")
        if ok:
            return response

    def get_beacon_freq(self):
        response, ok = check_success(self, "AT+BFREQ=?")
        if ok:
            return response

    def get_beacon_time(self):
        response, ok = check_success(self, "AT+BTIME=?")
        if ok:
            return response

    def get_gw_info(self):
        response, ok = check_success(self, "AT+BGW=?")
        if ok:
            return response

    # LORAWAN INFORMATION

    def get_rssi(self):
        response, ok = check_success(self, "AT+RSSI=?")
        if ok:
            return response

    def get_all_channel_rssi(self):
        response, ok = check_success(self, "AT+ARSSI=?")
        if ok:
            return response

    def get_signal_to_noise_ratio(self):
        response, ok = check_success(self, "AT+SNR=?")
        if ok:
            return response

    # LORAWAN REGIONAL COMMANDS
    # These commands are region-specific and govern frequency bands and
    # regulatory compliance. Input validation is minimal; it is the
    # caller's responsibility to pass values that are legal for the
    # target region and deployment.

    def get_mask(self):
        response, ok = check_success(self, "AT+MASK=?")
        if ok:
            return response

    def set_mask(self, mask: str):
        # Must be exactly 4 hexadecimal characters, representing a
        # 16-bit channel bitmask.
        # Only applicable to US915, AU915, CN470, and LA915 regions.
        if all(char in string.hexdigits for char in mask) and len(mask) == 4:
            response, ok = check_success(self, f"AT+MASK={mask}")
            if ok:
                return response
        else:
            logging.warning("This must be a 4 digit hexadecimal characters mask")
            return None

    def get_eight_channel_mode(self):
        response, ok = check_success(self, "AT+CHE=?")
        if ok:
            return response

    def set_eight_channel_mode(
        self,
        value1: int = 0,
        value2: int = 0,
        value3: int = 0,
        value4: int = 0,
    ):
        # Only applicable to US915, AU915, CN470, and LA915 regions.
        # Each parameter selects an 8-channel sub-band; valid range is
        # 0-9 (0-12 for CN470).
        response, ok = check_success(
            self, f"AT+CHE={value1}:{value2}:{value3}:{value4}"
        )
        if ok:
            return response

    def get_single_channel_mode_freq(self):
        response, ok = check_success(self, "AT+CHS=?")
        if ok:
            return response

    def set_single_channel_mode_freq(self, freq: int):
        response, ok = check_success(self, f"AT+CHS={freq}")
        if ok:
            return response

    def get_freq_band(self):
        response, ok = check_success(self, "AT+BAND=?")
        if ok:
            return response

    def set_freq_band(self, band: int):
        if band < 0 or band > 12:
            logging.warning("Value must be between 0 and 12")
            return None
        response, ok = check_success(self, f"AT+BAND={band}")
        if ok:
            return response

    # LORAWAN MULTICAST GROUP COMMANDS

    def set_multicast_group(
        self,
        lorawan_class: str,
        dev_addr: str,
        nwk_s_key: str,
        app_s_key: str,
        freq: int,
        datarate: int,
        periodicity: int,
    ):
        # Class B and Class C use the same command parameters.
        # The periodicity parameter is required even for Class C,
        # where it has no functional effect.
        if lorawan_class.upper() not in ("B", "C"):
            logging.warning("Multicast class must be either B or C")
            return None
        if not (
            all(char in string.hexdigits for char in dev_addr) and len(dev_addr) == 8
        ):
            logging.warning("dev_addr must be exactly 8 hexadecimal characters")
            return None
        if not (
            all(char in string.hexdigits for char in nwk_s_key) and len(nwk_s_key) == 32
        ):
            logging.warning("Network key must be exactly 32 hexadecimal characters")
            return None
        if not (
            all(char in string.hexdigits for char in app_s_key) and len(app_s_key) == 32
        ):
            logging.warning("App key must be exactly 32 hexadecimal characters")
            return None
        if datarate < 0 or datarate > 7:
            logging.warning("Datarate must be between 0 and 7")
            return None
        if periodicity < 0 or periodicity > 7:
            logging.warning("Periodicity must be between 0 and 7")
            return None
        response, ok = check_success(
            self,
            f"AT+ADDMULC={lorawan_class.upper()}:{dev_addr}"
            f":{nwk_s_key}:{app_s_key}:{freq}:{datarate}:{periodicity}",
        )
        if ok:
            return response

    def remove_multicast_group(self, dev_addr: str):
        if all(char in string.hexdigits for char in dev_addr) and len(dev_addr) == 8:
            response, ok = check_success(self, f"AT+RMVMULC={dev_addr}")
            if ok:
                return response
        else:
            logging.warning("Device address must be exactly 8 hexadecimal characters")
            return None

    def get_multicast_group(self):
        response, ok = check_success(self, "AT+LSTMULC=?")
        if ok:
            return response

    # P2P INSTRUCTIONS

    def get_lora_network_mode(self):
        response, ok = check_success(self, "AT+NWM=?")
        if ok:
            return response

    def set_lora_network_mode(self, mode: int):
        # 0 - P2P_LORA
        # 1 - LoRaWAN
        # 2 - P2P_FSK
        if mode not in (0, 1, 2):
            logging.warning("Mode must be either 0, 1 or 2")
            return None
        response, ok = check_success(self, f"AT+NWM={mode}")
        if ok:
            return response

    def get_p2p_freq(self):
        response, ok = check_success(self, "AT+PFREQ=?")
        if ok:
            return response

    def set_p2p_freq(self, freq: int):
        response, ok = check_success(self, f"AT+PFREQ={freq}")
        if ok:
            return response

    def get_spread_factor(self):
        response, ok = check_success(self, "AT+PSF=?")
        if ok:
            return response

    def set_spread_factor(self, spread: int = 7):
        if spread not in (5, 6, 7, 8, 9, 10, 11, 12):
            logging.warning("Value must be between 5 and 12")
            return None
        response, ok = check_success(self, f"AT+PSF={spread}")
        if ok:
            return response

    def get_p2p_band(self):
        response, ok = check_success(self, "AT+PBW=?")
        if ok:
            return response

    def set_p2p_band(self, band: int = 0):
        if not 0 <= band <= 9:
            logging.warning("Value must be between 0 and 9")
            return None
        response, ok = check_success(self, f"AT+PBW={band}")
        if ok:
            return response

    def get_p2p_code_rate(self):
        response, ok = check_success(self, "AT+PCR=?")
        if ok:
            return response

    def set_p2p_code_rate(self, code_rate: int):
        if code_rate not in (0, 1, 2, 3):
            logging.warning("Code rate must be between 0 and 3")
            return None
        response, ok = check_success(self, f"AT+PCR={code_rate}")
        if ok:
            return response

    def get_p2p_preamble_length(self):
        response, ok = check_success(self, "AT+PPL=?")
        if ok:
            return response

    def set_p2p_preamble_length(self, length: int):
        if not 5 <= length <= 65535:
            logging.warning("Preamble length must be between 5 and 65535")
            return None
        response, ok = check_success(self, f"AT+PPL={length}")
        if ok:
            return response

    def get_p2p_tx_power(self):
        response, ok = check_success(self, "AT+PTP=?")
        if ok:
            return response

    def set_p2p_tx_power(self, tx_power: int):
        if not 5 <= tx_power <= 22:
            logging.warning("TX power must between 5 and 22")
            return None
        response, ok = check_success(self, f"AT+PTP={tx_power}")
        if ok:
            return response

    def get_p2p_fsk_bitrate(self):
        response, ok = check_success(self, "AT+PBR=?")
        if ok:
            return response

    def set_p2p_fsk_bitrate(self, bitrate: int):
        if not 600 <= bitrate <= 300000:
            logging.warning("Bitrate must be between 600 and 300000")
            return None
        response, ok = check_success(self, f"AT+PBR={bitrate}")
        if ok:
            return response

    def get_p2p_freq_deviation(self):
        response, ok = check_success(self, "AT+PFDEV=?")
        if ok:
            return response

    def set_p2p_freq_deviation(self, deviation: int):
        if not 600 <= deviation <= 200000:
            logging.warning("Frequency deviation must be between 600 and 200000")
            return None
        response, ok = check_success(self, f"AT+PFDEV={deviation}")
        if ok:
            return response

    def p2p_send(self, payload: str):
        if (
            all(char in string.hexdigits for char in payload)
            and 2 <= len(payload) <= 500
            and len(payload) % 2 == 0
        ):
            response, ok = check_success(self, f"AT+PSEND={payload}")
            if ok:
                return response
        logging.warning(
            "Payload must be an even number of hexadecimal characters between 2 and 500"
        )

    def get_p2p_channel_activity(self):
        response, ok = check_success(self, "AT+CAD=?")
        if ok:
            return response

    def set_p2p_channel_activity(self, on: bool):
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+CAD={mode}")
        if ok:
            return response

    def p2p_receive(self, timeout: int):
        if not 1 <= timeout <= 65535:
            logging.warning("Timeout must be between 1 and 65535 milliseconds")
            return None
        response, ok = check_success(self, f"AT+PRECV={timeout}")
        if ok:
            return response

    def get_p2p_encryption(self):
        response, ok = check_success(self, "AT+ENCRY=?")
        if ok:
            return response

    def set_p2p_encryption(self, on: bool):
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+ENCRY={mode}")
        if ok:
            return response

    def get_p2p_encryption_key(self):
        response, ok = check_success(self, "AT+ENCKEY=?")
        if ok:
            return response

    def set_p2p_encryption_key(self, key: str):
        if all(char in string.hexdigits for char in key) and len(key) == 32:
            response, ok = check_success(self, f"AT+ENCKEY={key}")
            if ok:
                return response
        logging.warning("Encrytion key must be exactly 32 hexadecimal characters")

    def get_p2p_crypt_status(self):
        response, ok = check_success(self, "AT+PCRYPT=?")
        if ok:
            return response

    def set_p2p_crypt_status(self, on: bool):
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+PCRYPT={mode}")
        if ok:
            return response

    def get_p2p_crypt_decrypt_key(self):
        response, ok = check_success(self, "AT+PKEY=?")
        if ok:
            return response

    def set_p2p_crypt_decrypt_key(self, key: str):
        if all(char in string.hexdigits for char in key) and len(key) == 16:
            response, ok = check_success(self, f"AT+PKEY={key}")
            if ok:
                return response
        logging.warning("Key must be exactly 16 hexadecimal characters")

    def get_p2p_crypt_iv(self):
        response, ok = check_success(self, "AT+CRYPIV=?")
        if ok:
            return response

    def set_p2p_crypt_iv(self, key: str):
        if all(char in string.hexdigits for char in key) and len(key) == 32:
            response, ok = check_success(self, f"AT+CRYPIV={key}")
            if ok:
                return response
        logging.warning("CryptIV key must be exactly 32 hexadecimal characters")

    def get_p2p_params(self):
        response, ok = check_success(self, "AT+P2P=?")
        if ok:
            return response

    def set_p2p_params(
        self,
        freq: int = 868000000,
        sf: int = 7,
        bandwidth: int = 125,
        code_rate: int = 0,
        preamble_len: int = 8,
        tx_power: int = 14,
    ):
        if not 150000000 <= freq <= 960000000:
            logging.warning("Frequency must be between 150 MHz and 960 MHz")
            return None
        if not 6 <= sf <= 12:
            logging.warning("Spreading factor must be between 6 and 12")
            return None
        if not 0 <= bandwidth <= 9:
            logging.warning("Bandwidth must be between 0 and 9")
            return None
        if code_rate not in (0, 1, 2, 3):
            logging.warning("Code rate must be either 0, 1, 2 or 3")
            return None
        if not 2 <= preamble_len <= 65535:
            logging.warning("Preamble length must be between 2 and 65535")
            return None
        if not 5 <= tx_power <= 22:
            logging.warning("TX Power must be between 5 and 22")
            return None

        response, ok = check_success(
            self,
            f"AT+P2P={freq}:{sf}:{bandwidth}:{code_rate}:{preamble_len}:{tx_power}",
        )
        if ok:
            return response

    def get_p2p_iq_inv(self):
        response, ok = check_success(self, "AT+IQINVER=?")
        if ok:
            return response

    def set_p2p_iq_inv(self, on: bool):
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+IQINVER={mode}")
        if ok:
            return response

    def get_p2p_syncword(self):
        response, ok = check_success(self, "AT+SYNCWORD=?")
        if ok:
            return response

    def set_p2p_syncword(self, word: str):
        if all(char in string.hexdigits for char in word) and len(word) == 4:
            response, ok = check_success(self, f"AT+SYNCWORD={word}")
            if ok:
                return response
        else:
            logging.warning("Syncword must be exactly 4 hexadecimal characters")
            return None

    def get_p2p_rf_freq(self):
        response, ok = check_success(self, "AT+RFFREQUENCY=?")
        if ok:
            return response

    def set_p2p_rf_freq(self, freq: int):
        response, ok = check_success(self, f"AT+RFFREQUENCY={freq}")
        if ok:
            return response

    def get_p2p_tx_out_power(self):
        response, ok = check_success(self, "AT+TXOUTPUTPOWER=?")
        if ok:
            return response

    def set_p2p_tx_out_power(self, tx_out: int):
        if not 5 <= tx_out <= 22:
            logging.warning("TX out power must be between 5 and 22")
            return None
        response, ok = check_success(self, f"AT+TXOUTPUTPOWER={tx_out}")
        if ok:
            return response

    def get_p2p_bandwidth(self):
        response, ok = check_success(self, "AT+BANDWIDTH=?")
        if ok:
            return response

    def set_p2p_bandwidth(self, band: int):
        if not 0 <= band <= 9:
            logging.warning("Bandwidth must be between 0 and 9")
            return None
        response, ok = check_success(self, f"AT+basicConfig={band}")
        if ok:
            return response

    def get_p2p_spread_factor(self):
        response, ok = check_success(self, "AT+SPREADINGFACTOR=?")
        if ok:
            return response

    def set_p2p_spread_factor(self, sf: int):
        if not 5 <= sf <= 12:
            logging.warning("Spreading Facotr must be between 5 and 12")
            return None
        response, ok = check_success(self, f"AT+SPREADINGFACTOR={sf}")
        if ok:
            return response

    def get_p2p_coding_rate(self):
        response, ok = check_success(self, "AT+CODINGRATE=?")
        if ok:
            return response

    def set_p2p_coding_rate(self, code_rate: int):
        if code_rate not in (0, 1, 2, 3):
            logging.warning("Coding rate must be either 0, 1, 2 or 3")
            return None
        response, ok = check_success(self, f"AT+CODINGRATE={code_rate}")
        if ok:
            return response

    def get_p2p_preamble_length_2(self):
        response, ok = check_success(self, "AT+PREAMBLELENGTH=?")
        if ok:
            return response

    def set_p2p_preamble_length_2(self, preamble_len: int):
        if 5 <= preamble_len <= 65535:
            logging.warning("Preamble length must be between 5 and 65535")
            return None
        response, ok = check_success(self, f"AT+PREAMBLELENGTH={preamble_len}")
        if ok:
            return response

    def get_p2p_symbol_timeout(self):
        response, ok = check_success(self, "AT+SYMBOLTIMEOUT=?")
        if ok:
            return response

    def set_p2p_symbol_timeout(self, timeout: int):
        if not 0 <= timeout <= 248:
            logging.warning("Symbol timeout must be between 0 and 248")
            return None
        response, ok = check_success(self, f"AT+SYMBOLTIMEOUT={timeout}")
        if ok:
            return response

    def get_p2p_fixed_length_payload(self):
        response, ok = check_success(self, "AT+FIXEDLENGTHPAYLOAD=?")
        if ok:
            return response

    def set_p2p_fixed_length_payload(self, on: bool):
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+FIXEDLENGTHPAYLOAD={mode}")
        if ok:
            return response

    # RF TEST

    def rf_rssi_test(self):
        response, ok = check_success(self, "AT+TRSSI=?")
        if ok:
            return response

    def rf_tone_test(self):
        response, ok = check_success(self, "AT+TTONE")
        if ok:
            return response

    def set_rf_tx_test_packet_number(self, number: int):
        response, ok = check_success(self, f"AT+TTX={number}")
        if ok:
            return response

    def set_rf_rx_test_packet_number(self, number: int):
        response, ok = check_success(self, f"AT+TRX={number}")
        if ok:
            return response
