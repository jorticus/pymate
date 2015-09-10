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

from matenet import MateNET
from struct import pack
from cstruct import struct

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


from util import bin2hexstr, hexstr2bin

QueryPacket = struct('>HBB', ('reg', 'param1', 'param2'))

def process_query(query):
    # Scan?
    if query.reg == 0x0000:
        print "SCAN received, pretending to be an MX/CC"
        return MateNET.DEVICE_MX

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
        print "Unknown query! (0x%.4x)" % query.reg

    return 0

def packet_query(tester, packet):
    _, _, payload = packet
    query = QueryPacket.from_buffer(payload)
    print "Query:", query

    result = process_query(query)
    tester.send_packet(pack('>H', result))

def packet_log(tester, packet):
    _, _, payload = packet
    query = QueryPacket.from_buffer(payload)


def packet_status(tester, packet):
    # Send a dummy status packet, to see the effect of various values
    print "Received status packet, sending dummy data"

    tester.send_packet(
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

if __name__ == "__main__":
    tester = MateTester('COM8')

    print "Reading packets:"
    while True:
        try:
            packet = tester.recv_packet(timeout=5.0)
            if packet:
                _, ptype, _ = packet
                if ptype == MateNET.TYPE_QUERY:
                    packet_query(tester, packet)
                elif ptype == MateNET.TYPE_STATUS:
                    packet_status(tester, packet)
                elif ptype == MateNET.TYPE_LOG:
                    packet_log(tester, packet)
                else:
                    print "Received:", packet
        except Exception as e:
            print e
            continue

# First boot
#Received: (0, 2, [0, 0, 0, 0])

# STATUS/CC/METER : Charger watts
#Received: (0, 2, [1, 106, 0, 0])

# : Charger kWhrs
# Received: (0, 2, [1, 234, 0, 0])

# STATUS/CC/METER : Charger Amps DC
#Received: (0, 2, [1, 199, 0, 0])

# STATUS/CC/METER : Battery voltage
#Received: (0, 2, [0, 8, 0, 0])

# STATUS/CC/METER : Panel voltage
#Received: (0, 2, [1, 198, 0, 0])

# STATUS/CC/METER : Revision
#Received: (0, 2, [0, 0, 0, 0])
#Received: (0, 2, [0, 2, 0, 0])
#Received: (0, 2, [0, 3, 0, 0])
#Received: (0, 2, [0, 4, 0, 0])

# STATUS/CC/MODE
#Received: (0, 2, [1, 200, 0, 0])

# : Aux relay mode & : Aux relay state
#Received: (0, 2, [1, 201, 0, 0])

# STATUS/CC/LOG1
# Contains AH/kWH/Vp/Ap/kWp, min/max battery voltage, absorb/float time
#Received: (0, 22, [0, 0, 0, 0])
#Received: (0, 22, [0, 0, 0, 0])
#Received: (0, 22, [0, 0, 0, 4])
#Received: (0, 22, [0, 0, 0, 4])
#                            ^day

# STATUS/CC/STAT : Maximum battery
#Received: (0, 2, [0, 15, 0, 0])

# : voc
#Received: (0, 2, [0, 16, 0, 0])

# : max voc
#Received: (0, 2, [0, 18, 0, 0])

# : maximum wattage
#Received: (0, 2, [0, 21, 0, 0])

# : total kWH DC
#Received: (0, 2, [0, 19, 0, 0])

# : total kAH
#Received: (0, 2, [0, 20, 0, 0])

# AC INPUT CONTROL
# Drop: Received: (1, 3, [0, 58, 0, 0])
# Use: Received: (1, 3, [0, 58, 0, 1])

# INVERTER CONTROL
# OFF: Received: (255, 3, [0, 61, 0, 0])
# SRCH: Received: (255, 3, [0, 61, 0, 1])
# ON: Received: (255, 3, [0, 61, 0, 2])


# Also, we intermittently receive the following packet:
#Received: (0, 3, [64, 4, 146, 233])