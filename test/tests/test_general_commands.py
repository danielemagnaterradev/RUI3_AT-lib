"""
tests/test_general_commands.py
================================
Tests for the General Commands section of the RUI3 AT command manual.

Covered methods
---------------
ping, at_help, toggle_command_echo, reset, restore_default,
get_serial_number, get_battery_level, get_build_time, get_repo_info,
get_firm_version, get_at_version, get_api_version, get_hw_model,
get_hw_id, get_device_alias, set_device_alias,
get_system_voltage, get_ble_mac, set_ble_mac, get_boot_ver.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, call

import rui3pylib
from conftest import OK_RESPONSE, ERR_PARAM


# ── shared helpers ──────────────────────────────────────────────────────────


def _ok(node, method_name: str, *args, expected_cmd: str) -> None:
    """Assert that method sends the expected command and returns non-None."""
    with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
        result = getattr(node, method_name)(*args)
        m.assert_called_once_with(node, expected_cmd)
        assert result is not None


def _fail(node, method_name: str, *args) -> None:
    """Assert that when the device returns an error, the method returns None."""
    with patch("rui3pylib.check_success", return_value=ERR_PARAM):
        result = getattr(node, method_name)(*args)
        assert result is None


# ===========================================================================
# AT — ping
# ===========================================================================


class TestPing:
    @pytest.mark.cmd_format
    def test_sends_bare_at(self, node):
        _ok(node, "ping", expected_cmd="AT")

    @pytest.mark.happy_path
    def test_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.ping() is not None

    @pytest.mark.device_error
    def test_returns_none_on_failure(self, node):
        _fail(node, "ping")


# ===========================================================================
# AT? — short help
# ===========================================================================


class TestAtHelp:
    @pytest.mark.cmd_format
    def test_sends_at_question_mark(self, node):
        _ok(node, "at_help", expected_cmd="AT?")

    @pytest.mark.device_error
    def test_returns_none_on_failure(self, node):
        _fail(node, "at_help")


# ===========================================================================
# ATE — echo toggle
# ===========================================================================


class TestToggleCommandEcho:
    @pytest.mark.cmd_format
    def test_sends_ate(self, node):
        _ok(node, "toggle_command_echo", expected_cmd="ATE")

    @pytest.mark.device_error
    def test_returns_none_on_failure(self, node):
        _fail(node, "toggle_command_echo")


# ===========================================================================
# ATZ — MCU reset
# ===========================================================================


class TestReset:
    @pytest.mark.cmd_format
    def test_uses_send_command_not_check_success(self, node):
        """ATZ does not return OK; send_command is used directly."""
        with (
            patch("rui3pylib.send_command") as m_send,
            patch("rui3pylib.check_success") as m_check,
        ):
            node.reset()
            m_send.assert_called_once_with(node, "ATZ")
            m_check.assert_not_called()

    @pytest.mark.happy_path
    def test_returns_none(self, node):
        """reset() always returns None (fire-and-forget)."""
        with patch("rui3pylib.send_command"):
            assert node.reset() is None


# ===========================================================================
# ATR — restore defaults
# ===========================================================================


class TestRestoreDefault:
    @pytest.mark.cmd_format
    def test_sends_atr(self, node):
        _ok(node, "restore_default", expected_cmd="ATR")

    @pytest.mark.device_error
    def test_returns_none_on_failure(self, node):
        _fail(node, "restore_default")


# ===========================================================================
# AT+SN — serial number (read-only)
# ===========================================================================


class TestGetSerialNumber:
    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        _ok(node, "get_serial_number", expected_cmd="AT+SN=?")

    @pytest.mark.device_error
    def test_returns_none_on_failure(self, node):
        _fail(node, "get_serial_number")


# ===========================================================================
# AT+BAT — battery level (read-only)
# ===========================================================================


class TestGetBatteryLevel:
    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        _ok(node, "get_battery_level", expected_cmd="AT+BAT=?")

    @pytest.mark.device_error
    def test_returns_none_on_failure(self, node):
        _fail(node, "get_battery_level")


# ===========================================================================
# AT+BUILDTIME (read-only)
# ===========================================================================


class TestGetBuildTime:
    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        _ok(node, "get_build_time", expected_cmd="AT+BUILDTIME=?")


# ===========================================================================
# AT+REPOINFO (read-only)
# ===========================================================================


class TestGetRepoInfo:
    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        _ok(node, "get_repo_info", expected_cmd="AT+REPOINFO=?")


# ===========================================================================
# AT+VER — firmware version (read-only)
# ===========================================================================


class TestGetFirmVersion:
    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        _ok(node, "get_firm_version", expected_cmd="AT+VER=?")


# ===========================================================================
# AT+CLIVER — AT command set version (read-only)
# ===========================================================================


class TestGetAtVersion:
    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        _ok(node, "get_at_version", expected_cmd="AT+CLIVER=?")


# ===========================================================================
# AT+APIVER — API version (read-only)
# ===========================================================================


class TestGetApiVersion:
    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        _ok(node, "get_api_version", expected_cmd="AT+APIVER=?")


# ===========================================================================
# AT+HWMODEL — hardware model string (read-only)
# ===========================================================================


class TestGetHwModel:
    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        _ok(node, "get_hw_model", expected_cmd="AT+HWMODEL=?")


# ===========================================================================
# AT+HWID — hardware ID (read-only)
# ===========================================================================


class TestGetHwId:
    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        _ok(node, "get_hw_id", expected_cmd="AT+HWID=?")


# ===========================================================================
# AT+ALIAS — device alias (get + set)
# ===========================================================================


class TestDeviceAlias:
    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        _ok(node, "get_device_alias", expected_cmd="AT+ALIAS=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_set_sends_alias_value(self, node):
        _ok(node, "set_device_alias", "MySensor", expected_cmd="AT+ALIAS=MySensor")

    @pytest.mark.boundary
    def test_set_single_char_alias_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_device_alias("X")
            m.assert_called_once_with(node, "AT+ALIAS=X")
            assert result is not None

    @pytest.mark.boundary
    def test_set_16_char_alias_accepted(self, node):
        alias = "A" * 16
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_device_alias(alias)
            m.assert_called_once_with(node, f"AT+ALIAS={alias}")
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_empty_alias_rejected(self, node):
        """Alias must be at least 1 character; empty string → None, no AT command sent."""
        with patch("rui3pylib.check_success") as m:
            result = node.set_device_alias("")
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_17_char_alias_rejected(self, node):
        """Alias must be ≤ 16 characters; 17-char string → None."""
        with patch("rui3pylib.check_success") as m:
            result = node.set_device_alias("A" * 17)
            m.assert_not_called()
            assert result is None

    @pytest.mark.device_error
    def test_set_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_device_alias("test") is None


# ===========================================================================
# AT+SYSV — system voltage (read-only)
# ===========================================================================


class TestGetSystemVoltage:
    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        _ok(node, "get_system_voltage", expected_cmd="AT+SYSV=?")


# ===========================================================================
# AT+BLEMAC — BLE MAC address (get + set)
# ===========================================================================


class TestBleMac:
    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        _ok(node, "get_ble_mac", expected_cmd="AT+BLEMAC=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_set_formats_to_colon_separated_lowercase(self, node):
        """12-char hex string → 'xx:xx:xx:xx:xx:xx' in lowercase."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_ble_mac("001122334455")
            m.assert_called_once_with(node, "AT+BLEMAC=00:11:22:33:44:55")

    @pytest.mark.cmd_format
    def test_set_uppercase_input_produces_lowercase_cmd(self, node):
        """Uppercase hex input is converted to lowercase in the AT command."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_ble_mac("AABBCCDDEEFF")
            m.assert_called_once_with(node, "AT+BLEMAC=aa:bb:cc:dd:ee:ff")

    @pytest.mark.cmd_format
    def test_set_mixed_case_input_produces_lowercase_cmd(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_ble_mac("aAbBcCdDeEfF")
            m.assert_called_once_with(node, "AT+BLEMAC=aa:bb:cc:dd:ee:ff")

    @pytest.mark.happy_path
    def test_set_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.set_ble_mac("001122334455") is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_11_char_mac_rejected(self, node):
        """MAC address shorter than 12 hex chars → None, no AT command."""
        with patch("rui3pylib.check_success") as m:
            result = node.set_ble_mac("00112233445")  # 11 chars
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_13_char_mac_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_ble_mac("0011223344556")  # 13 chars
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    def test_set_non_hex_chars_rejected(self, node):
        """Non-hex characters in the MAC address → None."""
        with patch("rui3pylib.check_success") as m:
            result = node.set_ble_mac("001122GG4455")  # 'G' is invalid
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    def test_set_empty_string_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_ble_mac("")
            m.assert_not_called()
            assert result is None

    @pytest.mark.device_error
    def test_set_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_ble_mac("001122334455") is None


# ===========================================================================
# AT+BOOTVER — RUI bootloader version (read-only, normal mode)
# ===========================================================================


class TestGetBootVer:
    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        _ok(node, "get_boot_ver", expected_cmd="AT+BOOTVER=?")

    @pytest.mark.device_error
    def test_returns_none_on_failure(self, node):
        _fail(node, "get_boot_ver")
