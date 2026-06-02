"""
tests/test_lorawan_network_mgmt.py
====================================
Tests for the LoRaWAN Network Management section.

Covered methods
---------------
get_adaptive_rate, set_adaptive_rate,
get_lorawan_class, set_lorawan_class,
get_duty_cycle, set_duty_cycle,
get_data_rate, set_data_rate,
get_join_delay_rx_window_1, set_join_delay_rx_window_1,
get_join_delay_rx_window_2, set_join_delay_rx_window_2,
get_public_network_mode, set_public_network_mode,
get_receive_window_1_delay, set_receive_window_1_delay,
get_receive_window_2_delay, set_receive_window_2_delay,
get_receive_window_2_data_rate, set_receive_window_2_data_rate,
get_receive_window_2_freq, set_receive_window_2_freq,
get_transmit_power, set_transmit_power,
get_link_check, set_link_check,
get_listen_before_talk, set_listen_before_talk,
get_listen_before_talk_rssi, set_listen_before_talk_rssi,
get_listen_before_talk_scan_time, set_listen_before_talk_scan_time,
get_time_req, set_time_req,
get_local_time.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

import rui3pylib
from conftest import OK_RESPONSE, ERR_PARAM, ERR_BUSY


# ===========================================================================
# AT+ADR — adaptive data rate
# ===========================================================================

class TestAdaptiveRate:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_adaptive_rate()
            m.assert_called_once_with(node, "AT+ADR=?")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_true_sends_adr_1(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_adaptive_rate(True)
            m.assert_called_once_with(node, "AT+ADR=1")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_false_sends_adr_0(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_adaptive_rate(False)
            m.assert_called_once_with(node, "AT+ADR=0")

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_set_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_adaptive_rate(True) is None


# ===========================================================================
# AT+CLASS — LoRaWAN device class
# ===========================================================================

class TestLorawanClass:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_lorawan_class()
            m.assert_called_once_with(node, "AT+CLASS=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_class_a(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_lorawan_class("A")
            m.assert_called_once_with(node, "AT+CLASS=A")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_class_b(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_lorawan_class("B")
            m.assert_called_once_with(node, "AT+CLASS=B")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_class_c(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_lorawan_class("C")
            m.assert_called_once_with(node, "AT+CLASS=C")

    @pytest.mark.happy_path
    @pytest.mark.lorawan
    def test_set_lowercase_is_uppercased(self, node):
        """Lowercase input is silently uppercased before sending."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_lorawan_class("a")
            m.assert_called_once_with(node, "AT+CLASS=A")

    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_set_invalid_class_d_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_lorawan_class("D")
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_set_empty_string_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_lorawan_class("")
            m.assert_not_called()
            assert result is None

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_set_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_lorawan_class("A") is None


# ===========================================================================
# AT+DCS — duty cycle
# ===========================================================================

class TestDutyCycle:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_duty_cycle()
            m.assert_called_once_with(node, "AT+DCS=?")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_true_enables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_duty_cycle(True)
            m.assert_called_once_with(node, "AT+DCS=1")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_false_disables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_duty_cycle(False)
            m.assert_called_once_with(node, "AT+DCS=0")

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_set_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_duty_cycle(True) is None


# ===========================================================================
# AT+DR — data rate index
# ===========================================================================

