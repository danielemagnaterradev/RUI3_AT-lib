"""
tests/test_core_functions.py
=============================
Unit tests for the two module-level I/O primitives:

    send_command(port, cmd, wait=3.0)  -> str
    check_success(port, cmd, wait=3.0) -> (str, bool)

These are the *only* functions that touch the serial wire.  Every other
test in the suite mocks them out; here we test the actual byte-level and
string-processing logic using ``FakeSerial``.

Time is controlled with ``unittest.mock.patch("time.sleep")`` to avoid
real delays.  ``time.monotonic`` is left real because FakeSerial drains
its buffer in a single read() call, so the drain loop exits immediately
on the first in_waiting check.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, call
import rui3pylib
from conftest import FakeSerial


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_send(fs: FakeSerial, cmd: str, wait: float = 0) -> str:
    """Run send_command with time.sleep patched out."""
    with patch("time.sleep"):
        return rui3pylib.send_command(fs, cmd, wait=wait)


def _make_ok_serial(extra: str = "") -> FakeSerial:
    """Return a FakeSerial pre-loaded with a well-formed OK response."""
    payload = (extra + "\r\nOK\r\n").encode()
    return FakeSerial(payload)


# ===========================================================================
# send_command — wire protocol
# ===========================================================================


class TestSendCommandWireProtocol:
    """Verify that send_command correctly encodes and writes the command."""

    @pytest.mark.cmd_format
    def test_appends_crlf_terminator(self):
        """Command sent to the device always ends with \\r\\n."""
        fs = FakeSerial()
        _run_send(fs, "AT+VER=?")
        assert fs.last_written_str == "AT+VER=?\r\n"

    @pytest.mark.cmd_format
    def test_strips_leading_and_trailing_whitespace_before_crlf(self):
        """Whitespace around the command is stripped; only \\r\\n is appended."""
        fs = FakeSerial()
        _run_send(fs, "  AT+VER=?  ")
        assert fs.last_written_str == "AT+VER=?\r\n"

    @pytest.mark.cmd_format
    def test_resets_input_buffer_before_write(self):
        """reset_input_buffer() is called before writing the command to the port.

        Design note
        ~~~~~~~~~~~
        On a real serial port, reset_input_buffer() discards stale incoming
        bytes that arrived before the new command was sent.  In FakeSerial
        this method is intentionally a no-op (see conftest.py), because the
        pre-loaded bytes are the intended response, not stale data.

        This test therefore uses unittest.mock.MagicMock to verify the *call
        order* (reset_input_buffer before write) without relying on FakeSerial
        clearing any buffer.
        """
        from unittest.mock import MagicMock, call

        mock_port = MagicMock()
        mock_port.in_waiting = 0  # no response bytes → empty response

        with patch("time.sleep"):
            rui3pylib.send_command(mock_port, "AT", wait=0)

        # reset_input_buffer() must have been called …
        mock_port.reset_input_buffer.assert_called_once()
        # … and it must have been called BEFORE write().
        call_order = [c[0] for c in mock_port.mock_calls]
        reset_idx = call_order.index("reset_input_buffer")
        write_idx = call_order.index("write")
        assert reset_idx < write_idx, (
            "reset_input_buffer() must be called before write() "
            f"(got indices {reset_idx} and {write_idx})"
        )
        # The command was written with the correct encoding.
        mock_port.write.assert_called_once_with(b"AT\r\n")

    @pytest.mark.cmd_format
    def test_sends_exactly_one_write_call_per_command(self):
        """Each send_command invocation writes exactly one chunk."""
        fs = FakeSerial()
        _run_send(fs, "AT+NWM=?")
        assert len(fs.all_written) == 1


# ===========================================================================
# send_command — response reading
# ===========================================================================


class TestSendCommandResponseReading:
    """Verify that the receive buffer is drained and decoded correctly."""

    @pytest.mark.happy_path
    def test_returns_response_string(self):
        """The decoded response is returned verbatim (except [APP] lines)."""
        payload = b"AT+VER=RUI_4.1.0_RAK4631\r\nOK\r\n"
        fs = FakeSerial(payload)
        response = _run_send(fs, "AT+VER=?")
        assert "RUI_4.1.0_RAK4631" in response
        assert "OK" in response

    @pytest.mark.happy_path
    def test_empty_response_returns_empty_string(self):
        """If the device sends nothing, an empty string is returned."""
        fs = FakeSerial()
        response = _run_send(fs, "ATZ")
        assert response == ""

    @pytest.mark.happy_path
    def test_filters_out_app_debug_lines(self):
        """Lines starting with [APP] are stripped from the returned response."""
        payload = b"[APP] internal debug\r\nOK\r\n"
        fs = FakeSerial(payload)
        response = _run_send(fs, "AT")
        assert "[APP]" not in response
        assert "OK" in response

    @pytest.mark.happy_path
    def test_non_app_lines_are_retained(self):
        """Lines NOT starting with [APP] are retained unchanged."""
        payload = b"AT+BAT=2.971191\r\nOK\r\n"
        fs = FakeSerial(payload)
        response = _run_send(fs, "AT+BAT=?")
        assert "AT+BAT=2.971191" in response

    @pytest.mark.happy_path
    def test_multiple_app_debug_lines_all_filtered(self):
        """Multiple [APP] lines are all stripped, leaving only the real payload."""
        payload = b"[APP] step 1\r\n[APP] step 2\r\nAT+SN=9181004E\r\nOK\r\n"
        fs = FakeSerial(payload)
        response = _run_send(fs, "AT+SN=?")
        assert "[APP]" not in response
        assert "9181004E" in response

    @pytest.mark.happy_path
    def test_non_utf8_bytes_decoded_with_replace(self):
        """Non-UTF-8 bytes produce the Unicode replacement character, not an exception."""
        payload = b"\xff\xfe\r\nOK\r\n"
        fs = FakeSerial(payload)
        # Must not raise.
        response = _run_send(fs, "AT")
        assert "OK" in response


# ===========================================================================
# check_success — OK detection logic
# ===========================================================================


class TestCheckSuccessOKDetection:
    """
    Verify the core invariant: ok=True iff the response contains a line
    that equals exactly "OK" (after stripping whitespace).
    """

    @pytest.mark.happy_path
    def test_ok_true_when_standalone_ok_line_present(self):
        """Standard OK response: \\r\\nOK\\r\\n → ok=True."""
        fs = _make_ok_serial()
        with patch("time.sleep"):
            _, ok = rui3pylib.check_success(fs, "AT")
        assert ok is True

    @pytest.mark.happy_path
    def test_ok_false_on_param_error(self):
        """AT_PARAM_ERROR response → ok=False."""
        fs = FakeSerial(b"AT_PARAM_ERROR\r\n")
        with patch("time.sleep"):
            _, ok = rui3pylib.check_success(fs, "AT+DR=99")
        assert ok is False

    @pytest.mark.happy_path
    def test_ok_false_on_busy_error(self):
        """AT_BUSY_ERROR response → ok=False."""
        fs = FakeSerial(b"AT_BUSY_ERROR\r\n")
        with patch("time.sleep"):
            _, ok = rui3pylib.check_success(fs, "AT+JOIN=1:0:8:0")
        assert ok is False

    @pytest.mark.happy_path
    def test_ok_false_on_no_network_joined(self):
        """AT_NO_NETWORK_JOINED response → ok=False."""
        fs = FakeSerial(b"AT_NO_NETWORK_JOINED\r\n")
        with patch("time.sleep"):
            _, ok = rui3pylib.check_success(fs, "AT+SEND=1:AABB")
        assert ok is False

    @pytest.mark.happy_path
    def test_ok_false_on_empty_response(self):
        """Empty response → ok=False (no OK line present)."""
        fs = FakeSerial()
        with patch("time.sleep"):
            _, ok = rui3pylib.check_success(fs, "ATZ")
        assert ok is False

    # ── False-positive prevention ──────────────────────────────────────────

    @pytest.mark.validation
    def test_ok_substring_in_payload_does_not_trigger_ok(self):
        """A payload that *contains* the letters OK must not produce ok=True."""
        fs = FakeSerial(b"SEND_CONFIRMED_OK_DONE\r\nAT_PARAM_ERROR\r\n")
        with patch("time.sleep"):
            _, ok = rui3pylib.check_success(fs, "AT+SEND=1:AB")
        assert ok is False

    @pytest.mark.validation
    def test_badok_line_does_not_trigger_ok(self):
        """A line 'BADOK' is not equal to 'OK' and must not set ok=True."""
        fs = FakeSerial(b"BADOK\r\n")
        with patch("time.sleep"):
            _, ok = rui3pylib.check_success(fs, "AT")
        assert ok is False

    @pytest.mark.validation
    def test_ok_with_surrounding_whitespace_is_still_recognised(self):
        """Firmware that pads 'OK' with spaces still sets ok=True after strip()."""
        fs = FakeSerial(b"  OK  \r\n")
        with patch("time.sleep"):
            _, ok = rui3pylib.check_success(fs, "AT")
        assert ok is True

    @pytest.mark.validation
    def test_ok_embedded_in_key_value_line_does_not_match(self):
        """'AT+CFM=1\\nOK' → only the standalone 'OK' line triggers ok=True."""
        # Two lines: "AT+CFM=1" and "OK".
        fs = FakeSerial(b"AT+CFM=1\r\nOK\r\n")
        with patch("time.sleep"):
            _, ok = rui3pylib.check_success(fs, "AT+CFM=?")
        assert ok is True  # The OK is on its own line, so it IS a match.

    # ── Return value structure ─────────────────────────────────────────────

    @pytest.mark.happy_path
    def test_returns_full_response_string_as_first_element(self):
        """The first return value is the complete raw response string."""
        payload = b"AT+VER=RUI_4.1.0_RAK4631\r\nOK\r\n"
        fs = FakeSerial(payload)
        with patch("time.sleep"):
            response, ok = rui3pylib.check_success(fs, "AT+VER=?")
        assert ok is True
        assert "RUI_4.1.0_RAK4631" in response

    @pytest.mark.happy_path
    def test_returns_tuple_of_str_and_bool(self):
        """Return value is always a (str, bool) tuple."""
        fs = _make_ok_serial()
        with patch("time.sleep"):
            result = rui3pylib.check_success(fs, "AT")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], bool)
