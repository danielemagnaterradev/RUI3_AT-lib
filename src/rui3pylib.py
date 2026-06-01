"""
rui3pylib — Python wrapper for the RUI3 AT command set.

Wraps every AT command defined in the official RAKwireless RUI3 AT Command
Manual (https://docs.rakwireless.com/…/rui3/at-command-manual/) as a method
of the RUI3Node class, which extends serial.Serial.

Dependencies:
    pyserial >= 3.5

Threading model:
    All methods are **blocking**. Do not share a single RUI3Node instance
    across threads without external locking.

Hex key conventions:
    All key/EUI/address parameters must be supplied as plain ASCII hex strings
    (e.g. "1122334455667788"), MSB first, matching the RUI3 documentation.
    No colons, spaces, or 0x prefixes unless otherwise stated.
"""

import logging
import serial
import string
import time
from serial.tools.list_ports import comports

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Maximum seconds to keep draining the receive buffer after the initial wait.
_READ_DRAIN_TIMEOUT = 5.0


def _status(ok: bool) -> str:
    return "OK" if ok else "FAILED"


def send_command(port: serial.Serial, cmd: str, wait: float = 3.0) -> str:
    """Send *cmd* over *port* and return the full response string.

    After the initial *wait* seconds the function drains the input buffer until
    no new bytes arrive for 0.1 s, or until _READ_DRAIN_TIMEOUT seconds have
    elapsed in total (whichever comes first), preventing an infinite loop on
    devices that emit continuous debug output.
    """
    port.reset_input_buffer()
    full_cmd = cmd.strip() + "\r\n"
    port.write(full_cmd.encode(errors="replace"))
    time.sleep(wait)

    response = ""
    deadline = time.monotonic() + _READ_DRAIN_TIMEOUT
    while port.in_waiting and time.monotonic() < deadline:
        response += port.read(port.in_waiting).decode(errors="replace")
        time.sleep(0.1)

    # Filter out firmware debug lines (e.g. "[APP] …")
    response = "\n".join(
        line for line in response.splitlines() if not line.startswith("[APP]")
    )
    return response


def check_success(port: serial.Serial, cmd: str, wait: float = 3.0) -> tuple[str, bool]:
    """Send *cmd*, log the outcome, and return (response, ok).

    *ok* is True when the response contains the final status line "OK".
    Only the standalone "OK" status token is matched — it is identified as a
    line that equals "OK" exactly, so payload data that happens to contain the
    letters "OK" does not produce a false positive and is not stripped from the
    logged output.
    """
    response = send_command(port, cmd, wait)
    # Check for the status token as a standalone line, not as a substring,
    # to avoid false positives on payload data that contains "OK".
    lines = response.splitlines()
    ok = any(line.strip() == "OK" for line in lines)
    # Build a clean version for logging by removing only the bare "OK" status line.
    clean_lines = [line for line in lines if line.strip() != "OK"]
    clean = "\n".join(clean_lines).strip()
    logging.info(f"[{_status(ok)}] {cmd}" + (f" -> {clean}" if clean else ""))
    return response, ok


