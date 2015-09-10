# pyMate controller (raw MateNET access)
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

from cstruct import struct
from value import Value
from serial import Serial, PARITY_SPACE, PARITY_MARK

# Raw mate status packet
_MateStatusStruct = struct('>B4sBBBHHHH', (
    'sop',              # Start-of-packet? has the 9th bit set to denote the start of the packet
    'q',                # TODO: Unsure what this contains
    'amp_hours',        # Daily accumulated amp-hours (0-255 AH)
    'kilowatt_peak',    # Daily kilowatts-peak (hundredths: 0.00-2.55 kW)
    'status',           # Status (Same as the MATE serial protocol)
    'kilowatt_hours',   # Kilowatt-hours (tenths: 0.0-6553.5 kWh)
    'v_bat',            # Battery/Out voltage (tenths: 0.0-6553.5 V)
    'v_pv'              # PV/In voltage (tenths: 0.0-6553.5 V)
))

class MateStatusPacket(_MateStatusStruct):
    STATUS_SLEEPING = 0
    STATUS_FLOATING = 1
    STATUS_BULK = 2
    STATUS_ABSORB = 3
    STATUS_EQUALIZE = 4

    @classmethod
    def from_buffer(cls, data):
        raw = super(MateStatusPacket, cls).from_buffer(data)
        # Wrap members in Value objects to make it more human-readable
        raw.amp_hours       = Value(raw.amp_hours,             units='Ah', resolution=0)
        raw.kilowatt_peak   = Value(raw.kilowatt_peak / 100.0, units='kW', resolution=2)
        raw.kilowatt_hours  = Value(raw.kilowatt_hours / 10.0, units='kW', resolution=1)
        raw.v_bat           = Value(raw.v_bat / 10.0,          units='V',  resolution=1)
        raw.v_pv            = Value(raw.v_pv / 10.0,           units='V',  resolution=1)
        # TODO: What does the 'q' member contain?
        return raw

class MateInterface(object):
    """
    Python interface for the MATE RJ45 bus
    Supports:
      - Solar Charger (Outback MATE)
    """
    def __init__(self, comport):
        self.ser = Serial(comport, 9600, parity=PARITY_SPACE)

    def _send(self, data):
        checksum = self._calc_checksum(data)
        footer = chr((checksum >> 8) & 0xFF) + chr(checksum & 0xFF)

        self.ser.setParity(PARITY_MARK)
        self.ser.write('\x00')
        self.ser.setParity(PARITY_SPACE)
        self.ser.write(data + footer)

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
        actual_chksum = MateInterface._calc_checksum(packet)
        if actual_chksum != expected_chksum:
            raise RuntimeError("Error receiving mate packet - Invalid checksum (Expected:%d, Actual:%d)" % (expected_chksum, actual_chksum))
        return packet

    def _recv(self):
        rawdata = [] # TODO
        return MateInterface._parse_packet(rawdata)

    def get_mxstatus(self):
        """
        Request a status packet from the controller
        :return: A MateStatusPacket
        """
        self._send('\x04\x00\x01\x00\x00\x00')
        data = self._recv()
        return MateStatusPacket.from_buffer(data)

def parse_hexstr(s):
    return ''.join([chr(int(x, 16)) for x in s.split()])


if __name__ == "__main__":
    # Testing
    data = parse_hexstr('03 81 80 82 00 6A 3F 01 00 1D 00 FF 02 40 03 8E')
    packet = MateInterface._parse_packet(data)
    status = MateStatusPacket.from_buffer(packet)
    print "status:", status

