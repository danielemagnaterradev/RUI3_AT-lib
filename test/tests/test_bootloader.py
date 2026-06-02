"""
tests/test_bootloader.py
=========================
Tests for the Bootloader Commands section.

Covered methods
---------------
set_boot_mode, get_bootloader_ver, get_bootloader_status,
at_run, boot_reset, boot_update.

Important
---------
All bootloader commands (except set_boot_mode) only function when the
device is *in* boot mode.  They use send_command directly because the
bootloader does not emit the standard "OK" status token.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

import rui3pylib
from conftest import OK_RESPONSE


BOOT_RESPONSE = "<BOOT MODE>\r\n"
VERSION_RESPONSE = "RUI_BOOT_0.6_STM32WLE5CC\r\n"


# ===========================================================================
# AT+BOOT — enter bootloader mode
# ===========================================================================

class TestSetBootMode:

    @pytest.mark.cmd_format
    @pytest.mark.bootloader
    def test_uses_send_command_not_check_success(self, node):
        """AT+BOOT does not return OK; send_command is used directly."""
        with patch("rui3pylib.send_command", return_value=BOOT_RESPONSE) as m_send, \
             patch("rui3pylib.check_success") as m_check:
            node.set_boot_mode()
            m_send.assert_called_once_with(node, "AT+BOOT")
            m_check.assert_not_called()

    @pytest.mark.happy_path
    @pytest.mark.bootloader
    def test_returns_raw_response_string(self, node):
        with patch("rui3pylib.send_command", return_value=BOOT_RESPONSE):
            result = node.set_boot_mode()
        assert result == BOOT_RESPONSE

    @pytest.mark.happy_path
    @pytest.mark.bootloader
    def test_returns_string_type(self, node):
        with patch("rui3pylib.send_command", return_value=BOOT_RESPONSE):
            assert isinstance(node.set_boot_mode(), str)


# ===========================================================================
# AT+VERSION — bootloader version (boot mode only)
# ===========================================================================

class TestGetBootloaderVer:

    @pytest.mark.cmd_format
    @pytest.mark.bootloader
    def test_uses_send_command_not_check_success(self, node):
        with patch("rui3pylib.send_command", return_value=VERSION_RESPONSE) as m_send, \
             patch("rui3pylib.check_success") as m_check:
            node.get_bootloader_ver()
            m_send.assert_called_once_with(node, "AT+VERSION")
            m_check.assert_not_called()

    @pytest.mark.happy_path
    @pytest.mark.bootloader
    def test_returns_version_string(self, node):
        with patch("rui3pylib.send_command", return_value=VERSION_RESPONSE):
            result = node.get_bootloader_ver()
        assert result == VERSION_RESPONSE


# ===========================================================================
# AT+BOOTSTATUS — bootloader status (boot mode only)
# ===========================================================================

class TestGetBootloaderStatus:

    @pytest.mark.cmd_format
    @pytest.mark.bootloader
    def test_sends_at_bootstatus(self, node):
        with patch("rui3pylib.send_command", return_value="Boot Mode\r\n") as m_send:
            node.get_bootloader_status()
            m_send.assert_called_once_with(node, "AT+BOOTSTATUS")

    @pytest.mark.happy_path
    @pytest.mark.bootloader
    def test_returns_status_string(self, node):
        with patch("rui3pylib.send_command", return_value="Boot Mode\r\n"):
            result = node.get_bootloader_status()
        assert "Boot Mode" in result


# ===========================================================================
# AT+RUN — exit boot mode (boot mode only)
# ===========================================================================

class TestAtRun:

    @pytest.mark.cmd_format
    @pytest.mark.bootloader
    def test_sends_at_run(self, node):
        with patch("rui3pylib.send_command", return_value="Stop Boot Mode\r\n") as m:
            node.at_run()
            m.assert_called_once_with(node, "AT+RUN")

    @pytest.mark.happy_path
    @pytest.mark.bootloader
    def test_returns_response_string(self, node):
        with patch("rui3pylib.send_command", return_value="Stop Boot Mode\r\n"):
            result = node.at_run()
        assert isinstance(result, str)


# ===========================================================================
# AT+RESET — device reset from boot mode (boot mode only)
# ===========================================================================

class TestBootReset:

    @pytest.mark.cmd_format
    @pytest.mark.bootloader
    def test_sends_at_reset(self, node):
        with patch("rui3pylib.send_command", return_value="") as m:
            node.boot_reset()
            m.assert_called_once_with(node, "AT+RESET")


# ===========================================================================
# AT+UPDATE — start Y-Modem receive (boot mode only)
# ===========================================================================

class TestBootUpdate:

    @pytest.mark.cmd_format
    @pytest.mark.bootloader
    def test_sends_at_update(self, node):
        with patch("rui3pylib.send_command", return_value="") as m:
            node.boot_update()
            m.assert_called_once_with(node, "AT+UPDATE")

    @pytest.mark.happy_path
    @pytest.mark.bootloader
    def test_returns_string(self, node):
        with patch("rui3pylib.send_command", return_value=""):
            assert isinstance(node.boot_update(), str)