class RUI3Node(serial.Serial):
    """RUI3 AT command wrapper.

    Extends serial.Serial so that the underlying port can be used directly
    when needed.  All AT commands are exposed as methods.

    Args:
        port:     Serial device path (e.g. ``"/dev/ttyUSB0"`` or ``"COM3"``).
                  If *None* (default) the constructor scans all available
                  ports and connects to the first RUI3-compatible device.
        baudrate: Serial baud rate.  Default is 115200 (RUI3 factory default).
        timeout:  Read timeout in seconds passed to serial.Serial.
    """

    def __init__(
        self,
        port: str | None = None,
        baudrate: int = 115200,
        timeout: float = 3.0,
    ) -> None:
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        if port is None:
            # Scan available ports; stop as soon as one responds to "AT".
            for interface in comports():
                try:
                    self.port = interface.device
                    self.open()
                    if self.try_connect():
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
                if self.try_connect():
                    logging.info(f"Connected to port {self.port}")
                else:
                    self.close()
            except serial.serialutil.SerialException as e:
                logging.info(f"SerialException on {self.port}: {e}")
                if self.is_open:
                    self.close()

    def try_connect(self) -> bool:
        """Send a bare AT and return True if the device responds with OK."""
        try:
            _, ok = check_success(self, "AT", 5.0)
            return ok
        except serial.serialutil.PortNotOpenError:
            logging.info("Port not open")
            return False

    # GENERAL COMMANDS

    def ping(self) -> str | None:
        """AT — check that communication is working (returns OK)."""
        response, ok = check_success(self, "AT")
        if ok:
            return response

    def at_help(self) -> str | None:
        """AT? — print a short help listing for all supported commands."""
        response, ok = check_success(self, "AT?")
        if ok:
            return response

    def toggle_command_echo(self) -> str | None:
        """ATE — toggle the AT command echo on the serial terminal.

        Each call inverts the current echo state.  The state is not readable
        via any AT command; the caller must track it externally if needed.
        """
        response, ok = check_success(self, "ATE")
        if ok:
            return response

    def reset(self) -> None:
        """ATZ — reset the module immediately.

        The module resets without returning an OK code, so send_command is
        used directly.  All volatile settings are lost; persistent settings
        (flash) are retained.
        """
        send_command(self, "ATZ")
        logging.info("Module reset")

    def restore_default(self) -> str | None:
        """ATR — restore all parameters to factory default values."""
        response, ok = check_success(self, "ATR")
        if ok:
            logging.info("Restored default values")
            return response

    def get_serial_number(self) -> str | None:
        """AT+SN=? — return the device serial number."""
        response, ok = check_success(self, "AT+SN=?")
        if ok:
            return response

    def get_battery_level(self) -> str | None:
        """AT+BAT=? — return the current battery voltage in mV."""
        response, ok = check_success(self, "AT+BAT=?")
        if ok:
            return response

    def get_build_time(self) -> str | None:
        """AT+BUILDTIME=? — return the firmware build timestamp."""
        response, ok = check_success(self, "AT+BUILDTIME=?")
        if ok:
            return response

    def get_repo_info(self) -> str | None:
        """AT+REPOINFO=? — return the firmware repository commit information."""
        response, ok = check_success(self, "AT+REPOINFO=?")
        if ok:
            return response

    def get_firm_version(self) -> str | None:
        """AT+VER=? — return the RUI3 firmware version string."""
        response, ok = check_success(self, "AT+VER=?")
        if ok:
            return response

    def get_at_version(self) -> str | None:
        """AT+CLIVER=? — return the AT command set version string."""
        response, ok = check_success(self, "AT+CLIVER=?")
        if ok:
            return response

    def get_api_version(self) -> str | None:
        """AT+APIVER=? — return the RUI3 API version string."""
        response, ok = check_success(self, "AT+APIVER=?")
        if ok:
            return response

    def get_hw_model(self) -> str | None:
        """AT+HWMODEL=? — return the hardware model identifier string."""
        response, ok = check_success(self, "AT+HWMODEL=?")
        if ok:
            return response

    def get_hw_id(self) -> str | None:
        """AT+HWID=? — return the hardware chip ID."""
        response, ok = check_success(self, "AT+HWID=?")
        if ok:
            return response

    def get_device_alias(self) -> str | None:
        """AT+ALIAS=? — return the user-defined device alias (1-16 characters)."""
        response, ok = check_success(self, "AT+ALIAS=?")
        if ok:
            return response

    def set_device_alias(self, alias: str) -> str | None:
        """AT+ALIAS=<alias> — set a user-defined device alias.

        *alias* must be between 1 and 16 characters.  The alias is stored in
        flash and survives resets.
        """
        if not 1 <= len(alias) <= 16:
            logging.warning("Alias must be between 1 and 16 characters")
            return None
        response, ok = check_success(self, f"AT+ALIAS={alias}")
        if ok:
            return response

    def get_system_voltage(self) -> str | None:
        """AT+SYSV=? — return the current system supply voltage in mV."""
        response, ok = check_success(self, "AT+SYSV=?")
        if ok:
            return response

    def get_ble_mac(self) -> str | None:
        """AT+BLEMAC=? — return the BLE MAC address in colon-separated hex format."""
        response, ok = check_success(self, "AT+BLEMAC=?")
        if ok:
            return response

    def set_ble_mac(self, mac: str) -> str | None:
        """AT+BLEMAC=<mac> — set the BLE MAC address.

        *mac* must be exactly 12 hexadecimal characters without separators
        (e.g. "001122334455").  The library converts it to the colon-separated
        format required by the firmware (e.g. "00:11:22:33:44:55").
        """
        if all(char in string.hexdigits for char in mac) and len(mac) == 12:
            formatted = ":".join(mac[i : i + 2] for i in range(0, 12, 2))
            response, ok = check_success(self, f"AT+BLEMAC={formatted.lower()}")
            if ok:
                return response
        else:
            logging.warning("Invalid format: it should be like 001122334455")
            return None

    def get_boot_ver(self) -> str | None:
        """AT+BOOTVER=? — return the bootloader version (normal mode).

        This command is available in normal operating mode.  For the equivalent
        command in boot mode, use get_bootloader_ver().
        """
        response, ok = check_success(self, "AT+BOOTVER=?")
        if ok:
            return response

    # LOW POWER COMMANDS

    def at_sleep(self, duration_ms: int) -> str | None:
        """AT+SLEEP=<ms> — enter sleep mode for *duration_ms* milliseconds.

        Valid range: 1 ~ (2^32 - 1) ms.  The AT+SLEEP command with no parameter
        (indefinite sleep) is not exposed here; use set_low_power_mode(True)
        for persistent low-power mode instead.
        """
        if duration_ms < 1:
            logging.warning("Sleep duration must be at least 1 ms")
            return None
        response, ok = check_success(self, f"AT+SLEEP={duration_ms}")
        if ok:
            return response

    def get_low_power_mode(self) -> str | None:
        """AT+LPM=? — return the current low-power mode state (0 = off, 1 = on)."""
        response, ok = check_success(self, "AT+LPM=?")
        if ok:
            return response

    def set_low_power_mode(self, on: bool) -> str | None:
        """AT+LPM=<mode> — enable (True) or disable (False) low-power mode.

        When enabled, the module enters sleep between AT commands to reduce
        current consumption.
        """
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+LPM={mode}")
        if ok:
            return response

    def get_low_power_mode_level(self) -> str | None:
        """AT+LPMLVL=? — return the low-power sleep level (RAK3172 only).

        Only effective on RAK3172; has no effect on other modules.
        Returns 1 (STOP1) or 2 (STOP2).
        """
        response, ok = check_success(self, "AT+LPMLVL=?")
        if ok:
            return response

    def set_low_power_mode_level(self, level: int) -> str | None:
        """AT+LPMLVL=<level> — set the low-power sleep level (RAK3172 only).

        Only effective on RAK3172; has no effect on other modules.

        level 1 — STOP1 mode: wakeup via both UART1 and UART2.
        level 2 — STOP2 mode: more power-efficient; wakeup via UART2 only.
        """
        if level not in (1, 2):
            logging.warning("Level must be either 1 (STOP1) or 2 (STOP2)")
            return None
        response, ok = check_success(self, f"AT+LPMLVL={level}")
        if ok:
            return response

    # SERIAL AT COMMANDS

    def lock_serial(self) -> None:
        """AT+LOCK — lock the serial port until the correct password is entered.

        The default password is "00000000" and can be changed with
        set_password().  AT+LOCK does not return OK; send_command is used
        directly.
        """
        _ = send_command(self, "AT+LOCK")
        logging.info(f"Serial port {self.port} is now locked")

    def set_password(self, password: str) -> str | None:
        """AT+PWORD=<password> — set the serial port locking password.

        *password* must be 1-8 printable ASCII characters.  The new password
        takes effect immediately and is stored in flash.
        """
        if not 1 <= len(password) <= 8:
            logging.warning("Password must be between 1 and 8 characters")
            return None
        if not password.isprintable():
            logging.warning("Password must contain only printable characters")
            return None
        response, ok = check_success(self, f"AT+PWORD={password}")
        if ok:
            return response

    def get_baud_rate(self) -> str | None:
        """AT+BAUD=? — return the current serial baud rate."""
        response, ok = check_success(self, "AT+BAUD=?")
        if ok:
            return response

    def set_baud_rate(self, baudrate: int) -> str | None:
        """AT+BAUD=<baudrate> — set the serial baud rate.

        The configured baud rate is stored in flash and persists across resets
        and power cycles.  The new rate takes effect after the next reset.
        """
        response, ok = check_success(self, f"AT+BAUD={baudrate}")
        if ok:
            return response

    def switch_to_at_mode(self) -> str | None:
        """AT+ATM — switch the module to AT command mode.

        Used when the module is running in a custom firmware mode; this
        command returns it to the standard AT command interface.
        """
        response, ok = check_success(self, "AT+ATM")
        if ok:
            return response

    # BOOTLOADER COMMANDS
    # All methods in this section except set_boot_mode() only work while
    # the device is in boot mode (entered via set_boot_mode()).

    def set_boot_mode(self) -> str:
        """AT+BOOT — enter bootloader mode for firmware upgrade.

        The device responds with "<BOOT MODE>" rather than "OK", so
        send_command is used directly.  To leave boot mode call at_run().
        AT_BUSY_ERROR is returned by the firmware if the bootloader process
        is already running.
        """
        response = send_command(self, "AT+BOOT")
        logging.info(f"Boot mode response: {response.strip()}")
        return response

    def get_bootloader_ver(self) -> str:
        """AT+VERSION — return the bootloader version string (boot mode only).

        This command is only available while the device is in boot mode
        (entered via set_boot_mode()).  The doc also accepts AT+VER=? in
        boot mode as an equivalent alias, but AT+VERSION is the canonical
        form and is used here.  Neither command returns an "OK" status token
        in boot mode, so send_command is used directly.
        """
        return send_command(self, "AT+VERSION")

    def get_bootloader_status(self) -> str:
        """AT+BOOTSTATUS — return the current bootloader status (boot mode only).

        Does not return an OK code; send_command is used directly.
        """
        return send_command(self, "AT+BOOTSTATUS")

    def at_run(self) -> str:
        """AT+RUN — exit bootloader mode and run the application firmware (boot mode only).

        Does not return an OK code; send_command is used directly.
        """
        return send_command(self, "AT+RUN")

    def boot_reset(self) -> str:
        """AT+RESET — reset the device from within bootloader mode (boot mode only).

        Does not return an OK code; send_command is used directly.
        """
        return send_command(self, "AT+RESET")

    def boot_update(self) -> str:
        """AT+UPDATE — start the Y-Modem firmware receive process (boot mode only).

        Initiates a Y-Modem transfer session on the serial port.  Send the
        firmware binary using a Y-Modem-compatible terminal after calling this
        method.  Does not return an OK code; send_command is used directly.
        """
        return send_command(self, "AT+UPDATE")

    # LORAWAN KEYS AND IDs
    # All key/EUI/address setters expect plain ASCII hex strings, MSB first,
    # with no colons, spaces, or 0x prefixes (see module docstring).

    def get_device_eui(self) -> str | None:
        """AT+DEVEUI=? — return the 8-byte device EUI as 16 hex characters."""
        response, ok = check_success(self, "AT+DEVEUI=?")
        if ok:
            return response

    def set_device_eui(self, deveui: str) -> str | None:
        """AT+DEVEUI=<deveui> — set the 8-byte device EUI.

        *deveui* must be exactly 16 hexadecimal characters (MSB first).
        """
        if all(char in string.hexdigits for char in deveui) and len(deveui) == 16:
            response, ok = check_success(self, f"AT+DEVEUI={deveui}")
            if ok:
                return response
        else:
            logging.warning("Device EUI must be exactly 16 hexdigits")
            return None

    def get_app_eui(self) -> str | None:
        """AT+APPEUI=? — return the 8-byte application EUI as 16 hex characters."""
        response, ok = check_success(self, "AT+APPEUI=?")
        if ok:
            return response

    def set_app_eui(self, appeui: str) -> str | None:
        """AT+APPEUI=<appeui> — set the 8-byte application EUI (JoinEUI in LoRaWAN 1.1).

        *appeui* must be exactly 16 hexadecimal characters (MSB first).
        """
        if all(char in string.hexdigits for char in appeui) and len(appeui) == 16:
            response, ok = check_success(self, f"AT+APPEUI={appeui}")
            if ok:
                return response
        else:
            logging.warning("App EUI must be exactly 16 hexdigits")
            return None

    def get_app_key(self) -> str | None:
        """AT+APPKEY=? — return the 16-byte application key as 32 hex characters (OTAA)."""
        response, ok = check_success(self, "AT+APPKEY=?")
        if ok:
            return response

    def set_app_key(self, appkey: str) -> str | None:
        """AT+APPKEY=<appkey> — set the 16-byte application key (OTAA).

        *appkey* must be exactly 32 hexadecimal characters (MSB first).
        """
        if all(char in string.hexdigits for char in appkey) and len(appkey) == 32:
            response, ok = check_success(self, f"AT+APPKEY={appkey}")
            if ok:
                return response
        else:
            logging.warning("App key must be exactly 32 hexdigits")
            return None

    def get_dev_addr(self) -> str | None:
        """AT+DEVADDR=? — return the 4-byte device address as 8 hex characters (ABP)."""
        response, ok = check_success(self, "AT+DEVADDR=?")
        if ok:
            return response

    def set_dev_addr(self, devaddr: str) -> str | None:
        """AT+DEVADDR=<devaddr> — set the 4-byte device address (ABP).

        *devaddr* must be exactly 8 hexadecimal characters (MSB first).
        """
        if all(char in string.hexdigits for char in devaddr) and len(devaddr) == 8:
            response, ok = check_success(self, f"AT+DEVADDR={devaddr}")
            if ok:
                return response
        else:
            logging.warning("Device address must be exactly 8 hexdigits")
            return None

    def get_app_s_key(self) -> str | None:
        """AT+APPSKEY=? — return the 16-byte application session key as 32 hex characters (ABP)."""
        response, ok = check_success(self, "AT+APPSKEY=?")
        if ok:
            return response

    def set_app_s_key(self, appskey: str) -> str | None:
        """AT+APPSKEY=<appskey> — set the 16-byte application session key (ABP).

        *appskey* must be exactly 32 hexadecimal characters (MSB first).
        """
        if all(char in string.hexdigits for char in appskey) and len(appskey) == 32:
            response, ok = check_success(self, f"AT+APPSKEY={appskey}")
            if ok:
                return response
        else:
            logging.warning("App security key must be exactly 32 hexdigits")
            return None

    def get_network_s_key(self) -> str | None:
        """AT+NWKSKEY=? — return the 16-byte network session key as 32 hex characters (ABP)."""
        response, ok = check_success(self, "AT+NWKSKEY=?")
        if ok:
            return response

    def set_network_s_key(self, netskey: str) -> str | None:
        """AT+NWKSKEY=<netskey> — set the 16-byte network session key (ABP).

        *netskey* must be exactly 32 hexadecimal characters (MSB first).
        """
        if all(char in string.hexdigits for char in netskey) and len(netskey) == 32:
            response, ok = check_success(self, f"AT+NWKSKEY={netskey}")
            if ok:
                return response
        else:
            logging.warning("Network security key must be exactly 32 hexdigits")
            return None

    def get_network_id(self) -> str | None:
        """AT+NETID=? — return the 3-byte network identifier as 6 hex characters."""
        response, ok = check_success(self, "AT+NETID=?")
        if ok:
            return response

    def set_network_id(self, netid: str) -> str | None:
        """AT+NETID=<netid> — set the 3-byte network identifier.

        *netid* must be exactly 6 hexadecimal characters (MSB first).
        """
        if all(char in string.hexdigits for char in netid) and len(netid) == 6:
            response, ok = check_success(self, f"AT+NETID={netid}")
            if ok:
                return response
        else:
            logging.warning("Network ID must be exactly 6 hexdigits")
            return None

    def get_multicast_root_key(self) -> str | None:
        """AT+MCROOTKEY=? — return the multicast root key (read-only).

        This key is read-only and derived internally by the firmware; there is
        no corresponding setter command in the RUI3 AT command set.
        """
        response, ok = check_success(self, "AT+MCROOTKEY=?")
        if ok:
            return response

    # LORAWAN JOINING AND SENDING

    def get_confirm_mode(self) -> str | None:
        """AT+CFM=? — return the current uplink confirmation mode (0 = unconfirmed, 1 = confirmed)."""
        response, ok = check_success(self, "AT+CFM=?")
        if ok:
            return response

    def set_confirm_mode(self, on: bool) -> str | None:
        """AT+CFM=<mode> — configure uplink payload as confirmed (True) or unconfirmed (False)."""
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+CFM={mode}")
        if ok:
            return response

    def get_confirm_status(self) -> str | None:
        """AT+CFS=? — return the confirmation status of the last AT+SEND uplink.

        Returns 0 if the last confirmed uplink was not acknowledged by the
        network server, or 1 if it was acknowledged.
        """
        response, ok = check_success(self, "AT+CFS=?")
        if ok:
            return response

    def get_join_params(self) -> str | None:
        """AT+JOIN=? — return the current join parameters in the format <join>:<auto>:<interval>:<attempts>."""
        response, ok = check_success(self, "AT+JOIN=?")
        if ok:
            return response

    def try_join(
        self,
        join: bool = True,
        auto_join: bool = False,
        interval: int = 8,
        join_attempts: int = 0,
    ) -> str | None:
        """AT+JOIN=<join>:<auto_join>:<interval>:<attempts> — start the LoRaWAN join procedure.

        This is an asynchronous command: OK means the join process has been
        initiated, not that it succeeded.  Use get_network_join_status() to
        poll for the result.

        Args:
            join:          True to start joining, False to stop an ongoing attempt.
            auto_join:     True to enable automatic re-join on network loss.
            interval:      Reattempt interval in seconds (7-255).
            join_attempts: Number of join attempts before giving up (0-255, 0 = unlimited).
        """
        join_bin = 1 if join else 0
        auto_join_bin = 1 if auto_join else 0
        if not 7 <= interval <= 255:
            logging.warning("Reattempt value must be within 7 and 255")
            return None
        if not 0 <= join_attempts <= 255:
            logging.warning("No. of join attempts must be between 0 and 255")
            return None
        response, ok = check_success(
            self,
            f"AT+JOIN={join_bin}:{auto_join_bin}:{interval}:{join_attempts}",
        )
        if ok:
            return response

    def get_network_join_mode(self) -> str | None:
        """AT+NJM=? — return the current network join mode (0 = ABP, 1 = OTAA)."""
        response, ok = check_success(self, "AT+NJM=?")
        if ok:
            return response

    def set_network_join_mode(self, mode: int = 0) -> str | None:
        """AT+NJM=<mode> — set the network join mode.

        mode 0 — ABP (Activation By Personalisation): uses pre-provisioned
                 session keys; no over-the-air join procedure required.
        mode 1 — OTAA (Over-The-Air Activation): performs a join exchange
                 with the network server to derive session keys.
        """
        if mode not in (0, 1):
            logging.warning("Parameter must be either 0 (ABP) or 1 (OTAA)")
            return None
        response, ok = check_success(self, f"AT+NJM={mode}")
        if ok:
            return response

    def get_network_join_status(self) -> str | None:
        """AT+NJS=? — return the current network join status (0 = not joined, 1 = joined)."""
        response, ok = check_success(self, "AT+NJS=?")
        if ok:
            return response

    def get_last_received_data(self) -> str | None:
        """AT+RECV=? — return the last received downlink payload.

        The response format is <port>:<payload_hex>.  Returns "0:" if no
        downlink has been received since the last time this command was called.
        """
        response, ok = check_success(self, "AT+RECV=?")
        if ok:
            return response

    def send_data(self, port: int, payload: str) -> str | None:
        """AT+SEND=<port>:<payload> — send a LoRaWAN uplink payload.

        Args:
            port:    LoRaWAN application port (1-233).
            payload: Hexadecimal payload string; must be an even number of hex
                     characters between 2 and 500 (i.e. 1 to 250 bytes).
        """
        if not 1 <= port <= 233:
            logging.warning("Port must be between 1 and 233")
            return None
        if not all(char in string.hexdigits for char in payload):
            logging.warning("Payload must only contain hexadecimal characters")
            return None
        if not 2 <= len(payload) <= 500 or len(payload) % 2 != 0:
            logging.warning("Payload length must be an even number between 2 and 500")
            return None
        response, ok = check_success(self, f"AT+SEND={port}:{payload}")
        if ok:
            return response

    def send_long_packet_data(self, port: int, ack: bool, payload: str) -> str | None:
        """AT+LPSEND=<port>:<ack>:<payload> — send a long uplink payload (up to 1000 bytes).

        This is an asynchronous command: OK means the send process has been
        initiated, not that it has completed.  Only supported for uplink packets
        and requires a WisGate Edge gateway.

        Args:
            port:    LoRaWAN application port (1-233).
            ack:     True to request a confirmed uplink (ACK), False otherwise.
            payload: Hexadecimal payload string; must be an even number of hex
                     characters between 2 and 2000 (i.e. 1 to 1000 bytes).
        """
        ack_bool = 1 if ack else 0
        if not 1 <= port <= 233:
            logging.warning("Port must be between 1 and 233")
            return None
        if not all(char in string.hexdigits for char in payload):
            logging.warning("Payload must only contain hexadecimal characters")
            return None
        if not 2 <= len(payload) <= 2000 or len(payload) % 2 != 0:
            logging.warning("Payload length must be an even number between 2 and 2000")
            return None
        response, ok = check_success(self, f"AT+LPSEND={port}:{ack_bool}:{payload}")
        if ok:
            return response

    def get_confirm_packet_retransmission(self) -> str | None:
        """AT+RETY=? — return the number of retransmissions for confirmed uplinks (0-7)."""
        response, ok = check_success(self, "AT+RETY=?")
        if ok:
            return response

    def set_confirm_packet_retransmission(self, tries: int) -> str | None:
        """AT+RETY=<tries> — set the number of retransmissions for confirmed uplinks.

        *tries* must be between 0 and 7.  A value of 0 means no retransmissions
        (the packet is sent exactly once).
        """
        if not 0 <= tries <= 7:
            logging.warning("Invalid number: must be within 0 and 7")
            return None
        response, ok = check_success(self, f"AT+RETY={tries}")
        if ok:
            return response

    # LORAWAN NETWORK MANAGEMENT

    def get_adaptive_rate(self) -> str | None:
        """AT+ADR=? — return the adaptive data rate state (0 = disabled, 1 = enabled)."""
        response, ok = check_success(self, "AT+ADR=?")
        if ok:
            return response

    def set_adaptive_rate(self, on: bool) -> str | None:
        """AT+ADR=<mode> — enable (True) or disable (False) adaptive data rate (ADR).

        When enabled, the network server controls the data rate and TX power
        to optimise range and airtime.  Disable only for mobile nodes.
        """
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+ADR={mode}")
        if ok:
            return response

    def get_lorawan_class(self) -> str | None:
        """AT+CLASS=? — return the current LoRaWAN device class (A, B, or C)."""
        response, ok = check_success(self, "AT+CLASS=?")
        if ok:
            return response

    def set_lorawan_class(self, lorawan_class: str) -> str | None:
        """AT+CLASS=<class> — set the LoRaWAN device class.

        lorawan_class — "A" (default, lowest power), "B" (beacon-scheduled
        downlinks), or "C" (continuous receive, highest power).
        """
        if lorawan_class.upper() not in ("A", "B", "C"):
            logging.warning("LoRaWAN class must be either A, B or C")
            return None
        response, ok = check_success(self, f"AT+CLASS={lorawan_class.upper()}")
        if ok:
            return response

    def get_duty_cycle(self) -> str | None:
        """AT+DCS=? — return the duty cycle enforcement state (0 = disabled, 1 = enabled)."""
        response, ok = check_success(self, "AT+DCS=?")
        if ok:
            return response

    def set_duty_cycle(self, on: bool) -> str | None:
        """AT+DCS=<mode> — enable (True) or disable (False) duty cycle enforcement.

        Duty cycle enforcement is mandatory in some regions (e.g. EU868).
        Disable only when regulatory compliance is guaranteed by other means.
        """
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+DCS={mode}")
        if ok:
            return response

    def get_data_rate(self) -> str | None:
        """AT+DR=? — return the current uplink data rate index."""
        response, ok = check_success(self, "AT+DR=?")
        if ok:
            return response

    def set_data_rate(self, data_rate: int) -> str | None:
        """AT+DR=<dr> — set the uplink data rate index.

        Valid range: 0-7.  The exact mapping of index to spreading factor and
        bandwidth is region-dependent (e.g. DR0 = SF12/BW125 in EU868).
        This setting is ignored when ADR is enabled.
        """
        if not 0 <= data_rate <= 7:
            logging.warning("Data rate must be between 0 and 7")
            return None
        response, ok = check_success(self, f"AT+DR={data_rate}")
        if ok:
            return response

    def get_join_delay_rx_window_1(self) -> str | None:
        """AT+JN1DL=? — return the join accept delay for RX window 1 in seconds (1-14)."""
        response, ok = check_success(self, "AT+JN1DL=?")
        if ok:
            return response

    def set_join_delay_rx_window_1(self, value: int) -> str | None:
        """AT+JN1DL=<value> — set the join accept delay for RX window 1.

        *value* is in seconds; valid range is 1-14.  Must be strictly less
        than the value set for RX window 2 (AT+JN2DL).
        """
        if not 1 <= value <= 14:
            logging.warning("Value must be within 1 and 14")
            return None
        response, ok = check_success(self, f"AT+JN1DL={value}")
        if ok:
            return response

    def get_join_delay_rx_window_2(self) -> str | None:
        """AT+JN2DL=? — return the join accept delay for RX window 2 in seconds (2-15)."""
        response, ok = check_success(self, "AT+JN2DL=?")
        if ok:
            return response

    def set_join_delay_rx_window_2(self, value: int) -> str | None:
        """AT+JN2DL=<value> — set the join accept delay for RX window 2.

        *value* is in seconds; valid range is 2-15.  Must be strictly greater
        than the value set for RX window 1 (AT+JN1DL).
        """
        if not 2 <= value <= 15:
            logging.warning("Value must be within 2 and 15")
            return None
        response, ok = check_success(self, f"AT+JN2DL={value}")
        if ok:
            return response

    def get_public_network_mode(self) -> str | None:
        """AT+PNM=? — return the public/private network mode (0 = private, 1 = public)."""
        response, ok = check_success(self, "AT+PNM=?")
        if ok:
            return response

    def set_public_network_mode(self, on: bool) -> str | None:
        """AT+PNM=<mode> — set public (True) or private (False) network mode.

        This controls the LoRa sync word: 0x34 for public networks (LoRaWAN),
        0x12 for private networks.  Must match the gateway configuration.
        """
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+PNM={mode}")
        if ok:
            return response

    def get_receive_window_1_delay(self) -> str | None:
        """AT+RX1DL=? — return the RX1 receive window delay in seconds (1-15)."""
        response, ok = check_success(self, "AT+RX1DL=?")
        if ok:
            return response

    def set_receive_window_1_delay(self, value: int) -> str | None:
        """AT+RX1DL=<value> — set the RX1 receive window delay.

        *value* is in seconds; valid range is 1-15.  This is the delay from
        the end of the uplink transmission to the opening of the first
        downlink receive window.
        """
        if not 1 <= value <= 15:
            logging.warning("Value must be between 1 and 15")
            return None
        response, ok = check_success(self, f"AT+RX1DL={value}")
        if ok:
            return response

    def get_receive_window_2_delay(self) -> str | None:
        """AT+RX2DL=? — return the RX2 receive window delay in seconds (2-15)."""
        response, ok = check_success(self, "AT+RX2DL=?")
        if ok:
            return response

    def set_receive_window_2_delay(self, value: int) -> str | None:
        """AT+RX2DL=<value> — set the RX2 receive window delay.

        *value* is in seconds; valid range is 2-15.  RX2 opens one second
        after RX1 by default; this value must be greater than RX1DL.
        """
        if not 2 <= value <= 15:
            logging.warning("Value must be between 2 and 15")
            return None
        response, ok = check_success(self, f"AT+RX2DL={value}")
        if ok:
            return response

    def get_receive_window_2_data_rate(self) -> str | None:
        """AT+RX2DR=? — return the RX2 receive window data rate index."""
        response, ok = check_success(self, "AT+RX2DR=?")
        if ok:
            return response

    def set_receive_window_2_data_rate(self, value: int) -> str | None:
        """AT+RX2DR=<value> — set the RX2 receive window data rate index.

        Accepted values per region:
            EU433 / RU864 / IN865 / EU868 / CN470 / KR920 — 0-5.
            AS923 — 2-5.
            US915 / AU915 / LA915 — 8-13.
        The firmware accepts the full ranges [0-7] and [8-13]; the caller is
        responsible for passing a value legal for the active region.
        """
        if not (0 <= value <= 7 or 8 <= value <= 13):
            logging.warning(
                "RX2 data rate must be in range 0-7 (EU/AS/KR/CN) "
                "or 8-13 (US915/AU915/LA915)"
            )
            return None
        response, ok = check_success(self, f"AT+RX2DR={value}")
        if ok:
            return response

    def get_receive_window_2_freq(self) -> str | None:
        """AT+RX2FQ=? — return the RX2 receive window frequency in Hz."""
        response, ok = check_success(self, "AT+RX2FQ=?")
        if ok:
            return response

    def set_receive_window_2_freq(self, freq: int) -> str | None:
        """AT+RX2FQ=<freq> — set the RX2 receive window frequency in Hz.

        The default value is region-dependent (e.g. 869525000 Hz for EU868).
        Changing this must match the network server configuration.
        """
        response, ok = check_success(self, f"AT+RX2FQ={freq}")
        if ok:
            return response

    def get_transmit_power(self) -> str | None:
        """AT+TXP=? — return the current uplink TX power index (0 = maximum for region)."""
        response, ok = check_success(self, "AT+TXP=?")
        if ok:
            return response

    def set_transmit_power(self, value: int) -> str | None:
        """AT+TXP=<value> — set the uplink TX power index.

        Index 0 corresponds to the maximum legal power for the active region.
        Valid upper bounds by region:
            EU433 — 0-5  |  EU868 / CN470 / KR920 / AS923 / RU864 — 0-7
            IN865 — 0-10 |  US915 / AU915 — 0-14
        """
        if not 0 <= value <= 14:
            logging.warning("Value must be between 0 and 14")
            return None
        response, ok = check_success(self, f"AT+TXP={value}")
        if ok:
            return response

    def get_link_check(self) -> str | None:
        """AT+LINKCHECK=? — return the current link check mode (0, 1, or 2)."""
        response, ok = check_success(self, "AT+LINKCHECK=?")
        if ok:
            return response

    def set_link_check(self, value: int) -> str | None:
        """AT+LINKCHECK=<value> — configure the LoRaWAN link check mechanism.

        value 0 — disable link check.
        value 1 — execute a single link check on the next uplink only.
        value 2 — execute a link check automatically after every uplink.
        """
        if value not in (0, 1, 2):
            logging.warning("Value must be either 0, 1 or 2")
            return None
        response, ok = check_success(self, f"AT+LINKCHECK={value}")
        if ok:
            return response

    def get_listen_before_talk(self) -> str | None:
        """AT+LBT=? — return the listen-before-talk state (0 = disabled, 1 = enabled)."""
        response, ok = check_success(self, "AT+LBT=?")
        if ok:
            return response

    def set_listen_before_talk(self, on: bool) -> str | None:
        """AT+LBT=<mode> — enable (True) or disable (False) listen-before-talk (LBT).

        LBT performs a channel scan before each transmission and aborts if the
        channel is occupied.  Required for regulatory compliance in some regions
        (e.g. AS923 in Japan).
        """
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+LBT={mode}")
        if ok:
            return response

    def get_listen_before_talk_rssi(self) -> str | None:
        """AT+LBTRSSI=? — return the LBT RSSI threshold in dBm."""
        response, ok = check_success(self, "AT+LBTRSSI=?")
        if ok:
            return response

    def set_listen_before_talk_rssi(self, value: int) -> str | None:
        """AT+LBTRSSI=<value> — set the LBT RSSI threshold in dBm.

        If the measured channel RSSI is below *value*, the channel is
        considered free and the transmission proceeds.  Typical values
        are in the range -80 to -100 dBm.
        """
        response, ok = check_success(self, f"AT+LBTRSSI={value}")
        if ok:
            return response

    def get_listen_before_talk_scan_time(self) -> str | None:
        """AT+LBTSCANTIME=? — return the LBT channel scan duration in milliseconds."""
        response, ok = check_success(self, "AT+LBTSCANTIME=?")
        if ok:
            return response

    def set_listen_before_talk_scan_time(self, value: int) -> str | None:
        """AT+LBTSCANTIME=<value> — set the LBT channel scan duration in milliseconds.

        The radio listens for *value* milliseconds before each transmission.
        If energy is detected above the RSSI threshold, the TX is deferred.
        """
        response, ok = check_success(self, f"AT+LBTSCANTIME={value}")
        if ok:
            return response

    def get_time_req(self) -> str | None:
        """AT+TIMEREQ=? — return the DeviceTimeReq state (0 = disabled, 1 = enabled)."""
        response, ok = check_success(self, "AT+TIMEREQ=?")
        if ok:
            return response

    def set_time_req(self, on: bool) -> str | None:
        """AT+TIMEREQ=<mode> — enable (True) or disable (False) time synchronisation requests.

        When enabled, the module sends a DeviceTimeReq MAC command on the next
        uplink to synchronise its internal clock with the network server.
        Use get_local_time() to read the resulting timestamp.
        """
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+TIMEREQ={mode}")
        if ok:
            return response

    def get_local_time(self) -> str | None:
        """AT+LTIME=? — return the current local time after network synchronisation.

        The time is expressed in UTC and is only valid after a successful
        DeviceTimeReq exchange (see set_time_req()).
        """
        response, ok = check_success(self, "AT+LTIME=?")
        if ok:
            return response

    # CLASS B MODE
    # The following commands are only meaningful when the device is operating
    # in LoRaWAN Class B mode (set via set_lorawan_class("B")).

    def get_periodicity(self) -> str | None:
        """AT+PGSLOT=? — return the Class B ping slot periodicity index (0-7)."""
        response, ok = check_success(self, "AT+PGSLOT=?")
        if ok:
            return response

    def set_periodicity(self, value: int) -> str | None:
        """AT+PGSLOT=<value> — set the Class B ping slot periodicity.

        The ping interval in seconds is 2^value:
            0=1 s, 1=2 s, 2=4 s, 3=8 s, 4=16 s, 5=32 s, 6=64 s, 7=128 s.
        Valid range: 0-7.
        """
        if not 0 <= value <= 7:
            logging.warning("Value must be between 0 and 7")
            return None
        response, ok = check_success(self, f"AT+PGSLOT={value}")
        if ok:
            return response

    def get_beacon_freq(self) -> str | None:
        """AT+BFREQ=? — return the Class B beacon broadcast frequency in Hz (read-only)."""
        response, ok = check_success(self, "AT+BFREQ=?")
        if ok:
            return response

    def get_beacon_time(self) -> str | None:
        """AT+BTIME=? — return the Class B beacon timestamp (read-only).

        The timestamp reflects the time of the last successfully received
        beacon and is expressed in GPS epoch seconds.
        """
        response, ok = check_success(self, "AT+BTIME=?")
        if ok:
            return response

    def get_gw_info(self) -> str | None:
        """AT+BGW=? — return the Class B gateway information from the last beacon (read-only).

        The response contains the network identifier and gateway coordinates
        as broadcast in the beacon frame.
        """
        response, ok = check_success(self, "AT+BGW=?")
        if ok:
            return response

    # LORAWAN INFORMATION

    def get_rssi(self) -> str | None:
        """AT+RSSI=? — return the RSSI of the last received downlink in dBm."""
        response, ok = check_success(self, "AT+RSSI=?")
        if ok:
            return response

    def get_all_channel_rssi(self) -> str | None:
        """AT+ARSSI=? — return the RSSI measured on all available channels.

        Returns a comma-separated list of <frequency>:<RSSI> pairs for each
        channel in the current channel plan.
        """
        response, ok = check_success(self, "AT+ARSSI=?")
        if ok:
            return response

    def get_signal_to_noise_ratio(self) -> str | None:
        """AT+SNR=? — return the SNR of the last received downlink in dB."""
        response, ok = check_success(self, "AT+SNR=?")
        if ok:
            return response

    # LORAWAN REGIONAL COMMANDS
    # These commands are region-specific and govern channel plans and
    # regulatory compliance.  The caller is responsible for passing values
    # that are legal for the target region and deployment.

    def get_mask(self) -> str | None:
        """AT+MASK=? — return the current 16-bit channel mask as a 4-character hex string.

        Only applicable to US915, AU915, CN470, and LA915 regions.
        """
        response, ok = check_success(self, "AT+MASK=?")
        if ok:
            return response

    def set_mask(self, mask: str) -> str | None:
        """AT+MASK=<mask> — set the 16-bit channel activity mask.

        *mask* must be exactly 4 hexadecimal characters (e.g. "0001"), where
        each bit enables or disables the corresponding 8-channel sub-band.
        Only applicable to US915, AU915, CN470, and LA915 regions.
        """
        if all(char in string.hexdigits for char in mask) and len(mask) == 4:
            response, ok = check_success(self, f"AT+MASK={mask}")
            if ok:
                return response
        else:
            logging.warning("This must be a 4 digit hexadecimal characters mask")
            return None

    def get_eight_channel_mode(self) -> str | None:
        """AT+CHE=? — return the current eight-channel sub-band selection.

        Only applicable to US915, AU915, CN470, and LA915 regions.
        Returns four colon-separated sub-band indices.
        """
        response, ok = check_success(self, "AT+CHE=?")
        if ok:
            return response

    def set_eight_channel_mode(
        self,
        value1: int = 0,
        value2: int = 0,
        value3: int = 0,
        value4: int = 0,
    ) -> str | None:
        """AT+CHE=<v1>:<v2>:<v3>:<v4> — select up to four 8-channel sub-bands.

        Each parameter selects an 8-channel sub-band.  A value of 0 disables
        the slot.  Valid sub-band range: 1-9 (1-12 for CN470).
        Only applicable to US915, AU915, CN470, and LA915 regions.
        """
        response, ok = check_success(
            self, f"AT+CHE={value1}:{value2}:{value3}:{value4}"
        )
        if ok:
            return response

    def get_single_channel_mode_freq(self) -> str | None:
        """AT+CHS=? — return the single-channel mode frequency in Hz (0 = disabled)."""
        response, ok = check_success(self, "AT+CHS=?")
        if ok:
            return response

    def set_single_channel_mode_freq(self, freq: int) -> str | None:
        """AT+CHS=<freq> — set the single-channel mode frequency in Hz.

        When non-zero, restricts all uplinks to this frequency.  Set to 0 to
        disable single-channel mode and restore the full channel plan.
        """
        response, ok = check_success(self, f"AT+CHS={freq}")
        if ok:
            return response

    def get_freq_band(self) -> str | None:
        """AT+BAND=? — return the current LoRaWAN frequency band index (0-12)."""
        response, ok = check_success(self, "AT+BAND=?")
        if ok:
            return response

    def set_freq_band(self, band: int) -> str | None:
        """AT+BAND=<band> — set the LoRaWAN frequency band.

        Band index mapping:
            0=EU433, 1=CN470, 2=RU864, 3=IN865, 4=EU868, 5=US915,
            6=AU915, 7=KR920, 8=AS923-1, 9=AS923-2, 10=AS923-3,
            11=AS923-4, 12=LA915.
        Valid range: 0-12.
        """
        if not 0 <= band <= 12:
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
    ) -> str | None:
        """AT+ADDMULC — add a multicast group.

        Configures the device to receive downlinks addressed to a multicast
        group.  Class B and Class C groups use the same parameter set; the
        *periodicity* parameter is required even for Class C (where it has no
        effect on receive scheduling).

        Args:
            lorawan_class: "B" or "C".
            dev_addr:      4-byte multicast device address as 8 hex characters.
            nwk_s_key:     16-byte multicast network session key as 32 hex characters.
            app_s_key:     16-byte multicast application session key as 32 hex characters.
            freq:          Multicast downlink frequency in Hz.
            datarate:      Multicast data rate index (0-7).
            periodicity:   Class B ping slot periodicity index (0-7); ignored for Class C.
        """
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
        if not 0 <= datarate <= 7:
            logging.warning("Datarate must be between 0 and 7")
            return None
        if not 0 <= periodicity <= 7:
            logging.warning("Periodicity must be between 0 and 7")
            return None
        response, ok = check_success(
            self,
            f"AT+ADDMULC={lorawan_class.upper()}:{dev_addr}"
            f":{nwk_s_key}:{app_s_key}:{freq}:{datarate}:{periodicity}",
        )
        if ok:
            return response

    def remove_multicast_group(self, dev_addr: str) -> str | None:
        """AT+RMVMULC=<dev_addr> — remove a previously configured multicast group.

        *dev_addr* must be exactly 8 hexadecimal characters (4 bytes, MSB first)
        and must match the address used when the group was added.
        """
        if all(char in string.hexdigits for char in dev_addr) and len(dev_addr) == 8:
            response, ok = check_success(self, f"AT+RMVMULC={dev_addr}")
            if ok:
                return response
        else:
            logging.warning("Device address must be exactly 8 hexadecimal characters")
            return None

    def get_multicast_group(self) -> str | None:
        """AT+LSTMULC=? — return a list of all configured multicast groups."""
        response, ok = check_success(self, "AT+LSTMULC=?")
        if ok:
            return response

    # P2P INSTRUCTIONS
    # The following commands configure and operate the module in LoRa P2P or
    # FSK P2P mode.  Switch between modes with set_lora_network_mode().

    def get_lora_network_mode(self) -> str | None:
        """AT+NWM=? — return the current network working mode (0, 1, or 2)."""
        response, ok = check_success(self, "AT+NWM=?")
        if ok:
            return response

    def set_lora_network_mode(self, mode: int) -> str | None:
        """AT+NWM=<mode> — set the network working mode.

        mode 0 — P2P LoRa (point-to-point LoRa modulation).
        mode 1 — LoRaWAN (managed network protocol).
        mode 2 — P2P FSK (point-to-point FSK modulation).
        """
        if mode not in (0, 1, 2):
            logging.warning("Mode must be either 0, 1 or 2")
            return None
        response, ok = check_success(self, f"AT+NWM={mode}")
        if ok:
            return response

    def get_p2p_freq(self) -> str | None:
        """AT+PFREQ=? — return the P2P radio frequency in Hz."""
        response, ok = check_success(self, "AT+PFREQ=?")
        if ok:
            return response

    def set_p2p_freq(self, freq: int) -> str | None:
        """AT+PFREQ=<freq> — set the P2P radio frequency in Hz.

        Valid range: 150000000-960000000 Hz.  The firmware does not enforce
        this range; the caller is responsible for passing a legal value.
        """
        response, ok = check_success(self, f"AT+PFREQ={freq}")
        if ok:
            return response

    def get_spread_factor(self) -> str | None:
        """AT+PSF=? — return the P2P LoRa spreading factor (5-12)."""
        response, ok = check_success(self, "AT+PSF=?")
        if ok:
            return response

    def set_spread_factor(self, spread: int = 7) -> str | None:
        """AT+PSF=<sf> — set the P2P LoRa spreading factor.

        Valid range: 5-12.  SF5 and SF6 use implicit header mode.  Higher
        spreading factors increase range at the cost of airtime.
        """
        if spread not in (5, 6, 7, 8, 9, 10, 11, 12):
            logging.warning("Value must be between 5 and 12")
            return None
        response, ok = check_success(self, f"AT+PSF={spread}")
        if ok:
            return response

    def get_p2p_band(self) -> str | None:
        """AT+PBW=? — return the P2P LoRa bandwidth index (0-9)."""
        response, ok = check_success(self, "AT+PBW=?")
        if ok:
            return response

    def set_p2p_band(self, band: int = 0) -> str | None:
        """AT+PBW=<band> — set the P2P LoRa bandwidth.

        Index encoding:
            0=125 kHz, 1=250 kHz, 2=500 kHz, 3=7.8 kHz, 4=10.4 kHz,
            5=15.63 kHz, 6=20.83 kHz, 7=31.25 kHz, 8=41.67 kHz, 9=62.5 kHz.
        Valid range: 0-9.
        """
        if not 0 <= band <= 9:
            logging.warning("Value must be between 0 and 9")
            return None
        response, ok = check_success(self, f"AT+PBW={band}")
        if ok:
            return response

    def get_p2p_code_rate(self) -> str | None:
        """AT+PCR=? — return the P2P LoRa coding rate index (0-3)."""
        response, ok = check_success(self, "AT+PCR=?")
        if ok:
            return response

    def set_p2p_code_rate(self, code_rate: int) -> str | None:
        """AT+PCR=<cr> — set the P2P LoRa coding rate.

        Index encoding: 0=4/5, 1=4/6, 2=4/7, 3=4/8.
        Higher coding rates improve error correction at the cost of airtime.
        Valid range: 0-3.
        """
        if code_rate not in (0, 1, 2, 3):
            logging.warning("Code rate must be between 0 and 3")
            return None
        response, ok = check_success(self, f"AT+PCR={code_rate}")
        if ok:
            return response

    def get_p2p_preamble_length(self) -> str | None:
        """AT+PPL=? — return the P2P LoRa preamble length in symbols (5-65535)."""
        response, ok = check_success(self, "AT+PPL=?")
        if ok:
            return response

    def set_p2p_preamble_length(self, length: int) -> str | None:
        """AT+PPL=<length> — set the P2P LoRa preamble length in symbols.

        Valid range: 5-65535.  Both transmitter and receiver must use the
        same preamble length.
        """
        if not 5 <= length <= 65535:
            logging.warning("Preamble length must be between 5 and 65535")
            return None
        response, ok = check_success(self, f"AT+PPL={length}")
        if ok:
            return response

    def get_p2p_tx_power(self) -> str | None:
        """AT+PTP=? — return the P2P TX output power in dBm (5-22)."""
        response, ok = check_success(self, "AT+PTP=?")
        if ok:
            return response

    def set_p2p_tx_power(self, tx_power: int) -> str | None:
        """AT+PTP=<power> — set the P2P TX output power in dBm.

        Valid range: 5-22 dBm.
        """
        if not 5 <= tx_power <= 22:
            logging.warning("TX power must between 5 and 22")
            return None
        response, ok = check_success(self, f"AT+PTP={tx_power}")
        if ok:
            return response

    def get_p2p_fsk_bitrate(self) -> str | None:
        """AT+PBR=? — return the P2P FSK bit rate in bits per second (600-300000)."""
        response, ok = check_success(self, "AT+PBR=?")
        if ok:
            return response

    def set_p2p_fsk_bitrate(self, bitrate: int) -> str | None:
        """AT+PBR=<bitrate> — set the P2P FSK bit rate in bits per second.

        Valid range: 600-300000 bps.  Only applicable in FSK mode (AT+NWM=2).
        """
        if not 600 <= bitrate <= 300000:
            logging.warning("Bitrate must be between 600 and 300000")
            return None
        response, ok = check_success(self, f"AT+PBR={bitrate}")
        if ok:
            return response

    def get_p2p_freq_deviation(self) -> str | None:
        """AT+PFDEV=? — return the P2P FSK frequency deviation in Hz (600-200000)."""
        response, ok = check_success(self, "AT+PFDEV=?")
        if ok:
            return response

    def set_p2p_freq_deviation(self, deviation: int) -> str | None:
        """AT+PFDEV=<deviation> — set the P2P FSK frequency deviation in Hz.

        Valid range: 600-200000 Hz.  Only applicable in FSK mode (AT+NWM=2).
        """
        if not 600 <= deviation <= 200000:
            logging.warning("Frequency deviation must be between 600 and 200000")
            return None
        response, ok = check_success(self, f"AT+PFDEV={deviation}")
        if ok:
            return response

    def p2p_send(self, payload: str) -> str | None:
        """AT+PSEND=<payload> — transmit a P2P payload.

        *payload* must be an even number of hexadecimal characters between
        2 and 500 (i.e. 1-250 bytes).
        """
        if (
            all(char in string.hexdigits for char in payload)
            and 2 <= len(payload) <= 500
            and len(payload) % 2 == 0
        ):
            response, ok = check_success(self, f"AT+PSEND={payload}")
            if ok:
                return response
        else:
            logging.warning(
            "Payload must be an even number of hexadecimal characters between 2 and 500"
        )
            return None

    def get_p2p_channel_activity(self) -> str | None:
        """AT+CAD=? — return the channel activity detection state (0 = disabled, 1 = enabled)."""
        response, ok = check_success(self, "AT+CAD=?")
        if ok:
            return response

    def set_p2p_channel_activity(self, on: bool) -> str | None:
        """AT+CAD=<mode> — enable (True) or disable (False) LoRa channel activity detection.

        When enabled, the radio listens for LoRa preamble activity before
        deciding whether the channel is occupied.
        """
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+CAD={mode}")
        if ok:
            return response

    def p2p_receive(self, timeout: int) -> str | None:
        """AT+PRECV=<timeout> — configure the P2P receive window.

        *timeout* values and their exact meanings per documentation:
            1 – 65532 — open RX window for *timeout* ms, then auto-stop and
                         emit +EVT:RXP2P RECEIVE TIMEOUT if nothing received.
            65533      — continuous RX; TX is still allowed (after each TX
                         the device automatically switches back to RX).
            65534      — continuous RX; no TX is possible until
                         p2p_receive(0) is called.
            65535      — RX until exactly one packet is received, then
                         automatically switch back to TX mode.
            0          — stop any ongoing RX session and switch to TX mode.

        NOTE: when set to 65534 (continuous RX), any new call to p2p_receive()
        is rejected by the firmware with AT_BUSY_ERROR.  You must first call
        p2p_receive(0) to exit continuous RX before changing any setting.
        """
        if not 0 <= timeout <= 65535:
            logging.warning("Timeout must be between 0 and 65535")
            return None
        response, ok = check_success(self, f"AT+PRECV={timeout}")
        if ok:
            return response

    def get_p2p_encryption(self) -> str | None:
        """AT+ENCRY=? — return the P2P payload encryption state (0 = disabled, 1 = enabled)."""
        response, ok = check_success(self, "AT+ENCRY=?")
        if ok:
            return response

    def set_p2p_encryption(self, on: bool) -> str | None:
        """AT+ENCRY=<mode> — enable (True) or disable (False) P2P payload encryption.

        When enabled, the payload is encrypted using AES-128 with the key
        configured via set_p2p_encryption_key().
        """
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+ENCRY={mode}")
        if ok:
            return response

    def get_p2p_encryption_key(self) -> str | None:
        """AT+ENCKEY=? — return the 16-byte P2P AES-128 encryption key as 32 hex characters."""
        response, ok = check_success(self, "AT+ENCKEY=?")
        if ok:
            return response

    def set_p2p_encryption_key(self, key: str) -> str | None:
        """AT+ENCKEY=<key> — set the 16-byte P2P AES-128 encryption key.

        *key* must be exactly 32 hexadecimal characters (16 bytes).
        """
        if all(char in string.hexdigits for char in key) and len(key) == 32:
            response, ok = check_success(self, f"AT+ENCKEY={key}")
            if ok:
                return response
        else:
            logging.warning("Encryption key must be exactly 32 hexadecimal characters")
            return None
        
    def get_p2p_crypt_status(self) -> str | None:
        """AT+PCRYPT=? — return the P2P additional encryption layer state (0 = disabled, 1 = enabled)."""
        response, ok = check_success(self, "AT+PCRYPT=?")
        if ok:
            return response

    def set_p2p_crypt_status(self, on: bool) -> str | None:
        """AT+PCRYPT=<mode> — enable (True) or disable (False) the P2P additional encryption layer.

        This encryption layer uses the key configured via
        set_p2p_crypt_decrypt_key() and the IV from set_p2p_crypt_iv().
        """
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+PCRYPT={mode}")
        if ok:
            return response

    def get_p2p_crypt_decrypt_key(self) -> str | None:
        """AT+PKEY=? — return the 8-byte P2P crypt/decrypt key as 16 hex characters."""
        response, ok = check_success(self, "AT+PKEY=?")
        if ok:
            return response

    def set_p2p_crypt_decrypt_key(self, key: str) -> str | None:
        """AT+PKEY=<key> — set the 8-byte P2P crypt/decrypt key.

        *key* must be exactly 16 hexadecimal characters (8 bytes).
        """
        if all(char in string.hexdigits for char in key) and len(key) == 16:
            response, ok = check_success(self, f"AT+PKEY={key}")
            if ok:
                return response
        else:
            logging.warning("Key must be exactly 16 hexadecimal characters")
            return None
        
    def get_p2p_crypt_iv(self) -> str | None:
        """AT+CRYPIV=? — return the 16-byte P2P encryption initialisation vector as 32 hex characters."""
        response, ok = check_success(self, "AT+CRYPIV=?")
        if ok:
            return response

    def set_p2p_crypt_iv(self, key: str) -> str | None:
        """AT+CRYPIV=<iv> — set the 16-byte P2P encryption initialisation vector.

        *iv* must be exactly 32 hexadecimal characters (16 bytes).
        """
        if all(char in string.hexdigits for char in key) and len(key) == 32:
            response, ok = check_success(self, f"AT+CRYPIV={key}")
            if ok:
                return response
        else:
            logging.warning("CryptIV key must be exactly 32 hexadecimal characters")
            return None

    def get_p2p_params(self) -> str | None:
        """AT+P2P=? — return all P2P parameters in the format <freq>:<sf>:<bw>:<cr>:<preamble>:<power>."""
        response, ok = check_success(self, "AT+P2P=?")
        if ok:
            return response

    def set_p2p_params(
        self,
        freq: int = 868000000,
        sf: int = 7,
        bandwidth: int = 0,
        code_rate: int = 0,
        preamble_len: int = 8,
        tx_power: int = 14,
    ) -> str | None:
        """AT+P2P=<freq>:<sf>:<bw>:<cr>:<preamble>:<power> — set all P2P parameters at once.

        Args:
            freq:         Radio frequency in Hz (150000000-960000000).
            sf:           Spreading factor (6-12).
            bandwidth:    Bandwidth index (0-9; see set_p2p_band() for encoding).
            code_rate:    Coding rate (0=4/5, 1=4/6, 2=4/7, 3=4/8).
            preamble_len: Preamble length in symbols (2-65535).
            tx_power:     TX output power in dBm (5-22).
        """
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

    def get_p2p_iq_inv(self) -> str | None:
        """AT+IQINVER=? — return the P2P IQ inversion state (0 = normal, 1 = inverted)."""
        response, ok = check_success(self, "AT+IQINVER=?")
        if ok:
            return response

    def set_p2p_iq_inv(self, on: bool) -> str | None:
        """AT+IQINVER=<mode> — enable (True) or disable (False) P2P IQ signal inversion.

        IQ inversion is used to distinguish uplink and downlink signals in
        some P2P deployments, or to prevent interference between networks
        using the same frequency.
        """
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+IQINVER={mode}")
        if ok:
            return response

    def get_p2p_syncword(self) -> str | None:
        """AT+SYNCWORD=? — return the P2P LoRa sync word as a 4-character hex string."""
        response, ok = check_success(self, "AT+SYNCWORD=?")
        if ok:
            return response

    def set_p2p_syncword(self, word: str) -> str | None:
        """AT+SYNCWORD=<word> — set the P2P LoRa sync word.

        *word* must be exactly 4 hexadecimal characters (2 bytes), e.g. "1424".
        All devices in the same P2P network must use the same sync word.
        """
        if all(char in string.hexdigits for char in word) and len(word) == 4:
            response, ok = check_success(self, f"AT+SYNCWORD={word}")
            if ok:
                return response
        else:
            logging.warning("Syncword must be exactly 4 hexadecimal characters")
            return None

    # P2P LEGACY COMMANDS
    # The commands below (AT+RFFREQUENCY through AT+FIXLENGTHPAYLOAD) are the
    # older individual-parameter counterparts to the modern AT+P2P command.
    # They are provided for backward compatibility.  Prefer the AT+P2P
    # equivalent (set_p2p_params / get_p2p_params) for new code.

    def get_p2p_rf_freq(self) -> str | None:
        """AT+RFFREQUENCY=? — return the P2P radio frequency in Hz (legacy command)."""
        response, ok = check_success(self, "AT+RFFREQUENCY=?")
        if ok:
            return response

    def set_p2p_rf_freq(self, freq: int) -> str | None:
        """AT+RFFREQUENCY=<freq> — set the P2P radio frequency in Hz (legacy command).

        Valid range: 150000000-960000000 Hz.
        """
        response, ok = check_success(self, f"AT+RFFREQUENCY={freq}")
        if ok:
            return response

    def get_p2p_tx_out_power(self) -> str | None:
        """AT+TXOUTPUTPOWER=? — return the P2P TX output power in dBm (legacy command)."""
        response, ok = check_success(self, "AT+TXOUTPUTPOWER=?")
        if ok:
            return response

    def set_p2p_tx_out_power(self, tx_out: int) -> str | None:
        """AT+TXOUTPUTPOWER=<power> — set the P2P TX output power in dBm (legacy command).

        Valid range: 5-22 dBm.
        """
        if not 5 <= tx_out <= 22:
            logging.warning("TX out power must be between 5 and 22")
            return None
        response, ok = check_success(self, f"AT+TXOUTPUTPOWER={tx_out}")
        if ok:
            return response

    def get_p2p_bandwidth(self) -> str | None:
        """AT+BANDWIDTH=? — return the P2P LoRa bandwidth index (legacy command)."""
        response, ok = check_success(self, "AT+BANDWIDTH=?")
        if ok:
            return response

    def set_p2p_bandwidth(self, band: int) -> str | None:
        """AT+BANDWIDTH=<band> — set the P2P LoRa bandwidth (legacy command).

        Index encoding (same as AT+PBW):
            0=125 kHz, 1=250 kHz, 2=500 kHz, 3=7.8 kHz, 4=10.4 kHz,
            5=15.63 kHz, 6=20.83 kHz, 7=31.25 kHz, 8=41.67 kHz, 9=62.5 kHz.
        Valid range: 0-9.
        """
        if not 0 <= band <= 9:
            logging.warning("Bandwidth must be between 0 and 9")
            return None
        response, ok = check_success(self, f"AT+BANDWIDTH={band}")
        if ok:
            return response

    def get_p2p_spread_factor(self) -> str | None:
        """AT+SPREADINGFACTOR=? — return the P2P LoRa spreading factor (legacy command)."""
        response, ok = check_success(self, "AT+SPREADINGFACTOR=?")
        if ok:
            return response

    def set_p2p_spread_factor(self, sf: int) -> str | None:
        """AT+SPREADINGFACTOR=<sf> — set the P2P LoRa spreading factor (legacy command).

        Valid range: 5-12, matching AT+PSF.
        """
        if not 5 <= sf <= 12:
            logging.warning("Spreading factor must be between 5 and 12")
            return None
        response, ok = check_success(self, f"AT+SPREADINGFACTOR={sf}")
        if ok:
            return response

    def get_p2p_coding_rate(self) -> str | None:
        """AT+CODINGRATE=? — return the P2P LoRa coding rate index (legacy command)."""
        response, ok = check_success(self, "AT+CODINGRATE=?")
        if ok:
            return response

    def set_p2p_coding_rate(self, code_rate: int) -> str | None:
        """AT+CODINGRATE=<cr> — set the P2P LoRa coding rate (legacy command).

        Index encoding: 0=4/5, 1=4/6, 2=4/7, 3=4/8.
        Valid range: 0-3.
        """
        if code_rate not in (0, 1, 2, 3):
            logging.warning("Coding rate must be either 0, 1, 2 or 3")
            return None
        response, ok = check_success(self, f"AT+CODINGRATE={code_rate}")
        if ok:
            return response

    def get_p2p_preamble_length_2(self) -> str | None:
        """AT+PREAMBLELENGTH=? — return the P2P preamble length in symbols (legacy command)."""
        response, ok = check_success(self, "AT+PREAMBLELENGTH=?")
        if ok:
            return response

    def set_p2p_preamble_length_2(self, preamble_len: int) -> str | None:
        """AT+PREAMBLELENGTH=<len> — set the P2P preamble length in symbols (legacy command).

        Valid range: 5-65535 symbols.
        """
        if not (5 <= preamble_len <= 65535):
            logging.warning("Preamble length must be between 5 and 65535")
            return None
        response, ok = check_success(self, f"AT+PREAMBLELENGTH={preamble_len}")
        if ok:
            return response

    def get_p2p_symbol_timeout(self) -> str | None:
        """AT+SYMBOLTIMEOUT=? — return the P2P RX symbol timeout (legacy command).

        The value is expressed in symbol periods (0-248).  A value of 0
        disables the timeout (continuous receive until manually stopped).
        """
        response, ok = check_success(self, "AT+SYMBOLTIMEOUT=?")
        if ok:
            return response

    def set_p2p_symbol_timeout(self, timeout: int) -> str | None:
        """AT+SYMBOLTIMEOUT=<timeout> — set the P2P RX symbol timeout (legacy command).

        *timeout* is in symbol periods; valid range is 0-248.  Set to 0 to
        disable the timeout.
        """
        if not 0 <= timeout <= 248:
            logging.warning("Symbol timeout must be between 0 and 248")
            return None
        response, ok = check_success(self, f"AT+SYMBOLTIMEOUT={timeout}")
        if ok:
            return response

    def get_p2p_fixed_length_payload(self) -> str | None:
        """AT+FIXLENGTHPAYLOAD=? — return the fixed-length payload mode (legacy command).

        Returns 0 (variable-length payload) or 1 (fixed-length payload).
        """
        response, ok = check_success(self, "AT+FIXLENGTHPAYLOAD=?")
        if ok:
            return response

    def set_p2p_fixed_length_payload(self, on: bool) -> str | None:
        """AT+FIXLENGTHPAYLOAD=<mode> — enable (True) or disable (False) fixed-length payload mode (legacy command).

        When enabled, the receiver does not include a payload length field in
        the LoRa header (implicit header mode).  Both sides must be configured
        identically.
        """
        mode = 1 if on else 0
        response, ok = check_success(self, f"AT+FIXLENGTHPAYLOAD={mode}")
        if ok:
            return response

    # RF TEST
    # The following commands place the radio in test mode for hardware
    # verification and regulatory certification.  Always call rf_test_stop()
    # before returning the module to normal LoRaWAN or P2P operation.

    def rf_rssi_test(self) -> str | None:
        """AT+TRSSI=? — execute an RSSI test and return the measured value."""
        response, ok = check_success(self, "AT+TRSSI=?")
        if ok:
            return response

    def rf_tone_test(self) -> str | None:
        """AT+TTONE — start a continuous RF tone test on the current frequency."""
        response, ok = check_success(self, "AT+TTONE")
        if ok:
            return response

    def set_rf_tx_test_packet_number(self, number: int) -> str | None:
        """AT+TTX=<n> — transmit *n* test packets at the current RF configuration."""
        response, ok = check_success(self, f"AT+TTX={number}")
        if ok:
            return response

    def set_rf_rx_test_packet_number(self, number: int) -> str | None:
        """AT+TRX=<n> — receive *n* test packets and report results."""
        response, ok = check_success(self, f"AT+TRX={number}")
        if ok:
            return response

    def set_rf_test_config(
        self,
        freq: int,
        power: int,
        bw: int,
        sf: int,
        cr: int,
        lna: int,
        pa_boost: int,
        modulation: int,
        payload_len: int,
        fdev: int,
        lowdropt: int,
        bt: int,
    ) -> str | None:
        """AT+TCONF=<Freq>:<Power>:<Bandwidth>:<SF>:<CR>:<LNA>:<PABoost>:<Modulation>:<PayloadLen>:<FskDeviation>:<LowDRopt>:<BTproduct>
        — configure the LoRa/FSK RF test parameters.

        This command must be issued before starting any RF test with AT+TTX or
        AT+TRX.  Use rf_test_stop() (AT+TOFF) to terminate an ongoing test.
        The number of packets for AT+TTX / AT+TRX is passed to those commands
        directly, not here.

        Args:
            freq:       Radio frequency in Hz.
                            Low-frequency modules (e.g. RAK3172-L):
                                150000000 – 600000000 Hz.
                            High-frequency modules (e.g. RAK3172-H):
                                600000000 – 960000000 Hz.
            power:      TX output power in dBm (5-22).
            bw:         Bandwidth.
                            LoRa mode (index, same encoding as AT+PBW):
                                0=125 kHz, 1=250 kHz, 2=500 kHz,
                                3=7.8 kHz, 4=10.4 kHz, 5=15.63 kHz,
                                6=20.83 kHz, 7=31.25 kHz, 8=41.67 kHz,
                                9=62.5 kHz.
                            FSK mode: direct value in Hz (4800-467000).
            sf:         LoRa spreading factor (5-12).  Ignored in FSK mode.
            cr:         LoRa coding rate: 1=4/5, 2=4/6, 3=4/7, 4=4/8.
                            **Note:** this parameter is 1-based, unlike AT+PCR
                            which is 0-based.  Ignored in FSK mode.
            lna:        LNA state (0 or 1).  Not implemented in current
                            firmware; pass 0.
            pa_boost:   PA Boost state (0 or 1).  Not implemented in current
                            firmware; pass 0.
            modulation: Modulation type: 0=FSK, 1=LoRa.
            payload_len: Payload length in bytes (1-255).
            fdev:       FSK frequency deviation in Hz (600-200000).
                            Only meaningful in FSK mode (modulation=0);
                            pass any value (e.g. 25000) for LoRa mode.
            lowdropt:   Low data rate optimisation flag.  Not implemented in
                            current firmware; pass 0.
            bt:         Gaussian filter bandwidth-time product for FSK.
                            Not implemented in current firmware; pass 0.

        Default values (from documentation):
            868000000, 14, 0, 7, 1, 0, 0, 1, 4, 25000, 0, 0

        Example (from documentation):
            AT+TCONF=868000000:14:4:12:1:0:0:1:16:25000:2:3
        """
        if not 150000000 <= freq <= 960000000:
            logging.warning("Frequency must be between 150 MHz and 960 MHz")
            return None
        if not 5 <= power <= 22:
            logging.warning("TX power must be between 5 and 22 dBm")
            return None
        if modulation not in (0, 1):
            logging.warning("Modulation must be 0 (FSK) or 1 (LoRa)")
            return None
        # Bandwidth validation is modulation-dependent (must be checked
        # after modulation is validated).
        if modulation == 1:  # LoRa: index 0-9
            if not 0 <= bw <= 9:
                logging.warning(
                    "Bandwidth index must be 0-9 for LoRa mode "
                    "(0=125 kHz, 1=250 kHz, 2=500 kHz, 3=7.8 kHz, "
                    "4=10.4 kHz, 5=15.63 kHz, 6=20.83 kHz, "
                    "7=31.25 kHz, 8=41.67 kHz, 9=62.5 kHz)"
                )
                return None
        else:  # FSK: direct Hz value
            if not 4800 <= bw <= 467000:
                logging.warning("Bandwidth must be 4800-467000 Hz for FSK mode")
                return None
        if not 5 <= sf <= 12:
            logging.warning("Spreading factor must be between 5 and 12")
            return None
        if cr not in (1, 2, 3, 4):
            logging.warning(
                "Coding rate must be 1 (4/5), 2 (4/6), 3 (4/7), or 4 (4/8). "
                "Note: AT+TCONF uses 1-based coding rate, unlike AT+PCR."
            )
            return None
        if lna not in (0, 1):
            logging.warning("LNA state must be 0 or 1")
            return None
        if pa_boost not in (0, 1):
            logging.warning("PA Boost state must be 0 or 1")
            return None
        if not 1 <= payload_len <= 255:
            logging.warning("Payload length must be between 1 and 255 bytes")
            return None
        if not 600 <= fdev <= 200000:
            logging.warning(
                "FSK frequency deviation must be between 600 and 200000 Hz. "
                "For LoRa mode this parameter is ignored by the firmware but "
                "must still be a valid value; use the default 25000."
            )
            return None
        response, ok = check_success(
            self,
            f"AT+TCONF={freq}:{power}:{bw}:{sf}:{cr}:{lna}:{pa_boost}"
            f":{modulation}:{payload_len}:{fdev}:{lowdropt}:{bt}",
        )
        if ok:
            return response

    def rf_tone_hopping_test(
        self,
        fstart: int,
        fstop: int,
        fdelta: int,
        packet_nb: int,
    ) -> str | None:
        """AT+TTH=<Fstart>:<Fstop>:<FDelta>:<PacketNb> — start a sequential RF TX hopping test.

        The radio transmits *packet_nb* packets stepping through frequencies from
        *fstart* to *fstop* in increments of *fdelta* Hz.  The modulation
        parameters are taken from the last AT+TCONF configuration.

        This is a sequential sweep; for a random-order sweep use
        rf_tx_fhss_hopping_test() (AT+TRTH).

        Example — 6 hops from 868 MHz to 868.5 MHz in 100 kHz steps:
            AT+TTH=868000000:868500000:100000:6

        Args:
            fstart:    Start frequency in Hz (150000000-960000000).
            fstop:     Stop frequency in Hz (150000000-960000000).
                           Must be greater than *fstart*.
            fdelta:    Frequency step between hops in Hz (> 0).
            packet_nb: Number of packets to transmit per hop (> 0).
        """
        if not 150000000 <= fstart <= 960000000:
            logging.warning("Start frequency must be between 150 MHz and 960 MHz")
            return None
        if not 150000000 <= fstop <= 960000000:
            logging.warning("Stop frequency must be between 150 MHz and 960 MHz")
            return None
        if fstop <= fstart:
            logging.warning("Stop frequency must be greater than start frequency")
            return None
        if fdelta <= 0:
            logging.warning("Frequency delta must be greater than 0 Hz")
            return None
        if packet_nb < 1:
            logging.warning("Number of packets must be at least 1")
            return None
        response, ok = check_success(
            self, f"AT+TTH={fstart}:{fstop}:{fdelta}:{packet_nb}"
        )
        if ok:
            return response

    def rf_test_stop(self) -> str | None:
        """AT+TOFF — stop any ongoing RF test (tone, hopping, TX, or RX).

        This is the only way to terminate a continuous test (e.g. AT+TTONE or
        AT+TTH with no stop condition).  Always call this before switching back
        to normal LoRaWAN or P2P operation.
        """
        response, ok = check_success(self, "AT+TOFF")
        if ok:
            return response

    def rf_certification_test(self) -> str | None:
        """AT+CERTIF — enter LoRaWAN certification test mode.

        The module enters certification mode and handles test frames from the
        certification tool automatically.  The internal timer for data
        transmission is set to 5 seconds.
        AT_BUSY_ERROR is returned if a frequency tone test is already running.
        """
        response, ok = check_success(self, "AT+CERTIF")
        if ok:
            return response

    def rf_continuous_wave_test(
        self, freq: int, power: int, time_ms: int
    ) -> str | None:
        """AT+CW=<freq>:<power>:<time> — transmit a continuous wave signal.

        Args:
            freq:    Radio frequency in Hz.
                         Low-frequency modules: 150000000-600000000 Hz.
                         High-frequency modules: 600000000-960000000 Hz.
            power:   TX power in dBm (5-22).
            time_ms: Duration in milliseconds (0-65535).
                         0 means transmit continuously until rf_test_stop()
                         (AT+TOFF) is called.
        """
        if not 150000000 <= freq <= 960000000:
            logging.warning("Frequency must be between 150 MHz and 960 MHz")
            return None
        if not 5 <= power <= 22:
            logging.warning("TX power must be between 5 and 22 dBm")
            return None
        if not 0 <= time_ms <= 65535:
            logging.warning("Duration must be between 0 and 65535 ms (0 = continuous)")
            return None
        response, ok = check_success(self, f"AT+CW={freq}:{power}:{time_ms}")
        if ok:
            return response

    def rf_tx_fhss_hopping_test(
        self,
        start_freq: int,
        end_freq: int,
        hop_step: int,
        hop_count: int,
    ) -> str | None:
        """AT+TRTH=<start_freq>:<end_freq>:<hop_step>:<hop_count> — start an FHSS TX hopping test.

        The radio transmits sequentially across *hop_count* channels, starting
        at *start_freq*, incrementing by *hop_step* Hz each hop, and stopping
        at or before *end_freq*.  The modulation parameters (SF, BW, power,
        payload) used for each hop are those previously configured via
        set_rf_test_config() (AT+TCONF).

        This command requires the device to be in LoRaWAN mode (AT+NWM=1) with
        the appropriate region set (AT+BAND).  Call rf_test_stop() (AT+TOFF)
        to terminate the test early.

        Example — US915 FHSS across 64 channels at 200 kHz spacing:
            AT+TRTH=902300000:914900000:200000:64

        Args:
            start_freq: Start frequency in Hz (150000000-960000000).
            end_freq:   End frequency in Hz (150000000-960000000).
                            Must be greater than *start_freq*.
            hop_step:   Frequency step between hops in Hz (> 0).
            hop_count:  Total number of hops to perform (> 0).
        """
        if not 150000000 <= start_freq <= 960000000:
            logging.warning("Start frequency must be between 150 MHz and 960 MHz")
            return None
        if not 150000000 <= end_freq <= 960000000:
            logging.warning("End frequency must be between 150 MHz and 960 MHz")
            return None
        if end_freq <= start_freq:
            logging.warning("End frequency must be greater than start frequency")
            return None
        if hop_step <= 0:
            logging.warning("Hop step must be greater than 0 Hz")
            return None
        if hop_count < 1:
            logging.warning("Hop count must be at least 1")
            return None
        response, ok = check_success(
            self, f"AT+TRTH={start_freq}:{end_freq}:{hop_step}:{hop_count}"
        )
        if ok:
            return response
