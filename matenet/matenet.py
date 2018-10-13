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

from serial import Serial, PARITY_SPACE, PARITY_MARK, PARITY_ODD, PARITY_EVEN
from cstruct import struct
from time import sleep

# Delay between bytes when space/mark is not supported
# This is needed to ensure changing the parity between even/odd only affects one byte at a time
# (Essentially forces 1 byte in the TX buffer at a time)
FUDGE_FACTOR = 0.002 # seconds

# Amount of time with no communication that signifies the end of the packet
END_OF_PACKET_TIMEOUT = 0.02 # seconds

# Retry command this many times if we read back an invalid packet (eg. bad CRC)
RETRY_PACKET = 1

class MateNET(object):
    """
    Interface for the MATE RJ45 bus ("MateNET")
    This class only handles the low level protocol,
    it does not care what is attached to the bus.
    """
    TxPacket = struct('>BBHH', ('port', 'ptype', 'addr', 'param'))  # Payload is always 4 bytes?
    QueryPacket = struct('>HH', ('reg', 'param'))
    QueryResponse = struct('>H', ('value',))

    DEVICE_HUB = 1
    DEVICE_FX = 2
    DEVICE_MX = 3

    TYPE_QUERY = 2
    TYPE_CONTROL = 3
    TYPE_STATUS = 4
    TYPE_LOG = 22

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
        if self.supports_spacemark:
            self.ser.parity = (PARITY_MARK if bit8 else PARITY_SPACE)
            #sleep(0.5)
            self.ser.write(data)
            sleep(FUDGE_FACTOR)
            #sleep(0.5)
        else:
            # Emulate SPACE/MARK parity using EVEN/ODD parity
            for b in data:
                p = self._odd_parity(ord(b)) ^ bit8
                self.ser.parity = (PARITY_ODD if p else PARITY_EVEN)
                self.ser.write(b)
                sleep(FUDGE_FACTOR)

    def _send(self, data):
        """
        Send a packet to the MateNET bus
        :param data: str containing the raw data to send (excluding checksum)
        """
        checksum = self._calc_checksum(data)
        footer = chr((checksum >> 8) & 0xFF) + chr(checksum & 0xFF)

        # First byte has bit8 set (address byte)
        self._write_9b(data[0], 1)

        # Rest of the bytes have bit8 cleared (data byte)
        self._write_9b(data[1:] + footer, 0)

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
            raise RuntimeError("Error receiving mate packet - Received packet too small (%d bytes)" % (len(data)))

        # Checksum
        packet = data[0:-2]
        expected_chksum = (ord(data[-2]) << 8) | ord(data[-1])
        actual_chksum = MateNET._calc_checksum(packet)
        if actual_chksum != expected_chksum:
            raise RuntimeError("Error receiving mate packet - Invalid checksum (Expected:%d, Actual:%d)"
                               % (expected_chksum, actual_chksum))
        return packet

    def _recv(self, timeout=1.0):
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
        self.ser.timeout = END_OF_PACKET_TIMEOUT
        b = 1
        while b:
            b = self.ser.read()
            rawdata += b

        return MateNET._parse_packet(rawdata)

    def send(self, ptype, addr, param=0, port=0):
        """
        Send a MateNET packet to the bus (as if it was sent by a MATE unit) and return the response
        :param port: Port to send to, if a hub is present (0 if no hub or talking to the hub)
        :param ptype: Type of the packet
        :param param: Optional parameter (16-bit uint)
        :return: The raw response (str)
        """

        packet = MateNET.TxPacket(port, ptype, addr, param)
        data = None
        for i in range(RETRY_PACKET+1):
            try:
                self._send(packet.to_buffer())

                data = self._recv()
                if not data:
                    return None
                    
                break # Received successfully
            except:
                if i < RETRY_PACKET:
                    continue  # Transmission error - try again
                raise         # Retry limit reached

        # Validation
        if len(data) < 2:
            raise RuntimeError("Error receiving packet - not enough data received")

        #if data[0] != chr(0x03):  # Pretty sure this is always 0x03
        #    raise RuntimeError("Error receiving packet - invalid header")
        return data[1:]


class Mate(MateNET):
    """
    Emulates the MATE controller, allows communication with any attached devices
    """
    def __init__(self, comport, supports_spacemark=None):
        super(Mate, self).__init__(comport, supports_spacemark)

    def scan(self, port):
        """
        Scan for device attached to the specified port
        :param port: int, 0-10 (root:0)
        :return: int, the type of device that is attached (see MateNET.DEVICE_*)
        """
        result = self.query(0x00, port=port)
        return result

    def query(self, reg, param=0, port=0):
        """
        Query a register and retrieve its value
        :param reg: The register (16-bit address)
        :param param: Optional parameter
        :param port: Port (0-10)
        :return: The value (16-bit uint)
        """
        resp = self.send(MateNET.TYPE_QUERY, addr=reg, param=param, port=port)
        if resp:
            response = MateNET.QueryResponse.from_buffer(resp)
            return response.value

    def control(self, reg, value, port=0):
        """
        Control a register
        :param reg: The register (16-bit address)
        :param value: The value (16-bit uint)
        :param port: Port (0-10)
        :return: ???
        """
        resp = self.send(MateNET.TYPE_CONTROL, addr=reg, param=value, port=port)
        if resp:
            return None  # TODO: What kind of response do we get from a control packet?

    @property
    def revision(self):
        """
        :return: The revision of the attached device (Format "000.000.000")
        """
        a = self.query(0x0002)
        b = self.query(0x0003)
        c = self.query(0x0004)
        return '%.3d.%.3d.%.3d' % (a, b, c)
