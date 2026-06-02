"""
tests/test_p2p.py
==================
Tests for the P2P (Point-to-Point) LoRa command section.

Covered methods
---------------
get_lora_network_mode / set_lora_network_mode   (AT+NWM)
get_p2p_freq / set_p2p_freq                     (AT+PFREQ)
get_spread_factor / set_spread_factor            (AT+PSF)
get_p2p_band / set_p2p_band                     (AT+PBW)
get_p2p_code_rate / set_p2p_code_rate           (AT+PCR)
get_p2p_preamble_length / set_p2p_preamble_length (AT+PPL)
get_p2p_tx_power / set_p2p_tx_power             (AT+PTP)
get_p2p_fsk_bitrate / set_p2p_fsk_bitrate       (AT+PBR)
get_p2p_freq_deviation / set_p2p_freq_deviation (AT+PFDEV)
p2p_send                                         (AT+PSEND)
get_p2p_channel_activity / set_p2p_channel_activity (AT+CAD)
p2p_receive                                      (AT+PRECV)
get_p2p_encryption / set_p2p_encryption         (AT+ENCRY)
get_p2p_encryption_key / set_p2p_encryption_key (AT+ENCKEY)
get_p2p_crypt_status / set_p2p_crypt_status     (AT+PCRYPT)
get_p2p_crypt_decrypt_key / set_p2p_crypt_decrypt_key (AT+PKEY)
get_p2p_crypt_iv / set_p2p_crypt_iv             (AT+CRYPIV)
get_p2p_params / set_p2p_params                 (AT+P2P)
get_p2p_iq_inv / set_p2p_iq_inv                 (AT+IQINVER)
get_p2p_syncword / set_p2p_syncword             (AT+SYNCWORD)
get_p2p_rf_freq / set_p2p_rf_freq               (AT+RFFREQUENCY)
get_p2p_tx_out_power / set_p2p_tx_out_power     (AT+TXOUTPUTPOWER)
get_p2p_bandwidth / set_p2p_bandwidth           (AT+BANDWIDTH)
get_p2p_spread_factor / set_p2p_spread_factor   (AT+SPREADINGFACTOR)
get_p2p_coding_rate / set_p2p_coding_rate       (AT+CODINGRATE)
get_p2p_preamble_length_2 / set_p2p_preamble_length_2 (AT+PREAMBLELENGTH)
get_p2p_symbol_timeout / set_p2p_symbol_timeout (AT+SYMBOLTIMEOUT)
get_p2p_fixed_length_payload / set_p2p_fixed_length_payload (AT+FIXLENGTHPAYLOAD)

BUG-001 — FIXED
----------------
set_p2p_params() previously had ``bandwidth=125`` as default (the value in
kHz) but the guard clause required ``0 <= bandwidth <= 9`` (the index).
The fix changed the default to ``bandwidth=0`` (index for 125 kHz), so
calling set_p2p_params() with no arguments now correctly sends
AT+P2P=868000000:7:0:0:8:14.

The regression-guard test (test_default_args_send_correct_cmd) below
verifies that this fix is not accidentally reverted in future.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

import rui3pylib
from conftest import OK_RESPONSE, ERR_PARAM, ERR_BUSY

# Valid test vectors
VALID_KEY_32 = "01020304050607080102030405060708"
VALID_KEY_16 = "0011223344556677"
VALID_IV_32  = "00112233445566770011223344556677"
VALID_SYNC   = "1424"


# ===========================================================================
# AT+NWM — LoRa network work mode (0=P2P, 1=LoRaWAN, 2=FSK)
# ===========================================================================

class TestLoraNetworkMode:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_lora_network_mode()
            m.assert_called_once_with(node, "AT+NWM=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.p2p
    @pytest.mark.parametrize("mode,cmd", [
        (0, "AT+NWM=0"),
        (1, "AT+NWM=1"),
        (2, "AT+NWM=2"),
    ])
    def test_set_valid_modes(self, node, mode, cmd):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_lora_network_mode(mode)
            m.assert_called_once_with(node, cmd)

    @pytest.mark.validation
    @pytest.mark.p2p
    def test_set_mode_3_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_lora_network_mode(3) is None
            m.assert_not_called()

    @pytest.mark.validation
    @pytest.mark.p2p
    def test_set_negative_mode_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_lora_network_mode(-1) is None
            m.assert_not_called()


# ===========================================================================
# AT+PFREQ — P2P frequency (no library-side range guard)
# ===========================================================================

class TestP2pFreq:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_freq()
            m.assert_called_once_with(node, "AT+PFREQ=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_eu868_freq(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_freq(868000000)
            m.assert_called_once_with(node, "AT+PFREQ=868000000")

    @pytest.mark.happy_path
    @pytest.mark.p2p
    def test_set_returns_response_on_ok(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE):
            assert node.set_p2p_freq(868000000) is not None


# ===========================================================================
# AT+PSF — P2P spreading factor (5-12)
# ===========================================================================

class TestP2pSpreadFactor:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_spread_factor()
            m.assert_called_once_with(node, "AT+PSF=?")

    @pytest.mark.boundary
    @pytest.mark.p2p
    @pytest.mark.parametrize("sf", [5, 6, 7, 8, 9, 10, 11, 12])
    def test_all_valid_sf_accepted(self, node, sf):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_spread_factor(sf)
            m.assert_called_once_with(node, f"AT+PSF={sf}")
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_sf_4_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_spread_factor(4) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_sf_13_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_spread_factor(13) is None
            m.assert_not_called()


# ===========================================================================
# AT+PBW — P2P bandwidth index (0-9)
# ===========================================================================

class TestP2pBandwidth:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_band()
            m.assert_called_once_with(node, "AT+PBW=?")

    @pytest.mark.boundary
    @pytest.mark.p2p
    @pytest.mark.parametrize("bw", range(10))   # 0-9
    def test_all_valid_bw_indexes_accepted(self, node, bw):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_p2p_band(bw)
            m.assert_called_once_with(node, f"AT+PBW={bw}")
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_bw_10_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_band(10) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_bw_negative_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_band(-1) is None
            m.assert_not_called()


# ===========================================================================
# AT+PCR — P2P code rate (0-3)
# ===========================================================================

class TestP2pCodeRate:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_code_rate()
            m.assert_called_once_with(node, "AT+PCR=?")

    @pytest.mark.boundary
    @pytest.mark.p2p
    @pytest.mark.parametrize("cr,label", [
        (0, "4/5"), (1, "4/6"), (2, "4/7"), (3, "4/8")
    ])
    def test_all_valid_code_rates_accepted(self, node, cr, label):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_p2p_code_rate(cr)
            m.assert_called_once_with(node, f"AT+PCR={cr}")
            assert result is not None, f"Code rate {cr} ({label}) should be accepted"

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_cr_4_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_code_rate(4) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_cr_negative_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_code_rate(-1) is None
            m.assert_not_called()


# ===========================================================================
# AT+PPL — P2P preamble length (5-65535)
# ===========================================================================

class TestP2pPreambleLength:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_preamble_length()
            m.assert_called_once_with(node, "AT+PPL=?")

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_minimum_5_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_preamble_length(5) is not None
            m.assert_called_once_with(node, "AT+PPL=5")

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_maximum_65535_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_preamble_length(65535) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_4_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_preamble_length(4) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_65536_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_preamble_length(65536) is None
            m.assert_not_called()


# ===========================================================================
# AT+PTP — P2P TX power (5-22 dBm)
# ===========================================================================

class TestP2pTxPower:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_tx_power()
            m.assert_called_once_with(node, "AT+PTP=?")

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_minimum_5dbm_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_tx_power(5) is not None

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_maximum_22dbm_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_tx_power(22) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_4_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_tx_power(4) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_23_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_tx_power(23) is None
            m.assert_not_called()


# ===========================================================================
# AT+PBR — P2P FSK bitrate (600-300000 bps)
# ===========================================================================

class TestP2pFskBitrate:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_fsk_bitrate()
            m.assert_called_once_with(node, "AT+PBR=?")

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_minimum_600bps_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_fsk_bitrate(600) is not None

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_maximum_300000bps_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_fsk_bitrate(300000) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_599bps_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_fsk_bitrate(599) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_300001bps_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_fsk_bitrate(300001) is None
            m.assert_not_called()


# ===========================================================================
# AT+PFDEV — P2P FSK frequency deviation (600-200000 Hz)
# ===========================================================================

class TestP2pFreqDeviation:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_freq_deviation()
            m.assert_called_once_with(node, "AT+PFDEV=?")

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_minimum_600hz_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_freq_deviation(600) is not None

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_maximum_200000hz_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_freq_deviation(200000) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_599hz_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_freq_deviation(599) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_200001hz_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_freq_deviation(200001) is None
            m.assert_not_called()


# ===========================================================================
# AT+PSEND — P2P send
# ===========================================================================

class TestP2pSend:

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_valid_payload(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.p2p_send("112233")
            m.assert_called_once_with(node, "AT+PSEND=112233")

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_minimum_2_char_payload(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.p2p_send("AB")
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_maximum_500_char_payload(self, node):
        payload = "AB" * 250
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.p2p_send(payload)
            assert result is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_1_char_payload_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.p2p_send("A") is None
            m.assert_not_called()

    @pytest.mark.validation
    @pytest.mark.p2p
    def test_odd_length_payload_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.p2p_send("ABC") is None
            m.assert_not_called()

    @pytest.mark.validation
    @pytest.mark.p2p
    def test_non_hex_payload_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.p2p_send("GGGG") is None
            m.assert_not_called()


# ===========================================================================
# AT+CAD — P2P Channel Activity Detection
# ===========================================================================

class TestP2pChannelActivity:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_channel_activity()
            m.assert_called_once_with(node, "AT+CAD=?")

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_true_enables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_channel_activity(True)
            m.assert_called_once_with(node, "AT+CAD=1")

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_false_disables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_channel_activity(False)
            m.assert_called_once_with(node, "AT+CAD=0")


# ===========================================================================
# AT+PRECV — P2P receive window
# ===========================================================================

class TestP2pReceive:

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_timed_rx_30s(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.p2p_receive(30000)
            m.assert_called_once_with(node, "AT+PRECV=30000")

    @pytest.mark.happy_path
    @pytest.mark.p2p
    @pytest.mark.parametrize("timeout,description", [
        (0,     "stop RX / switch to TX"),
        (1,     "minimum timed window"),
        (65532, "maximum timed window"),
        (65533, "continuous RX, TX allowed"),
        (65534, "continuous RX, no TX"),
        (65535, "RX until one packet received"),
    ])
    def test_all_special_timeout_values_accepted(self, node, timeout, description):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.p2p_receive(timeout)
            m.assert_called_once_with(node, f"AT+PRECV={timeout}")
            assert result is not None, f"Timeout {timeout} ({description}) should be valid"

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_negative_timeout_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.p2p_receive(-1) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_65536_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.p2p_receive(65536) is None
            m.assert_not_called()

    @pytest.mark.device_error
    @pytest.mark.p2p
    def test_returns_none_when_busy(self, node):
        """AT_BUSY_ERROR is returned when already in continuous RX mode."""
        with patch("rui3pylib.check_success", return_value=ERR_BUSY):
            assert node.p2p_receive(30000) is None


# ===========================================================================
# AT+ENCRY / AT+ENCKEY — P2P encryption on/off + key
# ===========================================================================

class TestP2pEncryption:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_status_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_encryption()
            m.assert_called_once_with(node, "AT+ENCRY=?")

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_true_enables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_encryption(True)
            m.assert_called_once_with(node, "AT+ENCRY=1")

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_false_disables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_encryption(False)
            m.assert_called_once_with(node, "AT+ENCRY=0")

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_key_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_encryption_key()
            m.assert_called_once_with(node, "AT+ENCKEY=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_valid_32_hex_key(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_encryption_key(VALID_KEY_32)
            m.assert_called_once_with(node, f"AT+ENCKEY={VALID_KEY_32}")

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_30_char_key_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_encryption_key("0" * 30) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_34_char_key_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_encryption_key("0" * 34) is None
            m.assert_not_called()

    @pytest.mark.validation
    @pytest.mark.p2p
    def test_non_hex_key_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_encryption_key("G" * 32) is None
            m.assert_not_called()


# ===========================================================================
# AT+PCRYPT / AT+PKEY — P2P crypt status + 8-byte key
# ===========================================================================

class TestP2pCryptStatus:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_status_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_crypt_status()
            m.assert_called_once_with(node, "AT+PCRYPT=?")

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_true_enables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_crypt_status(True)
            m.assert_called_once_with(node, "AT+PCRYPT=1")

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_key_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_crypt_decrypt_key()
            m.assert_called_once_with(node, "AT+PKEY=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_valid_16_hex_key(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_crypt_decrypt_key(VALID_KEY_16)
            m.assert_called_once_with(node, f"AT+PKEY={VALID_KEY_16}")

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_14_char_key_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_crypt_decrypt_key("0" * 14) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_18_char_key_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_crypt_decrypt_key("0" * 18) is None
            m.assert_not_called()

    @pytest.mark.validation
    @pytest.mark.p2p
    def test_non_hex_key_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_crypt_decrypt_key("G" * 16) is None
            m.assert_not_called()


# ===========================================================================
# AT+CRYPIV — P2P initialisation vector (32 hex chars / 16 bytes)
# ===========================================================================

class TestP2pCryptIv:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_crypt_iv()
            m.assert_called_once_with(node, "AT+CRYPIV=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_valid_iv(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_crypt_iv(VALID_IV_32)
            m.assert_called_once_with(node, f"AT+CRYPIV={VALID_IV_32}")

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_30_char_iv_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_crypt_iv("0" * 30) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_34_char_iv_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_crypt_iv("0" * 34) is None
            m.assert_not_called()

    @pytest.mark.validation
    @pytest.mark.p2p
    def test_non_hex_iv_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_crypt_iv("G" * 32) is None
            m.assert_not_called()


# ===========================================================================
# AT+P2P — set all P2P params at once
# ===========================================================================

class TestP2pParams:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_sends_correct_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_params()
            m.assert_called_once_with(node, "AT+P2P=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_valid_params_builds_correct_cmd(self, node):
        """All valid parameters → correct AT+P2P=freq:sf:bw:cr:preamble:power."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_params(
                freq=868000000, sf=7, bandwidth=0,
                code_rate=0, preamble_len=8, tx_power=14
            )
            m.assert_called_once_with(node, "AT+P2P=868000000:7:0:0:8:14")

    # ── BUG-001 regression guard (fix verified) ─────────────────────────────
    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_default_args_send_correct_cmd(self, node):
        """
        Regression guard for BUG-001 (now FIXED).

        set_p2p_params() with no arguments must send:
            AT+P2P=868000000:7:0:0:8:14

        Default values after the fix:
            freq=868000000, SF=7, bandwidth=0 (=125 kHz index),
            code_rate=0 (=4/5), preamble=8, tx_power=14 dBm.

        If this test starts FAILING, BUG-001 was accidentally reverted
        (bandwidth default changed back from 0 to 125).
        """
        expected = "AT+P2P=868000000:7:0:0:8:14"
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.set_p2p_params()   # all defaults
            m.assert_called_once_with(node, expected)
            assert result is not None, (
                "set_p2p_params() with default args returned None — "
                "BUG-001 may have been accidentally reverted "
                "(bandwidth default changed back to 125 instead of 0)."
            )

    # ── sf range ────────────────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_minimum_sf6_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_params(868000000, sf=6, bandwidth=0) is not None

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_maximum_sf12_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_params(868000000, sf=12, bandwidth=0) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_sf5_rejected_by_set_p2p_params(self, node):
        """set_p2p_params validates sf ≥ 6; note set_spread_factor (AT+PSF) allows sf=5."""
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_params(868000000, sf=5, bandwidth=0) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_sf13_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_params(868000000, sf=13, bandwidth=0) is None
            m.assert_not_called()

    # ── frequency range ─────────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_minimum_freq_150mhz_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_params(150000000, sf=7, bandwidth=0) is not None

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_maximum_freq_960mhz_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_params(960000000, sf=7, bandwidth=0) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_freq_below_150mhz_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_params(149999999, sf=7, bandwidth=0) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_freq_above_960mhz_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_params(960000001, sf=7, bandwidth=0) is None
            m.assert_not_called()

    # ── preamble range ───────────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_minimum_preamble_2_accepted(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_params(868000000, sf=7, bandwidth=0, preamble_len=2) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_preamble_1_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_params(868000000, sf=7, bandwidth=0, preamble_len=1) is None
            m.assert_not_called()

    # ── tx_power range ───────────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_tx_power_4_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_params(868000000, sf=7, bandwidth=0, tx_power=4) is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_tx_power_23_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_params(868000000, sf=7, bandwidth=0, tx_power=23) is None
            m.assert_not_called()


