
# pyMATE serial interface (emulated 9-bit)
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Emulates an Outback MATE controller panel, allowing direct communication with
# an attached device (no MATE needed!)
#
# The proprietary protocol between the MATE controller and an attached Outback product
# (from now on referred to as "MateNET"), is just serial (UART) with 0-24V logic levels.
# Serial format: 9600 baud, 9n1
# Pinout:
#   1: +V (battery voltage)
#   2: GND
#   3: TX (From MATE to unit)
#   6: RX (From unit to MATE)
# Note that the above pinout matches the pairs in a CAT5 cable (Green/Orange pairs)
#
# The protocol itself consists of raw binary data, in big-endian format.
# It uses 9-bit serial communication, where the 9th bit denotes the start of a packet.
# The rest of the implementation details are explained throughout the following code...
#

__author__ = 'Jared'

import logging
from time import sleep

from pymate.cstruct import struct
from pymate.util import bin2hexstr, to_byte, to_bytestr
from serial import PARITY_EVEN, PARITY_MARK, PARITY_ODD, PARITY_SPACE, Serial


class MateNETSerial(object):    
    """
    Interface for the MATE RJ45 bus ("MateNET")
    This class only handles the low level protocol,
    it does not care what is attached to the bus.
    """
    def __init__(self, comport, supports_spacemark=None):
        """
        :param comport: The hardware serial port to use (eg. /dev/ttyUSB0 or COM1)
        :param supports_spacemark: 
            True-Port supports Space/Mark parity. 
            False-Port does not support Space/Mark parity. 
            None-Try detect whether the port supports Space/Mark parity.
        """
        if isinstance(comport, Serial):
            self.ser = comport
        else:
            self.ser = Serial(comport, 9600, parity=PARITY_ODD)
            self.ser.timeout = 1.0

        self.log = logging.getLogger('mate.ser')

        # Delay between bytes when space/mark is not supported
        # This is needed to ensure changing the parity between even/odd only affects one byte at a time
        # (Essentially forces 1 byte in the TX buffer at a time)
        self.FUDGE_FACTOR = 0.002 # seconds

        # Amount of time with no communication that signifies the end of the packet
        self.END_OF_PACKET_TIMEOUT = 0.02 # seconds

        # Set to true to workaround issue where some received packets are too large
        self.TRIM_LARGE_PACKETS = True

        self.supports_spacemark = supports_spacemark
        if self.supports_spacemark is None:
            self.supports_spacemark = (
                (PARITY_SPACE in self.ser.PARITIES) and
                (PARITY_MARK in self.ser.PARITIES)
            )

    def _odd_parity(self, b):
        p = False
        while b:
            p = not p
            b = b & (b - 1)
        return p

    def _write_9b(self, data, bit8):
        
        #assert(data is not None and len(data) > 0)
        #assert(isinstance(data, bytes))

        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug('TX: [%d] %s', bit8, data)

        if self.supports_spacemark:
            if bit8:
                self.ser.parity = PARITY_MARK
            else:
                self.ser.parity = PARITY_SPACE
            self.ser.write(data)
            sleep(self.FUDGE_FACTOR)
        else:
            # Emulate SPACE/MARK parity using EVEN/ODD parity
            for b in data:
                p = self._odd_parity(to_byte(b)) ^ bit8
                self.ser.parity = (PARITY_ODD if p else PARITY_EVEN)
                self.ser.write(to_bytestr(b))
                sleep(self.FUDGE_FACTOR)

    @staticmethod
    def _calc_checksum(data):
        """
        Calculate the checksum of some raw data.
        The checksum is a simple 16-bit sum over all the bytes in the packet,
        including the 9-bit start-of-packet byte (though the 9th bit is not counted)
        """
        assert(isinstance(data, bytes))
        return sum(to_byte(c) for c in data) % 0xFFFF

    @staticmethod
    def _parse_packet(data, expected_len=None):
        """
        Parse a MATE packet, validatin the length and checksum
        :param data: Raw string data
        :return: Raw string data of the packet itself (excluding SOF and checksum)
        """
        # Validation
        if not data or len(data) == 0:
            raise RuntimeError("Error receiving mate packet - No data received")
        if len(data) < 3:
            raise RuntimeError("Error receiving mate packet - Received packet too small (%d bytes)" % (len(data)))
        assert(isinstance(data, bytes))

        if expected_len is not None:
            if len(data) < expected_len:
                raise RuntimeError("Error receiving mate packet - Received packet too small (%d bytes, expected %d)" % (len(data), expected_len))
            if len(data) > expected_len:
                RuntimeError("Error receiving mate packet - Received packet too large (%d bytes, expected %d)" % (len(data), expected_len)) 

        # Checksum
        packet = data[0:-2]
        expected_chksum = int((to_byte(data[-2]) << 8) | to_byte(data[-1]))
        actual_chksum = MateNETSerial._calc_checksum(packet)
        if actual_chksum != expected_chksum:
            raise RuntimeError("Error receiving mate packet - Invalid checksum (Expected:0x%.4x, Actual:0x%.4x)"
                               % (expected_chksum, actual_chksum))
        return packet

    def send(self, data):
        """
        Send a packet to the MateNET bus
        :param data: str containing the raw data to send (excluding checksum)
        """

        checksum = self._calc_checksum(data)
        footerh = checksum >> 8 & 0xFF
        footerl = checksum & 0xFF

        # First byte has bit8 set (address byte)
        self._write_9b(bytes([data[0]]), 1)

        # Rest of the bytes have bit8 cleared (data byte)
        self._write_9b(data[1:] + bytes([footerh]) + bytes([footerl]), 0)

    def recv(self, expected_len=None, timeout=1.0):
        """
        Receive a packet from the MateNET bus, waiting if necessary
        :param timeout: seconds to wait until returning, 0 to return immediately, None to block indefinitely
        :return: str if packet received, None if timeout
        """
        # Wait for packet
        # TODO: Check parity?
        self.ser.timeout = timeout
        rawdata = self.ser.read(1)
        if not rawdata:
            return None

        # Get rest of packet (timeout set to ~10ms to detect end of packet)
        self.ser.timeout = self.END_OF_PACKET_TIMEOUT
        b = 1
        while b:
            b = self.ser.read()
            rawdata += b

        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug('RX: %s', bin2hexstr(rawdata))

        if expected_len is not None:
            expected_len += 2 # Account for checksum

            if self.TRIM_LARGE_PACKETS and (len(rawdata) > expected_len):
                rawdata = rawdata[-expected_len:]

        return MateNETSerial._parse_packet(rawdata, expected_len)
