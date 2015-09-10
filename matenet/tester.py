# pyMATE tester
# Author: Jared Sanson <jared@jared.geek.nz>
#
# NOTE:
# This assumes the PC is connected to a MATE, instead of pretending to be a MATE.
# Thus RX/TX must be swapped.
#
# This pretends to be an MX device so we can test the MATE unit without
# needing it to be connected to the unit.
#
__author__ = 'Jared'

from abc import abstractmethod
from matenet import MateNET
from struct import pack
from cstruct import struct

from util import bin2hexstr, hexstr2bin

QueryPacket = struct('>HBB', ('reg', 'param1', 'param2'))


class MateTester(MateNET):
    """
    Used to test a MATE controller
    (PC connected to MATE)
    EXPERIMENTAL
    """
    def send_packet(self, payload):
        """
        Send a MateNET packet
        :param ptype: Type of the packet (int)
        :param payload: Packet payload (array of bytes)
        """
        data = chr(0x03) + payload  # TODO: not sure why 0x03 here
        self._send(data)

    def recv_packet(self, timeout=1.0):
        """
        Receive a MateNET packet
        :return: (port:int, type:int, payload:str) or None if no packet received
        """
        data = self._recv(timeout)
        if not data:
            return None

        port = ord(data[0])   # I think this is the port the device is connected to?
        ptype = ord(data[1])  # Type of the packet
        payload = [ord(c) for c in data[2:]]
        return port, ptype, payload

    def run(self):
        while True:
            try:
                packet = self.recv_packet(timeout=5.0)
                if packet:
                    self.packet_received(packet)
            except Exception as e:
                print e
                continue

    def packet_received(self, packet):
        """
        A packet has been received from the MATE.
        Decode it and try to figure out what to do with it.
        If we don't know what to do with it, return False and let any subclasses handle it
        """
        _, ptype, _ = packet
        if ptype == MateNET.TYPE_QUERY:
            self.packet_query(packet)
            return True
        else:
            return False

    def packet_query(self, packet):
        """
        The MATE wants to query a register
        """
        port, _, payload = packet
        query = QueryPacket.from_buffer(payload)
        print "Query:", query

        result = self.process_query(port, query)
        self.send_packet(pack('>H', result))

    def process_query(self, query):
        """
        Query a register, and return the value to the MATE
        (Override this in your subclass)
        """
        print "Unknown query! (0x%.4x, port:%d)" % (query.reg, port)
        return 0

class MXEmulator(MateTester):
    """
    Emulates an MX charge controller, outputting dummy data
    so we can see how the MATE unit responds
    """
    DEVICE = MateNET.DEVICE_MX

    def packet_received(self, packet):
        # Let the superclass handle packets first
        handled = super(MXEmulator, self).packet_received(packet)

        # Unknown packet, try handle it ourselves:
        if not handled:
            _, ptype, _ = packet
            if ptype == MateNET.TYPE_STATUS:
                self.packet_status(packet)
                return True
            elif ptype == MateNET.TYPE_LOG:
                self.packet_log(packet)
                return True
            else:
                print "Received:", packet
                return False

    def packet_status(self, packet):
        """
        The MATE wants a status packet, send it a dummy status packet
        to see the effect of various values
        """
        print "Received status packet, sending dummy data"

        self.send_packet(
            '\x81'  # Ah (upper)
            +'\x80' # In current
            +'\x82' # Out current
            +'\x00' # kWH (signed, upper)
            +'\x00' # Ah (lower)
            +'\x3F'
            +'\x02\x01' # Status/Error
            +'\xF0' # kWH (signed, lower)
            +'\x03\xE7' # Bat voltage
            +'\x27\x0F' # PV voltage
        )

    def packet_log(self, packet):
        """
        The MATE wants to see a log entry
        TODO: I don't know what format the MATE expects - need to capture some field data
        """
        _, _, payload = packet
        query = QueryPacket.from_buffer(payload)
        print "Note: Log emulation not yet implemented"

    def process_query(self, port, query):
        """
        The MATE wants to get the value of a register
        """
        # Get device type
        if query.reg == 0x0000:
            print "SCAN received, pretending to be an MX/CC"
            return self.DEVICE

        ##### STATUS/CC/METER #####
        # Charger Watts (1)
        elif query.reg == 0x016A:
            return 44
        # Charger kWh (1/10)
        elif query.reg == 0x01EA:
            return 55
        # Charger amps DC (-128..127, 0=128)
        elif query.reg == 0x01c7:
            return 128  # 0
        # Battery voltage (1/10)
        elif query.reg == 0x0008:
            return 77
        # Panel voltage (1)
        elif query.reg == 0x01C6:
            return 88

        # Revision (2.3.4)
        elif query.reg == 0x0002:
            return 11
        elif query.reg == 0x0003:
            return 22
        elif query.reg == 0x0004:
            return 33

        ##### STATUS/CC/MODE #####
        # Mode (0..4)
        elif query.reg == 0x01C8:
            return 4 # Equalize
        # Aux Relay Mode / Aux Relay State
        elif query.reg == 0x01C9:
            # bit 7: relay state
            # bit 6..0: relay mode
            #   0: Float
            #   1: Diversion: Relay
            #   2: Diversion: Solid St
            #   3: Low batt disconnect
            #   4: Remote
            #   5: Vent fan
            #   6: PV Trigger
            #   7: Error output
            #   8: Night light
            return 0x86  # Relay on, PV Trigger

        ##### STATUS/CC/STAT #####
        # Maximum battery (1/10)
        elif query.reg == 0x000F:
            return 111
        # VOC (1/10)
        elif query.reg == 0x0010:
            return 122
        # Max VOC (1/10)
        elif query.reg == 0x0012:
            return 133
        # Total kWH DC (1)
        elif query.reg == 0x0013:
            return 144
        # Total kAH (1/10)
        elif query.reg == 0x0014:
            return 155
        # Max wattage (1)
        elif query.reg == 0x0015:
            return 166

        ##### STATUS/CC/SETPT #####
        # Absorb (1/10)
        elif query.reg == 0x0170:
            return 177
        # Float (1/10)
        elif query.reg == 0x0172:
            return 188

        else:
            super(MXEmulator, self).process_query(query)


