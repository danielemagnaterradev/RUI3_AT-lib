"""
tests/test_rf_test.py
======================
Tests for the RF Test / Certification section.

Covered methods
---------------
rf_rssi_test                        (AT+TRSSI=?)
rf_tone_test                        (AT+TTONE)
set_rf_tx_test_packet_number        (AT+TTX=<n>)
set_rf_rx_test_packet_number        (AT+TRX=<n>)
set_rf_test_config                  (AT+TCONF=...)
rf_tone_hopping_test                (AT+TTH=...)
rf_test_stop                        (AT+TOFF)
rf_certification_test               (AT+CERTIF)
rf_continuous_wave_test             (AT+CW=...)
rf_tx_fhss_hopping_test             (AT+TRTH=...)

Notes
-----
AT+TCONF has an important encoding quirk:
    - Coding rate is **1-based** (1=4/5, 2=4/6, 3=4/7, 4=4/8), unlike AT+PCR
      which is 0-based.
    - Bandwidth is **modulation-dependent**: index 0-9 in LoRa mode, Hz value
      4800-467000 in FSK mode.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

import rui3pylib
from conftest import OK_RESPONSE, ERR_PARAM, ERR_BUSY


# Shared valid TCONF parameters
VALID_LORA_TCONF = dict(
    freq=868000000, power=14, bw=0, sf=7, cr=1, lna=0,
    pa_boost=0, modulation=1, payload_len=4, fdev=25000,
    lowdropt=0, bt=0,
)


# ===========================================================================
# AT+TRSSI=? — RF RSSI tone test (read)
# ===========================================================================

class TestRfRssiTest:

    @pytest.mark.cmd_format
    @pytest.mark.rf_test
    def test_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.rf_rssi_test()
            m.assert_called_once_with(node, "AT+TRSSI=?")

    @pytest.mark.happy_path
    @pytest.mark.rf_test
    def test_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.rf_rssi_test() is not None

    @pytest.mark.device_error
    @pytest.mark.rf_test
    def test_returns_none_on_busy(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_BUSY):
            assert node.rf_rssi_test() is None


# ===========================================================================
# AT+TTONE — RF tone test
# ===========================================================================

class TestRfToneTest:

    @pytest.mark.cmd_format
    @pytest.mark.rf_test
    def test_sends_correct_command(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.rf_tone_test()
            m.assert_called_once_with(node, "AT+TTONE")

    @pytest.mark.happy_path
    @pytest.mark.rf_test
    def test_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.rf_tone_test() is not None

    @pytest.mark.device_error
    @pytest.mark.rf_test
    def test_returns_none_on_busy(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_BUSY):
            assert node.rf_tone_test() is None


# ===========================================================================
# AT+TTX=<n> — RF TX test
# ===========================================================================

class TestRfTxTestPacketNumber:

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.rf_test
    def test_sends_correct_command(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_rf_tx_test_packet_number(4)
            m.assert_called_once_with(node, "AT+TTX=4")

    @pytest.mark.happy_path
    @pytest.mark.rf_test
    def test_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.set_rf_tx_test_packet_number(10) is not None

    @pytest.mark.device_error
    @pytest.mark.rf_test
    def test_returns_none_on_busy(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_BUSY):
            assert node.set_rf_tx_test_packet_number(4) is None


# ===========================================================================
# AT+TRX=<n> — RF RX test
# ===========================================================================

class TestRfRxTestPacketNumber:

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.rf_test
    def test_sends_correct_command(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_rf_rx_test_packet_number(4)
            m.assert_called_once_with(node, "AT+TRX=4")

    @pytest.mark.happy_path
    @pytest.mark.rf_test
    def test_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.set_rf_rx_test_packet_number(4) is not None


# ===========================================================================
# AT+TCONF — RF test configuration
# ===========================================================================

class TestSetRfTestConfig:

    def _call(self, node, **overrides):
        kwargs = dict(VALID_LORA_TCONF)
        kwargs.update(overrides)
        return node.set_rf_test_config(**kwargs)

    # ── happy path ───────────────────────────────────────────────────────────

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.rf_test
    def test_lora_valid_config_builds_correct_cmd(self, node):
        expected = "AT+TCONF=868000000:14:0:7:1:0:0:1:4:25000:0:0"
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            self._call(node)
            m.assert_called_once_with(node, expected)

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.rf_test
    def test_doc_example_config_accepted(self, node):
        """Example from documentation: AT+TCONF=868000000:14:4:12:1:0:0:1:16:25000:2:3"""
        expected = "AT+TCONF=868000000:14:4:12:1:0:0:1:16:25000:2:3"
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_rf_test_config(
                freq=868000000, power=14, bw=4, sf=12, cr=1,
                lna=0, pa_boost=0, modulation=1, payload_len=16,
                fdev=25000, lowdropt=2, bt=3,
            )
            m.assert_called_once_with(node, expected)

    # ── frequency ────────────────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_min_freq_150mhz_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, freq=150000000) is not None

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_max_freq_960mhz_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, freq=960000000) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_freq_below_min_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, freq=149999999) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_freq_above_max_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, freq=960000001) is None
            m.assert_not_called()

    # ── power ────────────────────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_min_power_5dbm_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, power=5) is not None

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_max_power_22dbm_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, power=22) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_power_4_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, power=4) is None
            m.assert_not_called()

    # ── modulation ───────────────────────────────────────────────────────────

    @pytest.mark.happy_path
    @pytest.mark.rf_test
    def test_fsk_modulation_0_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_rf_test_config(
                freq=868000000, power=14, bw=9600, sf=7, cr=1,
                lna=0, pa_boost=0, modulation=0,   # FSK
                payload_len=4, fdev=5000, lowdropt=0, bt=0,
            )
            assert result is not None

    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_modulation_2_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, modulation=2) is None
            m.assert_not_called()

    # ── bandwidth: LoRa mode (index 0-9) ────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_lora_bw_min_0_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, bw=0, modulation=1) is not None

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_lora_bw_max_9_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, bw=9, modulation=1) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_lora_bw_10_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, bw=10, modulation=1) is None
            m.assert_not_called()

    # ── bandwidth: FSK mode (Hz, 4800-467000) ────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_fsk_bw_min_4800hz_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_rf_test_config(
                freq=868000000, power=14, bw=4800, sf=7, cr=1,
                lna=0, pa_boost=0, modulation=0, payload_len=4,
                fdev=5000, lowdropt=0, bt=0,
            )
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_fsk_bw_4799hz_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.set_rf_test_config(
                freq=868000000, power=14, bw=4799, sf=7, cr=1,
                lna=0, pa_boost=0, modulation=0, payload_len=4,
                fdev=5000, lowdropt=0, bt=0,
            )
            assert result is None
            m.assert_not_called()

    # ── spreading factor ─────────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_sf_min_5_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, sf=5) is not None

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_sf_max_12_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, sf=12) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_sf_4_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, sf=4) is None
            m.assert_not_called()

    # ── coding rate: 1-based (1-4) ───────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.rf_test
    @pytest.mark.parametrize("cr", [1, 2, 3, 4])
    def test_all_valid_cr_values_accepted(self, node, cr):
        """AT+TCONF coding rate is 1-based (1=4/5, 2=4/6, 3=4/7, 4=4/8)."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, cr=cr) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_cr_0_rejected(self, node):
        """
        Unlike AT+PCR (0-based), AT+TCONF coding rate is 1-based.
        Passing cr=0 must be rejected.
        """
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, cr=0) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_cr_5_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, cr=5) is None
            m.assert_not_called()

    # ── payload length ────────────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_payload_min_1_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, payload_len=1) is not None

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_payload_max_255_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, payload_len=255) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_payload_0_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, payload_len=0) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_payload_256_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, payload_len=256) is None
            m.assert_not_called()

    # ── FSK frequency deviation ──────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_fdev_min_600hz_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, fdev=600) is not None

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_fdev_max_200000hz_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert self._call(node, fdev=200000) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_fdev_599hz_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, fdev=599) is None
            m.assert_not_called()

    # ── lna / pa_boost flags ──────────────────────────────────────────────────

    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_lna_2_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, lna=2) is None
            m.assert_not_called()

    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_pa_boost_2_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert self._call(node, pa_boost=2) is None
            m.assert_not_called()