# ===========================================================================
# AT+IQINVER — P2P IQ inversion
# ===========================================================================

class TestP2pIqInversion:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_iq_inv()
            m.assert_called_once_with(node, "AT+IQINVER=?")

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_true_enables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_iq_inv(True)
            m.assert_called_once_with(node, "AT+IQINVER=1")

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_false_disables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_iq_inv(False)
            m.assert_called_once_with(node, "AT+IQINVER=0")


# ===========================================================================
# AT+SYNCWORD — P2P sync word (4 hex chars / 2 bytes)
# ===========================================================================

class TestP2pSyncword:

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_syncword()
            m.assert_called_once_with(node, "AT+SYNCWORD=?")

    @pytest.mark.happy_path
    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_valid_syncword(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_syncword(VALID_SYNC)
            m.assert_called_once_with(node, f"AT+SYNCWORD={VALID_SYNC}")

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_3_char_syncword_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_syncword("142") is None
            m.assert_not_called()

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_5_char_syncword_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_syncword("14244") is None
            m.assert_not_called()

    @pytest.mark.validation
    @pytest.mark.p2p
    def test_non_hex_syncword_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_syncword("GGGG") is None
            m.assert_not_called()


# ===========================================================================
# Legacy P2P commands (AT+RFFREQUENCY, AT+TXOUTPUTPOWER, AT+BANDWIDTH,
# AT+SPREADINGFACTOR, AT+CODINGRATE, AT+PREAMBLELENGTH, AT+SYMBOLTIMEOUT,
# AT+FIXLENGTHPAYLOAD)
# ===========================================================================

class TestP2pLegacyCommands:

    # AT+RFFREQUENCY ─────────────────────────────────────────────────────────

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_rf_freq_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_rf_freq()
            m.assert_called_once_with(node, "AT+RFFREQUENCY=?")

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_rf_freq(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_rf_freq(868000000)
            m.assert_called_once_with(node, "AT+RFFREQUENCY=868000000")

    # AT+TXOUTPUTPOWER ───────────────────────────────────────────────────────

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_tx_out_power_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_tx_out_power()
            m.assert_called_once_with(node, "AT+TXOUTPUTPOWER=?")

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_set_tx_out_power_min_5(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_tx_out_power(5) is not None

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_set_tx_out_power_max_22(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_tx_out_power(22) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_set_tx_out_power_4_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_tx_out_power(4) is None

    # AT+BANDWIDTH ───────────────────────────────────────────────────────────

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_bandwidth_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_bandwidth()
            m.assert_called_once_with(node, "AT+BANDWIDTH=?")

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_set_bandwidth_min_0(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_bandwidth(0) is not None

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_set_bandwidth_max_9(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_bandwidth(9) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_set_bandwidth_10_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_bandwidth(10) is None

    # AT+SPREADINGFACTOR ─────────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_set_spreading_factor_min_5(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_spread_factor(5) is not None

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_set_spreading_factor_max_12(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_spread_factor(12) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_set_spreading_factor_4_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_spread_factor(4) is None

    # AT+CODINGRATE ──────────────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.p2p
    @pytest.mark.parametrize("cr", [0, 1, 2, 3])
    def test_coding_rate_valid(self, node, cr):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_coding_rate(cr) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_coding_rate_4_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_coding_rate(4) is None

    # AT+PREAMBLELENGTH ──────────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_preamble_length_2_min(self, node):
        """AT+PREAMBLELENGTH uses set_p2p_preamble_length_2 with range 5-65535."""
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_preamble_length_2(5) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_preamble_length_2_below_min_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_preamble_length_2(4) is None

    # AT+SYMBOLTIMEOUT ───────────────────────────────────────────────────────

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_symbol_timeout_min_0(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_symbol_timeout(0) is not None

    @pytest.mark.boundary
    @pytest.mark.p2p
    def test_symbol_timeout_max_248(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            assert node.set_p2p_symbol_timeout(248) is not None

    @pytest.mark.boundary
    @pytest.mark.validation
    @pytest.mark.p2p
    def test_symbol_timeout_249_rejected(self, node):
        with patch("rui3pylib.check_success") as m:
            assert node.set_p2p_symbol_timeout(249) is None

    # AT+FIXLENGTHPAYLOAD ────────────────────────────────────────────────────

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_get_fixed_length_payload_query(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.get_p2p_fixed_length_payload()
            m.assert_called_once_with(node, "AT+FIXLENGTHPAYLOAD=?")

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_true_enables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_fixed_length_payload(True)
            m.assert_called_once_with(node, "AT+FIXLENGTHPAYLOAD=1")

    @pytest.mark.cmd_format
    @pytest.mark.p2p
    def test_set_false_disables(self, node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            node.set_p2p_fixed_length_payload(False)
            m.assert_called_once_with(node, "AT+FIXLENGTHPAYLOAD=0")
