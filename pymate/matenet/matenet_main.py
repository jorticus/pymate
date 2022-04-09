# pyMATE controller
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Emulates an Outback MATE controller panel, allowing direct communication with
# an attached device (no MATE needed!)
#


__author__ = 'Jared'

import logging
from time import sleep

from pymate.cstruct import struct
from serial import PARITY_EVEN, PARITY_MARK, PARITY_ODD, PARITY_SPACE, Serial

from . import MateNETPJON, MateNETSerial


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
    DEVICE_FLEXNETDC = 4
    DEVICE_DC = 4 # Alias of FLEXNETDC

    TYPE_QUERY = 2
    TYPE_CONTROL = 3
    TYPE_STATUS = 4
    TYPE_LOG = 22

    TYPE_READ = 2
    TYPE_WRITE = 3
    
    TYPE_DEC   = 0
    TYPE_DIS   = 0
    TYPE_INC   = 1
    TYPE_EN    = 1
    TYPE_READ  = 2
    TYPE_WRITE = 3

    DEVICE_TYPES = {
        DEVICE_HUB: 'Hub',
        DEVICE_MX:  'MX',
        DEVICE_FX:  'FX',
        DEVICE_FLEXNETDC: 'FLEXnet DC',
    }

    def __init__(self, port, supports_spacemark=None, tap=None):
        if isinstance(port, (MateNETSerial, MateNETPJON)):
            self.port = port
        else:
            self.port = MateNETSerial(port, supports_spacemark)

        self.log = logging.getLogger('mate.net')

        # Retry command this many times if we read back an invalid packet (eg. bad CRC)
        self.RETRY_PACKET = 2

        self.tap = tap

    def send(self, ptype, addr, param=0, port=0, response_len=None):
        """
        Send a MateNET packet to the bus (as if it was sent by a MATE unit) and return the response
        :param port: Port to send to, if a hub is present (0 if no hub or talking to the hub)
        :param ptype: Type of the packet
        :param param: Optional parameter (16-bit uint)
        :return: The raw response (str)
        """
        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug('Send [Port%d, Type=0x%.2x, Addr=0x%.4x, Param=0x%.4x]', port, ptype, addr, param)

        if response_len is not None:
            response_len += 1 # Account for command ack byte

        packet = MateNET.TxPacket(port, ptype, addr, param)

        for i in range(self.RETRY_PACKET+1):
            try:
                txbuf = packet.to_buffer()
                self.port.send(txbuf)

                rxbuf = self.port.recv(response_len)
                if not rxbuf:
                    self.log.debug('RETRY')
                    continue  # No response - try again
                    #return None

                if self.tap:
                    # Send the packet to the wireshark tap pipe, if present
                    
                    self.tap.capture(
                        txbuf+'\xFF\xFF', # Dummy checksum
                        rxbuf+'\xFF\xFF'  # Dummy checksum
                    )
                    
                break # Received successfully
            except:
                if i < self.RETRY_PACKET:
                    self.log.debug('RETRY')
                    continue  # Transmission error - try again

                if self.tap:
                    # No response, just capture the TX packet for wireshark
                    self.tap.capture_tx(txbuf+'\xFF\xFF')

                raise         # Retry limit reached

        if not rxbuf:
            return None

        if len(rxbuf) < 2:
            raise RuntimeError("Error receiving packet - not enough data received")

        if rxbuf[0] & 0x80 == 0x80:
            raise RuntimeError("Invalid command 0x%.2x" % (rxbuf[0] & 0x7F))
            
        return rxbuf[1:]

### Higher level protocol functions ###

    def query(self, reg, param=0, port=0):
        """
        Query a register and retrieve its value
        :param reg: The register (16-bit address)
        :param param: Optional parameter
        :return: The value (16-bit uint)
        """
        resp = self.send(MateNET.TYPE_QUERY, addr=reg, param=param, port=port, response_len=MateNET.QueryResponse.size)
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
        resp = self.send(MateNET.TYPE_CONTROL, addr=reg, param=value, port=port, response_len=MateNET.QueryResponse.size)
        if resp:
            return None  # TODO: What kind of response do we get from a control packet?

    def read(self, register, param=0, port=0):
        """
        Read a register
        """
        return self.query(register, param, port)

    def write(self, register, value, port=0):
        """
        Write to a register
        """
        return self.control(register, value, port)

    def scan(self, port=0):
        """
        Scan for device attached to the specified port
        :param port: int, 0-10 (root:0)
        :return: int, the type of device that is attached (see MateNET.DEVICE_*)
        """
        result = self.query(0x00, port=port)
        if result is not None:
            # TODO: Don't know what the upper byte is for, but it is seen on some MX units
            result = result & 0x00FF
        return result

    def enumerate(self):
        """
        Scan for device(s) on the bus.
        Returns a list of device types at each port location
        """
        devices = [0]*10
        
        # Port 0 will either be a device or a hub.
        devices[0] = self.query(0x00, port=0)
        if not devices[0]:
            raise Exception('No devices found on the bus')
        
        # Only scan for other devices if a hub is attached to port 0
        if devices[0] == MateNET.DEVICE_HUB:
            for i in range(1,len(devices)):
                self.log.info('Scanning port %d', i)
                devices[i] = self.query(0x00, port=i)
        
        return devices

    def find_device(self, device_type):
        """
        Find which port a device is connected to.

        Note: If you have a hub, you should fill the ports starting from 1,
        not leaving any gaps. Any empty ports will introduce delay as we wait 
        for a timeout.

        KeyError is thrown if the device is not connected.

        Usage:
        port = bus.find_device(MateNET.DEVICE_MX)
        mx = MateMXDevice(bus, port)
        """
        for i in range(0,10):
            dtype = self.scan(port=i)
            if dtype and dtype == device_type:
                self.log.info('Found %s device at port %d',
                    MateNET.DEVICE_TYPES[dtype],
                    i
                )
                return i
        raise KeyError('%s device not found' % MateNET.DEVICE_TYPES[device_type])
