# pyMATE controller
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Emulates an Outback MATE controller panel, allowing direct communication with
# an attached device (no MATE needed!)
#


__author__ = 'Jared'

from serial import Serial, PARITY_SPACE, PARITY_MARK, PARITY_ODD, PARITY_EVEN
from pymate.cstruct import struct
from .matenet_ser import MateNETSerial
from .matenet_pjon import MateNETPJON
from time import sleep
import logging

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

    DEVICE_TYPES = {
        DEVICE_HUB: 'Hub',
        DEVICE_MX:  'MX',
        DEVICE_FX:  'FX'
    }

    def __init__(self, port, supports_spacemark=None):
        if isinstance(port, (MateNETSerial, MateNETPJON)):
            self.port = port
        else:
            self.port = MateNETSerial(port, supports_spacemark)

        self.log = logging.getLogger('mate.net')

        # Retry command this many times if we read back an invalid packet (eg. bad CRC)
        self.RETRY_PACKET = 2

    def send(self, ptype, addr, param=0, port=0):
        """
        Send a MateNET packet to the bus (as if it was sent by a MATE unit) and return the response
        :param port: Port to send to, if a hub is present (0 if no hub or talking to the hub)
        :param ptype: Type of the packet
        :param param: Optional parameter (16-bit uint)
        :return: The raw response (str)
        """
        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug('Send [Port%d, Type=0x%.2x, Addr=0x%.4x, Param=0x%.4x]', port, ptype, addr, param)

        packet = MateNET.TxPacket(port, ptype, addr, param)
        data = None
        for i in range(self.RETRY_PACKET+1):
            try:
                self.port.send(packet.to_buffer())

                data = self.port.recv()
                if not data:
                    self.log.debug('RETRY')
                    continue  # No response - try again
                    #return None
                    
                break # Received successfully
            except:
                if i < self.RETRY_PACKET:
                    self.log.debug('RETRY')
                    continue  # Transmission error - try again
                raise         # Retry limit reached

        if not data:
            return None

        # Validation
        if len(data) < 2:
            raise RuntimeError("Error receiving packet - not enough data received")

        if ord(data[0]) & 0x80 == 0x80:
            raise RuntimeError("Invalid command 0x%.2x" % (ord(data[0]) & 0x7F))
            
        return data[1:]

### Higher level protocol functions ###

    def query(self, reg, param=0, port=0):
        """
        Query a register and retrieve its value
        :param reg: The register (16-bit address)
        :param param: Optional parameter
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

    def scan(self, port=0):
        """
        Scan for device attached to the specified port
        :param port: int, 0-10 (root:0)
        :return: int, the type of device that is attached (see MateNET.DEVICE_*)
        """
        result = self.query(0x00, port=port)
        if result is not None:
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
            dtype = self.query(0x00, port=i)
            if dtype and dtype == device_type:
                self.log.info('Found %s device at port %d',
                    MateNET.DEVICE_TYPES[dtype],
                    i
                )
                return i
        raise KeyError('%s device not found' % MateNET.DEVICE_TYPES[device_type])
