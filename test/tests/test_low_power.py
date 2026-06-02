"""
tests/test_low_power.py
========================
Tests for the Low Power section of the RUI3 AT command manual.

Covered methods
---------------
at_sleep, get_low_power_mode, set_low_power_mode,
get_low_power_mode_level, set_low_power_mode_level.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

import rui3pylib
from conftest import OK_RESPONSE, ERR_PARAM


# ===========================================================================
# AT+SLEEP — timed sleep mode
# ===========================================================================


class TestAtSleep:
    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    def test_sends_sleep_command_with_duration(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.at_sleep(1000)
            m.assert_called_once_with(node, "AT+SLEEP=1000")

    @pytest.mark.boundary
    @pytest.mark.cmd_format
    def test_minimum_valid_duration_1ms(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.at_sleep(1)
            m.assert_called_once_with(node, "AT+SLEEP=1")
            assert result is not None

    @pytest.mark.boundary
    def test_large_duration_accepted(self, node):
        """2^31 - 1 is within the documented range (up to 2^32 - 1)."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.at_sleep(2_147_483_647)
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_zero_duration_rejected(self, node):
        """Duration < 1 ms is invalid; method returns None without sending AT command."""
        with patch("rui3pylib.check_success") as m:
            result = node.at_sleep(0)
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    def test_negative_duration_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.at_sleep(-100)
            m.assert_not_called()
            assert result is None

    @pytest.mark.device_error
    def test_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.at_sleep(500) is None


# ===========================================================================
# AT+LPM — low-power mode on/off
# ===========================================================================


class TestLowPowerMode:
    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_low_power_mode()
            m.assert_called_once_with(node, "AT+LPM=?")

    @pytest.mark.cmd_format
    def test_set_true_sends_lpm_1(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_low_power_mode(True)
            m.assert_called_once_with(node, "AT+LPM=1")

    @pytest.mark.cmd_format
    def test_set_false_sends_lpm_0(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_low_power_mode(False)
            m.assert_called_once_with(node, "AT+LPM=0")

    @pytest.mark.happy_path
    def test_set_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.set_low_power_mode(True) is not None

    @pytest.mark.device_error
    def test_get_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_low_power_mode() is None

    @pytest.mark.device_error
    def test_set_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_low_power_mode(True) is None

    @pytest.mark.happy_path
    def test_set_truthy_integer_treated_as_on(self, node):
        """Any truthy value (int 1) is encoded as mode=1."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_low_power_mode(1)  # truthy
            m.assert_called_once_with(node, "AT+LPM=1")


# ===========================================================================
# AT+LPMLVL — sleep level (RAK3172 only)
# ===========================================================================


class TestLowPowerModeLevel:
    @pytest.mark.cmd_format
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_low_power_mode_level()
            m.assert_called_once_with(node, "AT+LPMLVL=?")

    @pytest.mark.cmd_format
    def test_set_level_1_sends_stop1(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_low_power_mode_level(1)
            m.assert_called_once_with(node, "AT+LPMLVL=1")

    @pytest.mark.cmd_format
    def test_set_level_2_sends_stop2(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_low_power_mode_level(2)
            m.assert_called_once_with(node, "AT+LPMLVL=2")

    @pytest.mark.happy_path
    def test_set_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.set_low_power_mode_level(1) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_level_0_rejected(self, node):
        """Level 0 is not a valid LPMLVL value (only 1 or 2)."""
        with patch("rui3pylib.check_success") as m:
            result = node.set_low_power_mode_level(0)
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    def test_set_level_3_rejected(self, node):
        """Level 3 exceeds the maximum valid value of 2."""
        with patch("rui3pylib.check_success") as m:
            result = node.set_low_power_mode_level(3)
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    def test_set_level_negative_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_low_power_mode_level(-1)
            m.assert_not_called()
            assert result is None

    @pytest.mark.device_error
    def test_get_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_low_power_mode_level() is None

    @pytest.mark.device_error
    def test_set_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_low_power_mode_level(1) is None
