"""
tests/test_lorawan_keys.py
===========================
Tests for the LoRaWAN Keys and IDs section.

Covered methods
---------------
get_device_eui, set_device_eui,
get_app_eui, set_app_eui,
get_app_key, set_app_key,
get_dev_addr, set_dev_addr,
get_app_s_key, set_app_s_key,
get_network_s_key, set_network_s_key,
get_network_id, set_network_id,
get_multicast_root_key.

Hex conventions
---------------
All keys / EUIs / addresses are plain ASCII hex strings, MSB first.
No colons, spaces, or 0x prefixes.  The library enforces these rules
before any AT command is sent to the device.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

import rui3pylib
from conftest import OK_RESPONSE, ERR_PARAM


# ── fixtures ────────────────────────────────────────────────────────────────

VALID_EUI_8B   = "1122334455667788"   # 16 hex chars (8 bytes)
VALID_KEY_16B  = "01020AFBA1CD4D20010230405A6B7F88"  # 32 hex chars (16 bytes)
VALID_ADDR_4B  = "01020A0B"           # 8 hex chars (4 bytes)
VALID_NETID    = "000001"             # 6 hex chars (3 bytes)

INVALID_SHORT_EUI   = "112233445566778"   # 15 chars
INVALID_LONG_EUI    = "11223344556677889"  # 17 chars
INVALID_HEX_EUI     = "112233445566GGGG"  # 'G' not hex
INVALID_SHORT_KEY   = "01020AFBA1CD4D20010230405A6B7F"  # 30 chars
INVALID_LONG_KEY    = "01020AFBA1CD4D20010230405A6B7F8899"  # 34 chars
INVALID_HEX_KEY     = "01020AFBA1CD4D20010230405A6B7FGG"
INVALID_SHORT_ADDR  = "01020A"        # 6 chars
INVALID_LONG_ADDR   = "01020A0B0C"    # 10 chars
INVALID_HEX_ADDR    = "0102GG0B"
INVALID_SHORT_NETID = "0000"          # 4 chars
INVALID_LONG_NETID  = "00000100"      # 8 chars
INVALID_HEX_NETID   = "0000GG"


def _check_setter_valid(node, method: str, value: str, expected_cmd: str):
    with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
        result = getattr(node, method)(value)
        m.assert_called_once_with(node, expected_cmd)
        assert result is not None


def _check_setter_invalid(node, method: str, value: str):
    """Invalid value → no AT command sent, returns None."""
    with patch("rui3pylib.check_success") as m:
        result = getattr(node, method)(value)
        m.assert_not_called()
        assert result is None


def _check_getter(node, method: str, expected_cmd: str):
    with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
        result = getattr(node, method)()
        m.assert_called_once_with(node, expected_cmd)
        assert result is not None


# ===========================================================================
# AT+DEVEUI — device EUI (OTAA)
# ===========================================================================

class TestDeviceEui:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        _check_getter(node, "get_device_eui", "AT+DEVEUI=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_set_valid_eui(self, node):
        _check_setter_valid(node, "set_device_eui", VALID_EUI_8B,
                            f"AT+DEVEUI={VALID_EUI_8B}")

    @pytest.mark.happy_path
    def test_set_lowercase_hex_accepted(self, node):
        eui = "1122334455667788"
        _check_setter_valid(node, "set_device_eui", eui, f"AT+DEVEUI={eui}")

    @pytest.mark.happy_path
    def test_set_uppercase_hex_accepted(self, node):
        eui = "AABBCCDDEEFF0011"
        _check_setter_valid(node, "set_device_eui", eui, f"AT+DEVEUI={eui}")

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_15_char_eui_rejected(self, node):
        _check_setter_invalid(node, "set_device_eui", INVALID_SHORT_EUI)

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_17_char_eui_rejected(self, node):
        _check_setter_invalid(node, "set_device_eui", INVALID_LONG_EUI)

    @pytest.mark.validation
    def test_set_non_hex_chars_rejected(self, node):
        _check_setter_invalid(node, "set_device_eui", INVALID_HEX_EUI)

    @pytest.mark.validation
    def test_set_empty_string_rejected(self, node):
        _check_setter_invalid(node, "set_device_eui", "")

    @pytest.mark.device_error
    def test_get_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_device_eui() is None

    @pytest.mark.device_error
    def test_set_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_device_eui(VALID_EUI_8B) is None


# ===========================================================================
# AT+APPEUI — application EUI / JoinEUI (OTAA)
# ===========================================================================

class TestAppEui:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        _check_getter(node, "get_app_eui", "AT+APPEUI=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_set_valid_eui(self, node):
        eui = "0102030405060708"
        _check_setter_valid(node, "set_app_eui", eui, f"AT+APPEUI={eui}")

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_15_char_eui_rejected(self, node):
        _check_setter_invalid(node, "set_app_eui", INVALID_SHORT_EUI)

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_17_char_eui_rejected(self, node):
        _check_setter_invalid(node, "set_app_eui", INVALID_LONG_EUI)

    @pytest.mark.validation
    def test_set_non_hex_chars_rejected(self, node):
        _check_setter_invalid(node, "set_app_eui", INVALID_HEX_EUI)

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_18_char_eui_rejected(self, node):
        """One extra byte (18 hex chars) must be rejected."""
        _check_setter_invalid(node, "set_app_eui", "010203040506070809")

    @pytest.mark.device_error
    def test_set_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_app_eui(VALID_EUI_8B) is None


# ===========================================================================
# AT+APPKEY — application key (OTAA)
# ===========================================================================

class TestAppKey:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        _check_getter(node, "get_app_key", "AT+APPKEY=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_set_valid_key(self, node):
        _check_setter_valid(node, "set_app_key", VALID_KEY_16B,
                            f"AT+APPKEY={VALID_KEY_16B}")

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_30_char_key_rejected(self, node):
        _check_setter_invalid(node, "set_app_key", INVALID_SHORT_KEY)

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_34_char_key_rejected(self, node):
        _check_setter_invalid(node, "set_app_key", INVALID_LONG_KEY)

    @pytest.mark.validation
    def test_set_non_hex_chars_rejected(self, node):
        _check_setter_invalid(node, "set_app_key", INVALID_HEX_KEY)

    @pytest.mark.validation
    def test_set_empty_string_rejected(self, node):
        _check_setter_invalid(node, "set_app_key", "")

    @pytest.mark.device_error
    def test_set_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_app_key(VALID_KEY_16B) is None


# ===========================================================================
# AT+DEVADDR — device address (ABP)
# ===========================================================================

class TestDevAddr:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        _check_getter(node, "get_dev_addr", "AT+DEVADDR=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_set_valid_address(self, node):
        _check_setter_valid(node, "set_dev_addr", VALID_ADDR_4B,
                            f"AT+DEVADDR={VALID_ADDR_4B}")

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_6_char_address_rejected(self, node):
        _check_setter_invalid(node, "set_dev_addr", INVALID_SHORT_ADDR)

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_10_char_address_rejected(self, node):
        _check_setter_invalid(node, "set_dev_addr", INVALID_LONG_ADDR)

    @pytest.mark.validation
    def test_set_non_hex_chars_rejected(self, node):
        _check_setter_invalid(node, "set_dev_addr", INVALID_HEX_ADDR)

    @pytest.mark.device_error
    def test_set_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_dev_addr(VALID_ADDR_4B) is None


# ===========================================================================
# AT+APPSKEY — application session key (ABP)
# ===========================================================================

class TestAppSKey:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        _check_getter(node, "get_app_s_key", "AT+APPSKEY=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_set_valid_key(self, node):
        _check_setter_valid(node, "set_app_s_key", VALID_KEY_16B,
                            f"AT+APPSKEY={VALID_KEY_16B}")

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_30_char_key_rejected(self, node):
        _check_setter_invalid(node, "set_app_s_key", INVALID_SHORT_KEY)

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_34_char_key_rejected(self, node):
        _check_setter_invalid(node, "set_app_s_key", INVALID_LONG_KEY)

    @pytest.mark.validation
    def test_set_non_hex_chars_rejected(self, node):
        _check_setter_invalid(node, "set_app_s_key", INVALID_HEX_KEY)

    @pytest.mark.device_error
    def test_set_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_app_s_key(VALID_KEY_16B) is None


# ===========================================================================
# AT+NWKSKEY — network session key (ABP)
# ===========================================================================

class TestNetworkSKey:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        _check_getter(node, "get_network_s_key", "AT+NWKSKEY=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_set_valid_key(self, node):
        _check_setter_valid(node, "set_network_s_key", VALID_KEY_16B,
                            f"AT+NWKSKEY={VALID_KEY_16B}")

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_30_char_key_rejected(self, node):
        _check_setter_invalid(node, "set_network_s_key", INVALID_SHORT_KEY)

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_34_char_key_rejected(self, node):
        _check_setter_invalid(node, "set_network_s_key", INVALID_LONG_KEY)

    @pytest.mark.validation
    def test_set_non_hex_chars_rejected(self, node):
        _check_setter_invalid(node, "set_network_s_key", INVALID_HEX_KEY)

    @pytest.mark.device_error
    def test_set_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_network_s_key(VALID_KEY_16B) is None


# ===========================================================================
# AT+NETID — network identifier (3 bytes)
# ===========================================================================

class TestNetworkId:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        _check_getter(node, "get_network_id", "AT+NETID=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_set_valid_netid(self, node):
        _check_setter_valid(node, "set_network_id", VALID_NETID,
                            f"AT+NETID={VALID_NETID}")

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_4_char_netid_rejected(self, node):
        _check_setter_invalid(node, "set_network_id", INVALID_SHORT_NETID)

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_8_char_netid_rejected(self, node):
        _check_setter_invalid(node, "set_network_id", INVALID_LONG_NETID)

    @pytest.mark.validation
    def test_set_non_hex_chars_rejected(self, node):
        _check_setter_invalid(node, "set_network_id", INVALID_HEX_NETID)

    @pytest.mark.device_error
    def test_set_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_network_id(VALID_NETID) is None


# ===========================================================================
# AT+MCROOTKEY — multicast root key (read-only)
# ===========================================================================

class TestMulticastRootKey:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        _check_getter(node, "get_multicast_root_key", "AT+MCROOTKEY=?")

    @pytest.mark.device_error
    def test_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_multicast_root_key() is None

    def test_no_setter_exists(self, node):
        """AT+MCROOTKEY is read-only; there must be no setter method."""
        assert not hasattr(node, "set_multicast_root_key"), \
            "set_multicast_root_key should not exist (read-only command)"
