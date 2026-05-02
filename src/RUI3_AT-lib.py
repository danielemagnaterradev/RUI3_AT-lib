import logging
import openpyxl
import serial
import time
from typing import Optional

class RUI3node:
    def __init__ (self, port: str, baudrate: int = 115200, timeout: float = 3.0):
        self. port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None

    def connect(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout = self.timeout)
        time.sleep(1)
        log.info(f"Connected to port: {self.port}")

    def close(self):
        if self.ser && self.ser.is_open:
            self.ser.close()
            log.info("Serial port closed")
