"""
tests/test_lorawan_join_send.py
=================================
Tests for the LoRaWAN Joining and Sending section.

Covered methods
---------------
get_confirm_mode, set_confirm_mode,
get_confirm_status,
get_join_params, try_join,
get_network_join_mode, set_network_join_mode,
get_network_join_status,
get_last_received_data,
send_data,
send_long_packet_data,
get_confirm_packet_retransmission, set_confirm_packet_retransmission.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

import rui3pylib
from conftest import OK_RESPONSE, ERR_PARAM, ERR_BUSY, ERR_NO_NETWORK


# ===========================================================================
# AT+CFM — confirm mode
# ===========================================================================

class TestConfirmMode:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_confirm_mode()
            m.assert_called_once_with(node, "AT+CFM=?")

    @pytest.mark.cmd_format
    def test_set_true_sends_cfm_1(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_confirm_mode(True)
            m.assert_called_once_with(node, "AT+CFM=1")

    @pytest.mark.cmd_format
    def test_set_false_sends_cfm_0(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_confirm_mode(False)
            m.assert_called_once_with(node, "AT+CFM=0")

    @pytest.mark.device_error
    def test_set_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_confirm_mode(True) is None


# ===========================================================================
# AT+CFS — confirm status (read-only)
# ===========================================================================

class TestConfirmStatus:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_confirm_status()
            m.assert_called_once_with(node, "AT+CFS=?")

    @pytest.mark.device_error
    def test_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_confirm_status() is None


# ===========================================================================
# AT+JOIN — join LoRaWAN network
# ===========================================================================

class TestTryJoin:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_join_params()
            m.assert_called_once_with(node, "AT+JOIN=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_join_with_all_defaults(self, node):
        """Default call: join=True, auto_join=False, interval=8, attempts=0."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.try_join()
            m.assert_called_once_with(node, "AT+JOIN=1:0:8:0")

    @pytest.mark.cmd_format
    def test_join_false_sends_0(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.try_join(join=False)
            m.assert_called_once_with(node, "AT+JOIN=0:0:8:0")

    @pytest.mark.cmd_format
    def test_auto_join_true_sends_1(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.try_join(auto_join=True)
            m.assert_called_once_with(node, "AT+JOIN=1:1:8:0")

    @pytest.mark.cmd_format
    def test_explicit_params_form_correct_cmd(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.try_join(join=True, auto_join=False, interval=10, join_attempts=8)
            m.assert_called_once_with(node, "AT+JOIN=1:0:10:8")

    @pytest.mark.boundary
    def test_minimum_interval_7_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.try_join(interval=7)
            assert result is not None

    @pytest.mark.boundary
    def test_maximum_interval_255_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.try_join(interval=255)
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_interval_6_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.try_join(interval=6)
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_interval_256_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.try_join(interval=256)
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    def test_zero_attempts_accepted(self, node):
        """0 attempts means unlimited retries."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.try_join(join_attempts=0)
            assert result is not None

    @pytest.mark.boundary
    def test_max_attempts_255_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.try_join(join_attempts=255)
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_attempts_256_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.try_join(join_attempts=256)
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_negative_attempts_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.try_join(join_attempts=-1)
            m.assert_not_called()
            assert result is None

    @pytest.mark.device_error
    def test_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_BUSY):
            assert node.try_join() is None


# ===========================================================================
# AT+NJM — network join mode (ABP / OTAA)
# ===========================================================================

class TestNetworkJoinMode:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_network_join_mode()
            m.assert_called_once_with(node, "AT+NJM=?")

    @pytest.mark.cmd_format
    def test_set_abp_mode_0(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_network_join_mode(0)
            m.assert_called_once_with(node, "AT+NJM=0")

    @pytest.mark.cmd_format
    def test_set_otaa_mode_1(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_network_join_mode(1)
            m.assert_called_once_with(node, "AT+NJM=1")

    @pytest.mark.validation
    def test_set_mode_2_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_network_join_mode(2)
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    def test_set_negative_mode_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_network_join_mode(-1)
            m.assert_not_called()
            assert result is None

    @pytest.mark.device_error
    def test_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_network_join_mode(0) is None


# ===========================================================================
# AT+NJS — join status (read-only)
# ===========================================================================

class TestNetworkJoinStatus:

    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_network_join_status()
            m.assert_called_once_with(node, "AT+NJS=?")

    @pytest.mark.device_error
    def test_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_network_join_status() is None


# ===========================================================================
# AT+RECV — last received data (read-only)
# ===========================================================================

class TestGetLastReceivedData:

    @pytest.mark.cmd_format
    def test_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_last_received_data()
            m.assert_called_once_with(node, "AT+RECV=?")


# ===========================================================================
# AT+SEND — send LoRaWAN uplink
# ===========================================================================

class TestSendData:

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_valid_port_and_payload(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.send_data(12, "112233")
            m.assert_called_once_with(node, "AT+SEND=12:112233")
            assert result is not None

    @pytest.mark.boundary
    def test_minimum_port_1_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.send_data(1, "AABB")
            assert result is not None

    @pytest.mark.boundary
    def test_maximum_port_233_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.send_data(233, "AABB")
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_port_0_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.send_data(0, "AABB")
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_port_234_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.send_data(234, "AABB")
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    def test_minimum_payload_2_hex_chars(self, node):
        """Minimum payload is 2 hex chars (1 byte)."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.send_data(1, "AB")
            assert result is not None

    @pytest.mark.boundary
    def test_maximum_payload_500_hex_chars(self, node):
        """Maximum payload is 500 hex chars (250 bytes)."""
        payload = "AB" * 250  # 500 chars, all valid hex
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.send_data(1, payload)
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_payload_1_char_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.send_data(1, "A")
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_payload_502_chars_rejected(self, node):
        """Payload exceeding 500 chars is too long."""
        with patch("rui3pylib.check_success") as m:
            result = node.send_data(1, "AB" * 251)  # 502 chars
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    def test_odd_length_payload_rejected(self, node):
        """Odd-length payload cannot represent whole bytes."""
        with patch("rui3pylib.check_success") as m:
            result = node.send_data(1, "ABC")  # 3 chars = odd
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    def test_non_hex_payload_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.send_data(1, "GGGG")
            m.assert_not_called()
            assert result is None

    @pytest.mark.device_error
    def test_returns_none_when_not_joined(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_NO_NETWORK):
            assert node.send_data(1, "AABB") is None

    @pytest.mark.device_error
    def test_returns_none_on_busy(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_BUSY):
            assert node.send_data(1, "AABB") is None


# ===========================================================================
# AT+LPSEND — long packet send
# ===========================================================================

class TestSendLongPacketData:

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_valid_confirmed_send(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.send_long_packet_data(2, True, "123456")
            m.assert_called_once_with(node, "AT+LPSEND=2:1:123456")
            assert result is not None

    @pytest.mark.cmd_format
    def test_unconfirmed_send_uses_ack_0(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.send_long_packet_data(1, False, "AABB")
            m.assert_called_once_with(node, "AT+LPSEND=1:0:AABB")

    @pytest.mark.boundary
    def test_maximum_payload_2000_hex_chars(self, node):
        """Maximum long-packet payload is 2000 hex chars (1000 bytes)."""
        payload = "AB" * 1000
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.send_long_packet_data(1, False, payload)
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_payload_2002_chars_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.send_long_packet_data(1, False, "AB" * 1001)
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_port_0_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.send_long_packet_data(0, False, "AABB")
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_port_234_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.send_long_packet_data(234, False, "AABB")
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    def test_odd_length_payload_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.send_long_packet_data(1, False, "ABC")
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    def test_non_hex_payload_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.send_long_packet_data(1, False, "ZZZZ")
            m.assert_not_called()
            assert result is None

    @pytest.mark.device_error
    def test_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_BUSY):
            assert node.send_long_packet_data(1, False, "AABB") is None


# ===========================================================================
# AT+RETY — confirmed packet retransmissions
# ===========================================================================

class TestConfirmPacketRetransmission:

    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_confirm_packet_retransmission()
            m.assert_called_once_with(node, "AT+RETY=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_set_valid_value(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_confirm_packet_retransmission(3)
            m.assert_called_once_with(node, "AT+RETY=3")

    @pytest.mark.boundary
    def test_minimum_0_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_confirm_packet_retransmission(0)
            assert result is not None

    @pytest.mark.boundary
    def test_maximum_7_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_confirm_packet_retransmission(7)
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_value_8_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_confirm_packet_retransmission(8)
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_negative_value_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_confirm_packet_retransmission(-1)
            m.assert_not_called()
            assert result is None

    @pytest.mark.device_error
    def test_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_confirm_packet_retransmission(3) is None
