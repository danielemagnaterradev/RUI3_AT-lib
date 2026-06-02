"""
tests/test_class_b_info_regional_multicast.py
==============================================
Tests for four closely related sections of the AT command manual:

    Class B Mode
        get_periodicity / set_periodicity (AT+PGSLOT)
        get_beacon_freq              (AT+BFREQ, read-only)
        get_beacon_time              (AT+BTIME, read-only)
        get_gw_info                  (AT+BGW,   read-only)

    LoRaWAN Information
        get_rssi                     (AT+RSSI,  read-only)
        get_all_channel_rssi         (AT+ARSSI, read-only)
        get_signal_to_noise_ratio    (AT+SNR,   read-only)

    LoRaWAN Regional Commands
        get_mask / set_mask          (AT+MASK)
        get_eight_channel_mode / set_eight_channel_mode   (AT+CHE)
        get_single_channel_mode_freq / set_single_channel_mode_freq (AT+CHS)
        get_freq_band / set_freq_band (AT+BAND)

    LoRaWAN Multicast Group
        set_multicast_group          (AT+ADDMULC)
        remove_multicast_group       (AT+RMVMULC)
        get_multicast_group          (AT+LSTMULC)
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

import rui3pylib
from conftest import OK_RESPONSE, ERR_PARAM, ERR_BUSY


# ── shared keys ─────────────────────────────────────────────────────────────
VALID_ADDR   = "11223344"
VALID_KEY32  = "11223344556677881122334455667788"


# ===========================================================================
# Class B — AT+PGSLOT periodicity (0-7)
# ===========================================================================

class TestPeriodicity:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_periodicity()
            m.assert_called_once_with(node, "AT+PGSLOT=?")

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_minimum_0_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_periodicity(0) is not None
            m.assert_called_once_with(node, "AT+PGSLOT=0")

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_maximum_7_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_periodicity(7) is not None
            m.assert_called_once_with(node, "AT+PGSLOT=7")

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_8_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_periodicity(8) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_negative_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_periodicity(-1) is None
            m.assert_not_called()

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.set_periodicity(0) is None


# ===========================================================================
# Class B — AT+BFREQ, AT+BTIME, AT+BGW (read-only)
# ===========================================================================

class TestClassBReadOnly:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_beacon_freq_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_beacon_freq()
            m.assert_called_once_with(node, "AT+BFREQ=?")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_beacon_time_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_beacon_time()
            m.assert_called_once_with(node, "AT+BTIME=?")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_gw_info_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_gw_info()
            m.assert_called_once_with(node, "AT+BGW=?")

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_get_beacon_freq_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_beacon_freq() is None

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_get_beacon_time_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_beacon_time() is None

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_get_gw_info_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_gw_info() is None


# ===========================================================================
# LoRaWAN Info — AT+RSSI, AT+ARSSI, AT+SNR (all read-only)
# ===========================================================================

class TestLorawanInfo:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_rssi_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_rssi()
            m.assert_called_once_with(node, "AT+RSSI=?")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_all_channel_rssi_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_all_channel_rssi()
            m.assert_called_once_with(node, "AT+ARSSI=?")

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_snr_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_signal_to_noise_ratio()
            m.assert_called_once_with(node, "AT+SNR=?")

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_get_rssi_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_rssi() is None

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_get_all_channel_rssi_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_all_channel_rssi() is None

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_get_snr_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_signal_to_noise_ratio() is None


# ===========================================================================
# AT+MASK — channel mask (4 hex chars)
# ===========================================================================

class TestChannelMask:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_mask()
            m.assert_called_once_with(node, "AT+MASK=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_sub_band_1(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_mask("0001")
            m.assert_called_once_with(node, "AT+MASK=0001")

    @pytest.mark.happy_path
    @pytest.mark.lorawan
    def test_set_all_caps_hex_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_mask("01FF")
            assert result is not None

    @pytest.mark.happy_path
    @pytest.mark.lorawan
    def test_set_all_zeros_accepted(self, node):
        """0000 disables all sub-bands (documented valid value)."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_mask("0000") is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_3_char_mask_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_mask("001") is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_5_char_mask_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_mask("00001") is None
            m.assert_not_called()

    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_non_hex_chars_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_mask("00GG") is None
            m.assert_not_called()

    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_empty_mask_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_mask("") is None
            m.assert_not_called()

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_BUSY):
            assert node.set_mask("0001") is None


# ===========================================================================
# AT+CHE — eight-channel sub-band mode
# ===========================================================================

