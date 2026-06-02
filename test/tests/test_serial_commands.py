"""
tests/test_serial_commands.py
==============================
Tests for the Serial AT Commands section.

Covered methods
---------------
lock_serial, set_password, get_baud_rate, set_baud_rate, switch_to_at_mode.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

import rui3pylib
from conftest import OK_RESPONSE, ERR_PARAM


# ===========================================================================
# AT+LOCK — lock serial port
# ===========================================================================

class TestLockSerial:

    @pytest.mark.cmd_format
    def test_uses_send_command_not_check_success(self, node):
        """AT+LOCK does not wait for OK; send_command is used directly."""
        with patch("rui3pylib.send_command") as m_send, \
             patch("rui3pylib.check_success") as m_check:
            node.lock_serial()
            m_send.assert_called_once_with(node, "AT+LOCK")
            m_check.assert_not_called()

    @pytest.mark.happy_path
    def test_returns_none(self, node):
        """lock_serial is fire-and-forget, always returns None."""
        with patch("rui3pylib.send_command"):
            assert node.lock_serial() is None


# ===========================================================================
# AT+PWORD — set serial port password
# ===========================================================================

class TestSetPassword:

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_sends_correct_command(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_password("abc123")
            m.assert_called_once_with(node, "AT+PWORD=abc123")

    @pytest.mark.boundary
    def test_single_char_password_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_password("X")
            m.assert_called_once_with(node, "AT+PWORD=X")
            assert result is not None

    @pytest.mark.boundary
    def test_8_char_password_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_password("12345678")
            m.assert_called_once_with(node, "AT+PWORD=12345678")
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_empty_password_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_password("")
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_9_char_password_rejected(self, node):
        """Password exceeding 8 characters → None."""
        with patch("rui3pylib.check_success") as m:
            result = node.set_password("123456789")  # 9 chars
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    def test_non_printable_char_rejected(self, node):
        """Password containing non-printable chars → None."""
        with patch("rui3pylib.check_success") as m:
            result = node.set_password("abc\x00de")  # null byte
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    def test_printable_special_chars_accepted(self, node):
        """Printable special characters in a password are valid."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_password("~!@pword")  # example from docs
            m.assert_called_once_with(node, "AT+PWORD=~!@pword")
            assert result is not None

    @pytest.mark.device_error
    def test_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_password("test") is None


# ===========================================================================
# AT+BAUD — serial baud rate
# ===========================================================================

class TestBaudRate:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_baud_rate()
            m.assert_called_once_with(node, "AT+BAUD=?")

    @pytest.mark.cmd_format
    def test_set_sends_baud_value(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_baud_rate(115200)
            m.assert_called_once_with(node, "AT+BAUD=115200")

    @pytest.mark.happy_path
    def test_set_common_baud_rates(self, node):
        """Standard baud rates used in embedded systems."""
        for baud in (9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600):
            with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
                result = node.set_baud_rate(baud)
                assert result is not None, f"Baud rate {baud} should be accepted"

    @pytest.mark.happy_path
    def test_set_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.set_baud_rate(115200) is not None

    @pytest.mark.device_error
    def test_get_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_baud_rate() is None


# ===========================================================================
# AT+ATM — switch to AT command mode
# ===========================================================================

class TestSwitchToAtMode:

    @pytest.mark.cmd_format
    def test_sends_correct_command(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.switch_to_at_mode()
            m.assert_called_once_with(node, "AT+ATM")

    @pytest.mark.happy_path
    def test_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.switch_to_at_mode() is not None

    @pytest.mark.device_error
    def test_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.switch_to_at_mode() is None
