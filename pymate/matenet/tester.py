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

from . import MateNET
from struct import pack


class MateTester(MateNET):
    """
    Used to test a MATE controller
    (PC connected to MATE)
    EXPERIMENTAL
    """
    def send_packet(self, payload):
        """
        Send a MateNET packet
        :param payload: Packet payload (str)
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
            #try:
                packet = self.recv_packet(timeout=5.0)
                if packet:
                    self.packet_received(packet)
            #except Exception as e:
            #    print(e)
            #    continue

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
        query = MateNET.QueryPacket.from_buffer(payload)
        print("Query:", query)

        result = self.process_query(port, query)
        self.send_packet(pack('>H', result))

    def process_query(self, port, query):
        """
        Query a register, and return the value to the MATE
        (Override this in your subclass)
        """
        print("Unknown query! (0x%.4x, port:%d)" % (query.reg, port))
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
                print("Received:", packet)
                return False

    def packet_status(self, packet):
        """
        The MATE wants a status packet, send it a dummy status packet
        to see the effect of various values
        """
        print("Received status packet, sending dummy data. payload:", packet)

        self.send_packet(
            '\x81'  # Ah (upper)
            + '\x80'  # In current
            + '\x82'  # Out current
            + '\x00'  # kWH (signed, upper)
            + '\x00'  # Ah (lower)
            + '\x3F'
            + '\x02\x01'  # Status/Error
            + '\xF0'  # kWH (signed, lower)
            + '\x03\xE7'  # Bat voltage
            + '\x27\x0F'  # PV voltage
        )

    def packet_log(self, packet):
        """
        The MATE wants to see a log entry
        """
        _, _, payload = packet
        query = MateNET.QueryPacket.from_buffer(payload)
        day = query.param
        print("Get log entry (day -%d)" % day)
        self.send_packet('\x02\xFF\x17\x01\x16\x3C\x00\x01\x01\x40\x00\x10\x10' + chr(day))
        #self.send_packet('\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF' + chr(day))
        #self.send_packet('\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x48' + chr(day))

    def process_query(self, port, query):
        """
        The MATE wants to get the value of a register
        """
        # Get device type
        if query.reg == 0x0000:
            print("SCAN received, pretending to be an MX/CC")
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
            return 4  # Equalize
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
            return super(MXEmulator, self).process_query(port, query)


class FXEmulator(MateTester):
    """
    Emulates an FX inverter, outputting dummy data
    so we can see how the MATE unit responds
    """
    DEVICE = MateNET.DEVICE_FX

    def packet_received(self, packet):
        # Let the superclass handle packets first
        handled = super(FXEmulator, self).packet_received(packet)

        # Unknown packet, try handle it ourselves:
        if not handled:
            _, ptype, _ = packet
            if ptype == MateNET.TYPE_STATUS:
                self.packet_status(packet)
                return True
            else:
                print("Received:", packet)
                return False

    def packet_status(self, packet):
        """
        The MATE wants a status packet, send it a dummy status packet
        to see the effect of various values
        """
        print("Received status packet, sending dummy data. payload:", packet)

        self.send_packet(
            '\x02\x28\x0A'
            + '\x02\x01'
            + '\x0A\x00\x64\x00\x00\xDC\x14\x0A'
        )

    def process_query(self, port, query):
        """
        The MATE wants to get the value of a register
        """
        # Get device type
        if query.reg == 0x0000:
            print("SCAN received, pretending to be an FX")
            return self.DEVICE

        # Revision (2.3.4)
        elif query.reg == 0x0002:
            return 11
        elif query.reg == 0x0003:
            return 22
        elif query.reg == 0x0004:
            return 33

        ##### STATUS/FX/MODE #####
        # Inverter control
        elif query.reg == 0x003D:
            # 0: OFF
            # 1: Search
            # 2: ON
            return 1
        # AC IN control
        elif query.reg == 0x003A:
            # 0: Drop
            # 1: Use
            return 1
        # Charge control
        elif query.reg == 0x003C:
            # 0: Off
            # 1: Auto
            # 2: On
            return 2
        # AUX control
        elif query.reg == 0x005A:
            # 0: Off
            # 1: Auto
            # 2: On
            return 1
        # EQ enabled
        elif query.reg == 0x0038:
            return 0  # TODO: Can't get this to change the value??

        ##### STATUS/FX/METER #####
        # Output voltage (VAC) (*2)
        elif query.reg == 0x002D:
            return 11  # 22V
        # Input voltage (VAC) (*2)
        elif query.reg == 0x002C:
            return 22  # 44V
        # Inverter current (AAC) (/2)
        elif query.reg == 0x006D:
            return 33  # 16.5A
        # Charger current (AAC) (/2)
        elif query.reg == 0x006A:
            return 44  # 22.0A
        # Input current (AAC) (/2)
        elif query.reg == 0x006C:
            return 55  # 27.5A
        # Sell current (AAC) (/2)
        elif query.reg == 0x006B:
            return 66  # 33.0A

        ##### STATUS/FX/BATT #####
        # Battery actual (VDC)
        elif query.reg == 0x0019:
            return 77
        # Battery temp compensated (VDC)
        elif query.reg == 0x0016:
            return 88
        # Absorb setpoint (VDC)
        elif query.reg == 0x000B:
            return 99
        # Absorb time remaining (Hours)
        elif query.reg == 0x0070:
            return 111
        # Float setpoint (VDC)
        elif query.reg == 0x000A:
            return 122
        # Float time remaining (Hours)
        elif query.reg == 0x006E:
            return 133
        # Re-float setpoint (VDC)
        elif query.reg == 0x000D:
            return 144
        # Equalize setpoint (VDC)
        elif query.reg == 0x000C:
            return 155
        # Equalize time remaining (Hours)
        elif query.reg == 0x0071:
            return 166
        # Battery temp (Not in degree C/F)
        elif query.reg == 0x0032:
            return 177
        # Warnings > Airtemp (0-255)
        elif query.reg == 0x0033:
            return 200
        # Warnings > FET temp
        elif query.reg == 0x0034:
            return 211
        # Warnings > Cap temp
        elif query.reg == 0x0035:
            return 222

        ##### STATUS/FX #####
        # Errors
        elif query.reg == 0x0039:
            return 0xFF
        # Warnings
        elif query.reg == 0x0059:
            return 0xFF

        # Disconn
        elif query.reg == 0x0084:
            return 0xFF
        # Sell
        elif query.reg == 0x008F:
            return 0xFF  # Stop sell reason

        else:
            return super(FXEmulator, self).process_query(port, query)


class FlexNETDCEmulator(MateTester):
    """
    Emulates a FlexNET DC monitor, outputting dummy data
    so we can see how the MATE unit responds
    """
    DEVICE = MateNET.DEVICE_FX

    def packet_received(self, packet):
        # Let the superclass handle packets first
        handled = super(FlexNETDCEmulator, self).packet_received(packet)

        # Unknown packet, try handle it ourselves:
        if not handled:
            _, ptype, _ = packet
            if ptype == MateNET.TYPE_STATUS:
                self.packet_status(packet)
                return True
            else:
                print("Received:", packet)
                return False

    def packet_status(self, packet):
        """
        The MATE wants a status packet, send it a dummy status packet
        to see the effect of various values
        """
        print("Received status packet, sending dummy data. payload:", packet)

        self.send_packet('\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

    def process_query(self, port, query):
        """
        The MATE wants to get the value of a register
        """
        # Get device type
        if query.reg == 0x0000:
            print("SCAN received, pretending to be a FlexNET DC")
            return 4 #self.DEVICE

        # Revision (2.3.4)
        elif query.reg == 0x0002:
            return 11
        elif query.reg == 0x0003:
            return 22
        elif query.reg == 0x0004:
            return 33
        return 0


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
                print("Received:", packet)
        else:
            # Redirect to the correct device class
            device = self.get_device_at_port(port)
            if device:
                #print("Forwarding packet to", device)
                # TODO: Unsure if port needs to be set to 0
                return device.packet_received(packet)
            else:
                print("Warning: No device attached to port", port)
                return False

    def process_query(self, port, query):
        # SCAN: What device is attached to the specified port?
        if query.reg == 0x0000:
            # Pretend to be a hub attached to port 0
            if port == 0:
                print("SCAN received, pretending to be a hub")
                return MateNET.DEVICE_HUB
            # Dynamically look up what's attached to the other ports
            else:
                print("SCAN hub port %d" % port)
                device = self.get_device_at_port(port)
                if device:
                    print(device, "attached to port", port)
                    return device.DEVICE
                return 0  # No device attached to this port
        else:
            if port != 0:  # Need to forward queries for other ports to their respective devices
                device = self.get_device_at_port(port)
                if device:
                    # TODO: Unsure if port needs to be set to 0
                    return device.process_query(port, query)
        return 0


if __name__ == "__main__":
    comport = 'COM8'
    #unit = HubEmulator(comport)
    unit = MXEmulator(comport)
    #unit = FXEmulator(comport)
    #unit = FlexNETDCEmulator(comport)

    print("Running")
    unit.run()


# TODO: we intermittently receive the following packet:
#Received: (0, 3, [64, 4, 146, 233]) 40 04 92 E9
