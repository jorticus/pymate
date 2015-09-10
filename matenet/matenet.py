# pyMATE controller (raw MateNET access)
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Emulates an Outback MATE controller panel, allowing direct communication with
# an attached device (no MATE needed!)
#
# Currently only supports the MX status page (from an Outback MX charge controller)
# Connection through a Hub not tested
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

__author__ = 'Jared'

from serial import Serial, PARITY_SPACE, PARITY_MARK
from cstruct import struct
from util import bin2hexstr, hexstr2bin

class MateNET(object):
    """
    Interface for the MATE RJ45 bus ("MateNET")
    This class only handles the low level protocol,
    it does not care what is attached to the bus.
    """
    ScanPacket = struct('BBBB', ('a','b','c','d')) # TODO: What does each field represent?
    CommandPacket = None
    StatusPacket = None

    DEVICE_HUB = 1
    DEVICE_FX = 2
    DEVICE_MX = 3

    TYPE_QUERY = 2
    TYPE_CONTROL = 3
    TYPE_STATUS = 4
    TYPE_LOG = 22

    def __init__(self, comport):
        if isinstance(comport, Serial):
            self.ser = comport
        else:
            self.ser = Serial(comport, 9600, parity=PARITY_SPACE)
            self.ser.setTimeout(1.0)

    def _send(self, data):
        """
        Send a packet to the MateNET bus
        :param data: str containing the raw data to send (excluding checksum)
        """
        checksum = self._calc_checksum(data)
        footer = chr((checksum >> 8) & 0xFF) + chr(checksum & 0xFF)

        # First byte has bit8 set (address byte)
        self.ser.setParity(PARITY_MARK)
        self.ser.write(data[0])

        # Rest of the bytes have bit8 cleared (data byte)
        self.ser.setParity(PARITY_SPACE)
        self.ser.write(data[1:] + footer)

    @staticmethod
    def _calc_checksum(data):
        """
        Calculate the checksum of some raw data.
        The checksum is a simple 16-bit sum over all the bytes in the packet,
        including the 9-bit start-of-packet byte (though the 9th bit is not counted)
        """
        return sum(ord(c) for c in data) % 0xFFFF

    @staticmethod
    def _parse_packet(data):
        """
        Parse a MATE packet, validatin the length and checksum
        :param data: Raw string data
        :return: Raw string data of the packet itself (excluding SOF and checksum)
        """
        # Validation
        if not data or len(data) == 0:
            raise RuntimeError("Error receiving mate packet - No data received")
        if len(data) < 3:
            raise RuntimeError("Error receiving mate packet - Received packet too small")

        # Checksum
        packet = data[0:-2]
        expected_chksum = (ord(data[-2]) << 8) | ord(data[-1])
        actual_chksum = MateNET._calc_checksum(packet)
        if actual_chksum != expected_chksum:
            raise RuntimeError("Error receiving mate packet - Invalid checksum (Expected:%d, Actual:%d)" % (expected_chksum, actual_chksum))
        return packet

    def _recv(self, timeout=1.0):
        """
        Receive a packet from the MateNET bus, waiting if necessary
        :param timeout: seconds to wait until returning, 0 to return immediately, None to block indefinitely
        :return: str if packet received, None if timeout
        """
        # Wait for packet
        # TODO: Check parity?
        self.ser.setTimeout(timeout)
        rawdata = self.ser.read(1)
        if not rawdata:
            return None

        # Get rest of packet (timeout set to 10ms to detect end of packet)
        self.ser.setTimeout(0.01)
        b = 1
        while b:
            b = self.ser.read()
            rawdata += b

        return MateNET._parse_packet(rawdata)


class Mate(MateNET):
    """
    Emulates the MATE controller, allows communication with any attached devices
    """
    def __init__(self, comport):
        super(Mate, self).__init__(comport)

    def scan(self):
        self._send('\x00\x02\x00\x00\x00\x00')
        data = self._recv(16)
        print "scan:", data
        # TODO: What to do with the result?
        # TODO: Return the detected unit type (MX/FX/etc) ??