# ===========================================================================
# AT+TTH — RF TX hopping test (sequential)
# ===========================================================================

class TestRfToneHoppingTest:

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.rf_test
    def test_sends_correct_command(self, node):
        expected = "AT+TTH=868000000:868500000:100000:6"
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.rf_tone_hopping_test(868000000, 868500000, 100000, 6)
            m.assert_called_once_with(node, expected)

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_minimum_fstart_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.rf_tone_hopping_test(150000000, 150100000, 100000, 1)
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_fstop_equal_to_fstart_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.rf_tone_hopping_test(868000000, 868000000, 100000, 6)
            assert result is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_fstop_less_than_fstart_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.rf_tone_hopping_test(868500000, 868000000, 100000, 6)
            assert result is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_zero_fdelta_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.rf_tone_hopping_test(868000000, 868500000, 0, 6)
            assert result is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_zero_packets_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.rf_tone_hopping_test(868000000, 868500000, 100000, 0)
            assert result is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_fstart_below_150mhz_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            result = node.rf_tone_hopping_test(149999999, 868000000, 100000, 6)
            assert result is None
            m.assert_not_called()


# ===========================================================================
# AT+TOFF — stop RF test
# ===========================================================================

class TestRfTestStop:

    @pytest.mark.cmd_format
    @pytest.mark.rf_test
    def test_sends_correct_command(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.rf_test_stop()
            m.assert_called_once_with(node, "AT+TOFF")

    @pytest.mark.happy_path
    @pytest.mark.rf_test
    def test_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.rf_test_stop() is not None


# ===========================================================================
# AT+CERTIF — LoRaWAN certification mode
# ===========================================================================

class TestRfCertificationTest:

    @pytest.mark.cmd_format
    @pytest.mark.rf_test
    def test_sends_correct_command(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.rf_certification_test()
            m.assert_called_once_with(node, "AT+CERTIF")

    @pytest.mark.device_error
    @pytest.mark.rf_test
    def test_returns_none_on_busy(self, node):
        with patch("rui3pylib.check_success", return_value=ERR_BUSY):
            assert node.rf_certification_test() is None


# ===========================================================================
# AT+CW — continuous wave test
# ===========================================================================

class TestRfContinuousWaveTest:

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.rf_test
    def test_sends_correct_command(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.rf_continuous_wave_test(868000000, 14, 5000)
            m.assert_called_once_with(node, "AT+CW=868000000:14:5000")

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_zero_time_continuous(self, node):
        """time_ms=0 means transmit continuously until TOFF is called."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.rf_continuous_wave_test(868000000, 14, 0)
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_max_time_65535ms_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.rf_continuous_wave_test(868000000, 14, 65535)
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_time_65536ms_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.rf_continuous_wave_test(868000000, 14, 65536) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_freq_below_min_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.rf_continuous_wave_test(149999999, 14, 5000) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_power_4_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.rf_continuous_wave_test(868000000, 4, 5000) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_power_23_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.rf_continuous_wave_test(868000000, 23, 5000) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_negative_time_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.rf_continuous_wave_test(868000000, 14, -1) is None
            m.assert_not_called()


# ===========================================================================
# AT+TRTH — FHSS (random-order) TX hopping test
# ===========================================================================

class TestRfTxFhssHoppingTest:

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.rf_test
    def test_sends_correct_command(self, node):
        expected = "AT+TRTH=868000000:868500000:100000:6"
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.rf_tx_fhss_hopping_test(868000000, 868500000, 100000, 6)
            m.assert_called_once_with(node, expected)

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_end_equal_start_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.rf_tx_fhss_hopping_test(868000000, 868000000, 100000, 6) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_zero_hop_step_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.rf_tx_fhss_hopping_test(868000000, 868500000, 0, 6) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_zero_hop_count_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.rf_tx_fhss_hopping_test(868000000, 868500000, 100000, 0) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_start_freq_below_150mhz_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.rf_tx_fhss_hopping_test(149999999, 868000000, 100000, 6) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.rf_test
    def test_end_freq_above_960mhz_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.rf_tx_fhss_hopping_test(868000000, 960000001, 100000, 6) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.rf_test
    def test_minimum_hop_count_1_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.rf_tx_fhss_hopping_test(868000000, 868100000, 100000, 1)
            assert result is not None
