"""
tests/conftest.py
=================
Shared fixtures and test infrastructure for the rui3pylib test suite.

Architecture
------------
Unit tests avoid ALL serial-port I/O by mocking the two module-level I/O
functions that are the only bridge to the hardware wire:

    rui3pylib.check_success(port, cmd, wait=3.0) -> (response: str, ok: bool)
    rui3pylib.send_command(port, cmd, wait=3.0)  -> response: str

Every RUI3Node method either calls one of these two functions or performs
pure input validation before doing so.  The standard pattern in each unit
test is therefore:

    def test_something(node):
        with patch("rui3pylib.check_success", return_value=OK_RESPONSE) as m:
            result = node.some_setter(valid_value)
            m.assert_called_once_with(node, "AT+CMD=valid_value")
            assert result is not None

The ``node`` fixture creates a bare RUI3Node instance via object.__new__,
bypassing serial.Serial.__init__ entirely.

FakeSerial
----------
Used exclusively in test_core_functions.py to test send_command and
check_success at the byte-stream level.

The actual send_command() implementation:
    1. port.reset_input_buffer()    ← clears stale bytes
    2. port.write(cmd + "\\r\\n")
    3. time.sleep(wait)
    4. while port.in_waiting: response += port.read(port.in_waiting); sleep(0.1)
    5. filters out [APP] debug lines
    6. returns response string

FakeSerial.reset_input_buffer() is a NO-OP: the pre-loaded test response
is valid test data, not stale data.  The real serial port discards stale
incoming bytes that arrived before the command was sent; in tests the
pre-loaded bytes ARE the expected response and must be preserved.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch
import rui3pylib as lib


# ---------------------------------------------------------------------------
# Standard AT-command response constants
# ---------------------------------------------------------------------------

#: Successful device response – contains a standalone "OK" line.
OK_RESPONSE: tuple[str, bool] = ("\r\nOK\r\n", True)

#: Device returned AT_PARAM_ERROR (invalid parameter).
ERR_PARAM: tuple[str, bool] = ("AT_PARAM_ERROR\r\n", False)

#: Device returned AT_BUSY_ERROR (radio busy).
ERR_BUSY: tuple[str, bool] = ("AT_BUSY_ERROR\r\n", False)

#: Device returned AT_NO_NETWORK_JOINED.
ERR_NO_NETWORK: tuple[str, bool] = ("AT_NO_NETWORK_JOINED\r\n", False)


# ---------------------------------------------------------------------------
# Lightweight testable node fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def node() -> lib.RUI3Node:
    """
    Return a RUI3Node instance with all serial initialisation bypassed.

    Root cause of the previous failure
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUI3Node inherits from serial.Serial.  The serial.Serial.port attribute
    is a *property* whose setter calls self.is_open.  self.is_open is only
    set during serial.Serial.__init__(); if __init__ is not called (as in
    any subclass that overrides __init__ with a no-op), assigning to
    self.port raises:

        AttributeError: '_TestNode' object has no attribute 'is_open'

    Fix
    ~~~~
    Use object.__new__(lib.RUI3Node) to allocate the instance without
    invoking *any* __init__ (neither RUI3Node's nor serial.Serial's).
    Then set the internal pyserial attribute self._port directly, bypassing
    the property setter.  The property *getter* (used in log messages by
    lock_serial()) simply returns self._port, so this works correctly.

    All actual I/O is mocked per-test via patch("rui3pylib.check_success")
    and patch("rui3pylib.send_command"), so no real serial state is needed.
    """
    instance = object.__new__(lib.RUI3Node)
    # Set internal pyserial port attribute directly.
    # serial.Serial.port (getter) returns self._port, so self.port == "MOCK_PORT".
    instance._port = "MOCK_PORT"
    return instance


# ---------------------------------------------------------------------------
# FakeSerial – used only in test_core_functions.py
# ---------------------------------------------------------------------------

class FakeSerial:
    """
    Minimal serial.Serial substitute for byte-level I/O tests.

    Mirrors the interface used by send_command():
        - reset_input_buffer()   ← NO-OP (see module docstring)
        - write(data)
        - in_waiting             ← number of unread bytes
        - read(n)                ← consume n bytes

    Instantiate with the bytes the simulated device should return::

        fs = FakeSerial(b"AT+VER=RUI_4.1.0\\r\\nOK\\r\\n")
        result = send_command(fs, "AT+VER=?", wait=0)

    After the call ``fs.last_written_str`` contains the command that was
    sent (including the \\r\\n terminator).
    """

    def __init__(self, response: bytes = b"") -> None:
        self._buf: bytearray = bytearray(response)
        self._written: list[bytes] = []

    # ── write side ──────────────────────────────────────────────────────────

    def reset_input_buffer(self) -> None:
        """
        NO-OP in tests.

        send_command() calls this to discard stale bytes that arrived on a
        real serial port before the command was sent.  In FakeSerial the
        pre-loaded bytes ARE the intended response, not stale data, so they
        must be preserved.  Making this a no-op is correct for unit testing.
        """

    def write(self, data: bytes) -> int:
        self._written.append(data)
        return len(data)

    # ── read side ───────────────────────────────────────────────────────────

    @property
    def in_waiting(self) -> int:
        """Number of bytes not yet consumed by read()."""
        return len(self._buf)

    def read(self, n: int) -> bytes:
        chunk = bytes(self._buf[:n])
        del self._buf[:n]
        return chunk

    # ── test helpers ────────────────────────────────────────────────────────

    @property
    def last_written_str(self) -> str:
        """The last bytes passed to write(), decoded as UTF-8."""
        return self._written[-1].decode() if self._written else ""

    @property
    def all_written(self) -> list[str]:
        """All write() calls decoded as strings."""
        return [d.decode() for d in self._written]
