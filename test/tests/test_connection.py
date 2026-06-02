"""
tests/test_connection.py
=========================
Tests for the ``try_connect()`` method and the four legacy P2P getter
commands that were not covered by test_p2p.py.

try_connect()
-------------
The method sends ``AT`` with an extended wait of 5 s and returns a
``bool`` (True on OK, False on any error or exception).  It catches
``serial.serialutil.PortNotOpenError`` to handle the case where the
serial port could not be opened.

Legacy P2P getters (AT+SPREADINGFACTOR=?, AT+CODINGRATE=?,
AT+PREAMBLELENGTH=?, AT+SYMBOLTIMEOUT=?)
These are read-only counterparts of the legacy setter commands already
covered in test_p2p.py::TestP2pLegacyCommands.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

import rui3pylib
from conftest import OK_RESPONSE, ERR_PARAM


# ===========================================================================
# try_connect — AT with 5 s wait, returns bool
# ===========================================================================

class TestTryConnect:
    """
    try_connect() is the *only* public method that:
      1. uses check_success with a non-default wait (5.0 s instead of 3.0 s)
      2. returns a plain bool instead of str | None
      3. catches serial.serialutil.PortNotOpenError and returns False
    """

    @pytest.mark.happy_path
    def test_returns_true_when_device_responds_ok(self, node):
        """Device responds OK → try_connect returns True."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.try_connect()
            assert result is True

    @pytest.mark.happy_path
    def test_returns_false_when_device_does_not_respond(self, node):
        """Device returns an error → try_connect returns False."""
        with patch("rui3pylib.check_success", return_value=("AT_ERROR\r\n", False)):
            result = node.try_connect()
            assert result is False

    @pytest.mark.cmd_format
    def test_sends_bare_at_command(self, node):
        """try_connect must send exactly ``AT`` (the ping command)."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.try_connect()
            args = m.call_args[0]
            assert args[1] == "AT", (
                f"Expected command 'AT', got '{args[1]}'"
            )

    @pytest.mark.cmd_format
    def test_uses_extended_5s_wait(self, node):
        """
        try_connect uses a 5-second timeout to allow for slow boot sequences.
        The third positional argument (or ``wait`` keyword) must be 5.0.
        """
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.try_connect()
            call_args = m.call_args
            positional = call_args[0]    # (self, cmd, wait) if positional
            keyword    = call_args[1]    # {'wait': 5.0} if keyword

            # Accept either positional or keyword form.
            if len(positional) >= 3:
                wait = positional[2]
            else:
                wait = keyword.get("wait")

            assert wait == 5.0, (
                f"Expected wait=5.0, got {wait!r}. "
                "try_connect must use a 5-second timeout."
            )

    @pytest.mark.happy_path
    def test_return_type_is_bool(self, node):
        """try_connect always returns a bool, never str or None."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            result = node.try_connect()
        assert isinstance(result, bool), (
            f"Expected bool, got {type(result).__name__}"
        )

    @pytest.mark.happy_path
    def test_return_type_is_bool_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=("ERROR\r\n", False)):
            result = node.try_connect()
        assert isinstance(result, bool)

    @pytest.mark.device_error
    def test_returns_false_on_port_not_open_error(self, node):
        """
        If the serial port is not open, ``serial.serialutil.PortNotOpenError``
        is caught and try_connect returns False instead of propagating the
        exception.  This is critical for robustness in connection retry loops.
        """
        import serial
        with patch(
            "rui3pylib.check_success",
            side_effect=serial.serialutil.PortNotOpenError,
        ):
            result = node.try_connect()
            assert result is False, (
                "try_connect must return False when the port is not open, "
                "not raise an exception."
            )

    @pytest.mark.device_error
    def test_does_not_propagate_port_not_open_error(self, node):
        """
        The PortNotOpenError must be swallowed entirely; no exception
        should reach the caller.
        """
        import serial
        with patch(
            "rui3pylib.check_success",
            side_effect=serial.serialutil.PortNotOpenError,
        ):
            try:
                node.try_connect()
            except serial.serialutil.PortNotOpenError:
                pytest.fail(
                    "try_connect must not propagate PortNotOpenError. "
                    "It must catch it and return False."
                )

    @pytest.mark.happy_path
    def test_ok_response_maps_to_true(self, node):
        """The bool returned mirrors the ``ok`` flag from check_success."""
        with patch("rui3pylib.check_success", return_value=("\r\nOK\r\n", True)):
            assert node.try_connect() is True

    @pytest.mark.happy_path
    def test_false_ok_flag_maps_to_false(self, node):
        with patch("rui3pylib.check_success", return_value=("AT_BUSY_ERROR\r\n", False)):
            assert node.try_connect() is False


# ===========================================================================
# AT+SPREADINGFACTOR=? — legacy P2P spreading factor getter
# ===========================================================================

class TestGetP2pSpreadFactor:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_spread_factor()
            m.assert_called_once_with(node, "AT+SPREADINGFACTOR=?")

    @pytest.mark.happy_path
    @pytest.mark.p2p
    def test_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.get_p2p_spread_factor() is not None

    @pytest.mark.device_error
    @pytest.mark.p2p
    def test_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_p2p_spread_factor() is None


# ===========================================================================
# AT+CODINGRATE=? — legacy P2P coding rate getter
# ===========================================================================

class TestGetP2pCodingRate:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_coding_rate()
            m.assert_called_once_with(node, "AT+CODINGRATE=?")

    @pytest.mark.happy_path
    @pytest.mark.p2p
    def test_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.get_p2p_coding_rate() is not None

    @pytest.mark.device_error
    @pytest.mark.p2p
    def test_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_p2p_coding_rate() is None


# ===========================================================================
# AT+PREAMBLELENGTH=? — legacy P2P preamble length getter
# ===========================================================================

class TestGetP2pPreambleLength2:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_preamble_length_2()
            m.assert_called_once_with(node, "AT+PREAMBLELENGTH=?")

    @pytest.mark.happy_path
    @pytest.mark.p2p
    def test_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.get_p2p_preamble_length_2() is not None

    @pytest.mark.device_error
    @pytest.mark.p2p
    def test_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_p2p_preamble_length_2() is None


# ===========================================================================
# AT+SYMBOLTIMEOUT=? — legacy P2P symbol timeout getter
# ===========================================================================

class TestGetP2pSymbolTimeout:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_symbol_timeout()
            m.assert_called_once_with(node, "AT+SYMBOLTIMEOUT=?")

    @pytest.mark.happy_path
    @pytest.mark.p2p
    def test_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.get_p2p_symbol_timeout() is not None

    @pytest.mark.device_error
    @pytest.mark.p2p
    def test_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_p2p_symbol_timeout() is None