class TestDataRate:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_data_rate()
            m.assert_called_once_with(node, "AT+DR=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_dr3(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_data_rate(3)
            m.assert_called_once_with(node, "AT+DR=3")

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_minimum_dr0_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_data_rate(0) is not None

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_maximum_dr7_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_data_rate(7) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_dr8_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_data_rate(8) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_negative_dr_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_data_rate(-1) is None
            m.assert_not_called()

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_set_returns_none_on_device_error(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_data_rate(3) is None


# ===========================================================================
# AT+JN1DL — join accept delay RX1 (1-14 s)
# ===========================================================================

class TestJoinDelayRx1:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_join_delay_rx_window_1()
            m.assert_called_once_with(node, "AT+JN1DL=?")

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_minimum_1s_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_join_delay_rx_window_1(1) is not None
            m.assert_called_once_with(node, "AT+JN1DL=1")

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_maximum_14s_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_join_delay_rx_window_1(14) is not None
            m.assert_called_once_with(node, "AT+JN1DL=14")

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_zero_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_join_delay_rx_window_1(0) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_15_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_join_delay_rx_window_1(15) is None
            m.assert_not_called()

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_returns_none_on_busy(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_BUSY):
            assert node.set_join_delay_rx_window_1(5) is None


# ===========================================================================
# AT+JN2DL — join accept delay RX2 (2-15 s)
# ===========================================================================

class TestJoinDelayRx2:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_join_delay_rx_window_2()
            m.assert_called_once_with(node, "AT+JN2DL=?")

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_minimum_2s_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_join_delay_rx_window_2(2) is not None

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_maximum_15s_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_join_delay_rx_window_2(15) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_1_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_join_delay_rx_window_2(1) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_16_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_join_delay_rx_window_2(16) is None
            m.assert_not_called()


# ===========================================================================
# AT+PNM — public network mode
# ===========================================================================

class TestPublicNetworkMode:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_public_network_mode()
            m.assert_called_once_with(node, "AT+PNM=?")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_true(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_public_network_mode(True)
            m.assert_called_once_with(node, "AT+PNM=1")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_false(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_public_network_mode(False)
            m.assert_called_once_with(node, "AT+PNM=0")


# ===========================================================================
# AT+RX1DL — RX1 window delay (1-15 s)
# ===========================================================================

class TestRx1Delay:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_receive_window_1_delay()
            m.assert_called_once_with(node, "AT+RX1DL=?")

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_minimum_1_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_receive_window_1_delay(1) is not None
            m.assert_called_once_with(node, "AT+RX1DL=1")

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_maximum_15_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_receive_window_1_delay(15) is not None
            m.assert_called_once_with(node, "AT+RX1DL=15")

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_zero_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_receive_window_1_delay(0) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_16_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_receive_window_1_delay(16) is None
            m.assert_not_called()


# ===========================================================================
# AT+RX2DL — RX2 window delay (2-15 s)
# ===========================================================================

class TestRx2Delay:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_receive_window_2_delay()
            m.assert_called_once_with(node, "AT+RX2DL=?")

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_minimum_2_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_receive_window_2_delay(2) is not None

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_maximum_15_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_receive_window_2_delay(15) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_1_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_receive_window_2_delay(1) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_16_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_receive_window_2_delay(16) is None
            m.assert_not_called()


# ===========================================================================
# AT+RX2DR — RX2 data rate ([0-7] or [8-13])
# ===========================================================================

class TestRx2DataRate:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_receive_window_2_data_rate()
            m.assert_called_once_with(node, "AT+RX2DR=?")

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_eu_range_0_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_receive_window_2_data_rate(0) is not None

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_eu_range_7_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_receive_window_2_data_rate(7) is not None

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_us_range_8_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_receive_window_2_data_rate(8) is not None

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_us_range_13_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_receive_window_2_data_rate(13) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_14_rejected(self, node):
        """Value 14 falls outside both valid ranges ([0-7] and [8-13])."""
        with patch("rui3pylib.check_success") as m:
            assert node.set_receive_window_2_data_rate(14) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_negative_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_receive_window_2_data_rate(-1) is None
            m.assert_not_called()


# ===========================================================================
# AT+RX2FQ — RX2 frequency (read-only)
# ===========================================================================

class TestRx2Freq:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_receive_window_2_freq()
            m.assert_called_once_with(node, "AT+RX2FQ=?")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_freq(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_receive_window_2_freq(869525000)
            m.assert_called_once_with(node, "AT+RX2FQ=869525000")


# ===========================================================================
# AT+TXP — transmit power (0-14)
# ===========================================================================

class TestTransmitPower:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_transmit_power()
            m.assert_called_once_with(node, "AT+TXP=?")

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_minimum_0_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_transmit_power(0) is not None
            m.assert_called_once_with(node, "AT+TXP=0")

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_maximum_14_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_transmit_power(14) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_15_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_transmit_power(15) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_negative_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_transmit_power(-1) is None
            m.assert_not_called()


# ===========================================================================
# AT+LINKCHECK — link check mode (0, 1, 2)
# ===========================================================================

class TestLinkCheck:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_link_check()
            m.assert_called_once_with(node, "AT+LINKCHECK=?")

    @pytest.mark.happy_path
    @pytest.mark.lorawan
    @pytest.mark.parametrize("value,expected", [
        (0, "AT+LINKCHECK=0"),
        (1, "AT+LINKCHECK=1"),
        (2, "AT+LINKCHECK=2"),
    ])
    def test_set_valid_values(self, node, value, expected):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_link_check(value)
            m.assert_called_once_with(node, expected)
            assert result is not None

    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_set_3_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_link_check(3) is None
            m.assert_not_called()

    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_set_negative_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_link_check(-1) is None
            m.assert_not_called()


# ===========================================================================
# AT+LBT — Listen Before Talk on/off
# ===========================================================================

class TestListenBeforeTalk:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_listen_before_talk()
            m.assert_called_once_with(node, "AT+LBT=?")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_true_enables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_listen_before_talk(True)
            m.assert_called_once_with(node, "AT+LBT=1")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_false_disables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_listen_before_talk(False)
            m.assert_called_once_with(node, "AT+LBT=0")


# ===========================================================================
# AT+LBTRSSI — LBT RSSI threshold
# ===========================================================================

class TestListenBeforeTalkRssi:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_listen_before_talk_rssi()
            m.assert_called_once_with(node, "AT+LBTRSSI=?")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_negative_rssi(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_listen_before_talk_rssi(-80)
            m.assert_called_once_with(node, "AT+LBTRSSI=-80")

    @pytest.mark.happy_path
    @pytest.mark.lorawan
    def test_set_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.set_listen_before_talk_rssi(-80) is not None


# ===========================================================================
# AT+LBTSCANTIME — LBT scan time
# ===========================================================================

class TestListenBeforeTalkScanTime:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_listen_before_talk_scan_time()
            m.assert_called_once_with(node, "AT+LBTSCANTIME=?")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_scan_time(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_listen_before_talk_scan_time(5)
            m.assert_called_once_with(node, "AT+LBTSCANTIME=5")


# ===========================================================================
# AT+TIMEREQ — time request
# ===========================================================================

class TestTimeReq:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_time_req()
            m.assert_called_once_with(node, "AT+TIMEREQ=?")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_true_enables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_time_req(True)
            m.assert_called_once_with(node, "AT+TIMEREQ=1")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_false_disables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_time_req(False)
            m.assert_called_once_with(node, "AT+TIMEREQ=0")


# ===========================================================================
# AT+LTIME — local time (read-only)
# ===========================================================================

class TestLocalTime:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_local_time()
            m.assert_called_once_with(node, "AT+LTIME=?")

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_local_time() is None