class HubEmulator(MateTester):
    """
    Emulate a Hub, to see how it works
    """
    def __init__(self, comport):
        super(HubEmulator, self).__init__(comport)
        # Devices attached to this virtual hub:
        self.ports = {
            1: MXEmulator(self.ser),
            2: MXEmulator(self.ser),
        }

    def get_device_at_port(self, port):
        device = self.ports.get(port)
        if device and isinstance(device, MateTester):
            return device
        return None

    def packet_received(self, packet):
        port, ptype, _ = packet
        if ptype == MateNET.TYPE_QUERY or port == 0:
            # Let the superclass handle packets first
            handled = super(HubEmulator, self).packet_received(packet)

            # Unknown packet, try handle it ourselves:
            if not handled:
                print "Received:", packet
        else:
            # Redirect to the correct device class
            device = self.get_device_at_port(port)
            if device:
                #print "Forwarding packet to", device
                # TODO: Unsure if port needs to be set to 0
                return device.packet_received(packet)
            else:
                print "Warning: No device attached to port", port
                return False

    def process_query(self, port, query):
        # SCAN: What device is attached to the specified port?
        if query.reg == 0x0000:
            # Pretend to be a hub attached to port 0
            if port == 0:
                print "SCAN received, pretending to be a hub"
                return MateNET.DEVICE_HUB
            # Dynamically look up what's attached to the other ports
            else:
                print "SCAN hub port %d" % port
                device = self.get_device_at_port(port)
                if device:
                    print device, "attached to port", port
                    return device.DEVICE
                return 0  # No device attached to this port
        else:
            if port != 0:  # Need to forward queries for other ports to their respective devices
                device = self.get_device_at_port(port)
                if device:
                    # TODO: Unsure if port needs to be set to 0
                    device.process_query(query)



if __name__ == "__main__":
    unit = HubEmulator('COM8')

    print "Running"
    unit.run()


# STATUS/CC/LOG1
# Contains AH/kWH/Vp/Ap/kWp, min/max battery voltage, absorb/float time
#Received: (0, 22, [0, 0, 0, 0])
#Received: (0, 22, [0, 0, 0, 0])
#Received: (0, 22, [0, 0, 0, 4])
#Received: (0, 22, [0, 0, 0, 4])
#                            ^day

# AC INPUT CONTROL
# Drop: Received: (1, 3, [0, 58, 0, 0])
# Use: Received: (1, 3, [0, 58, 0, 1])

# INVERTER CONTROL
# OFF: Received: (255, 3, [0, 61, 0, 0])
# SRCH: Received: (255, 3, [0, 61, 0, 1])
# ON: Received: (255, 3, [0, 61, 0, 2])


# Also, we intermittently receive the following packet:
#Received: (0, 3, [64, 4, 146, 233])