class TestEightChannelMode:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_eight_channel_mode()
            m.assert_called_once_with(node, "AT+CHE=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_four_subbands(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_eight_channel_mode(1, 2, 3, 4)
            m.assert_called_once_with(node, "AT+CHE=1:2:3:4")

    @pytest.mark.happy_path
    @pytest.mark.lorawan
    def test_set_defaults_all_zero(self, node):
        """Default call (no args) sends AT+CHE=0:0:0:0."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_eight_channel_mode()
            m.assert_called_once_with(node, "AT+CHE=0:0:0:0")

    @pytest.mark.happy_path
    @pytest.mark.lorawan
    def test_set_single_subband_others_zero(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_eight_channel_mode(2, 0, 0, 0)
            m.assert_called_once_with(node, "AT+CHE=2:0:0:0")


# ===========================================================================
# AT+CHS — single-channel mode frequency
# ===========================================================================

class TestSingleChannelMode:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_single_channel_mode_freq()
            m.assert_called_once_with(node, "AT+CHS=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_set_us915_channel_0(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_single_channel_mode_freq(902300000)
            m.assert_called_once_with(node, "AT+CHS=902300000")

    @pytest.mark.happy_path
    @pytest.mark.lorawan
    def test_set_zero_disables_single_channel(self, node):
        """Setting freq=0 disables single-channel mode."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_single_channel_mode_freq(0)
            m.assert_called_once_with(node, "AT+CHS=0")
            assert result is not None


# ===========================================================================
# AT+BAND — frequency band (0-12)
# ===========================================================================

class TestFreqBand:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_freq_band()
            m.assert_called_once_with(node, "AT+BAND=?")

    @pytest.mark.happy_path
    @pytest.mark.lorawan
    @pytest.mark.parametrize("band,name", [
        (0, "EU433"), (1, "CN470"), (2, "RU864"), (3, "IN865"),
        (4, "EU868"), (5, "US915"), (6, "AU915"), (7, "KR920"),
        (8, "AS923-1"), (9, "AS923-2"), (10, "AS923-3"),
        (11, "AS923-4"), (12, "LA915"),
    ])
    def test_all_valid_bands_accepted(self, node, band, name):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_freq_band(band)
            m.assert_called_once_with(node, f"AT+BAND={band}")
            assert result is not None, f"Band {band} ({name}) should be accepted"

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_band_13_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_freq_band(13) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_band_negative_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_freq_band(-1) is None
            m.assert_not_called()

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_returns_none_on_device_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_BUSY):
            assert node.set_freq_band(4) is None


# ===========================================================================
# AT+ADDMULC — add multicast group
# ===========================================================================

class TestSetMulticastGroup:

    def _valid_call(self, node, **overrides):
        kwargs = dict(
            lorawan_class="B",
            dev_addr=VALID_ADDR,
            nwk_s_key=VALID_KEY32,
            app_s_key=VALID_KEY32,
            freq=868000000,
            datarate=0,
            periodicity=0,
        )
        kwargs.update(overrides)
        return kwargs

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_class_b_sends_correct_cmd(self, node):
        expected = (
            f"AT+ADDMULC=B:{VALID_ADDR}:{VALID_KEY32}:{VALID_KEY32}"
            f":868000000:0:0"
        )
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_multicast_group(**self._valid_call(node))
            m.assert_called_once_with(node, expected)

    @pytest.mark.happy_path
    @pytest.mark.lorawan
    def test_class_c_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_multicast_group(**self._valid_call(node, lorawan_class="C"))
            assert result is not None

    @pytest.mark.lorawan
    def test_class_lowercase_uppercased(self, node):
        """Lowercase 'b' is silently uppercased in the AT command."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_multicast_group(**self._valid_call(node, lorawan_class="b"))
            cmd = m.call_args[0][1]
            assert cmd.startswith("AT+ADDMULC=B:")

    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_class_a_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_multicast_group(**self._valid_call(node, lorawan_class="A"))
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_bad_dev_addr_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_multicast_group(**self._valid_call(node, dev_addr="ZZZZ"))
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_short_dev_addr_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_multicast_group(**self._valid_call(node, dev_addr="1122"))
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_bad_nwk_s_key_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_multicast_group(**self._valid_call(node, nwk_s_key="XXXX"))
            m.assert_not_called()
            assert result is None

    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_bad_app_s_key_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_multicast_group(**self._valid_call(node, app_s_key="XXXX"))
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_datarate_8_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_multicast_group(**self._valid_call(node, datarate=8))
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.lorawan
    def test_periodicity_8_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_multicast_group(**self._valid_call(node, periodicity=8))
            m.assert_not_called()
            assert result is None

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_max_valid_datarate_7_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_multicast_group(**self._valid_call(node, datarate=7))
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.lorawan
    def test_max_valid_periodicity_7_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_multicast_group(**self._valid_call(node, periodicity=7))
            assert result is not None


# ===========================================================================
# AT+RMVMULC — remove multicast group
# ===========================================================================

class TestRemoveMulticastGroup:

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_sends_correct_command(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.remove_multicast_group(VALID_ADDR)
            m.assert_called_once_with(node, f"AT+RMVMULC={VALID_ADDR}")

    @pytest.mark.happy_path
    @pytest.mark.lorawan
    def test_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.remove_multicast_group(VALID_ADDR) is not None

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.remove_multicast_group(VALID_ADDR) is None


# ===========================================================================
# AT+LSTMULC — list multicast groups (read-only)
# ===========================================================================

class TestGetMulticastGroup:

    @pytest.mark.cmd_format
    @pytest.mark.lorawan
    def test_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_multicast_group()
            m.assert_called_once_with(node, "AT+LSTMULC=?")

    @pytest.mark.device_error
    @pytest.mark.lorawan
    def test_returns_none_on_failure(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_PARAM):
            assert node.get_multicast_group() is None
