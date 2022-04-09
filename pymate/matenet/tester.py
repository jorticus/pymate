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
# USAGE:
# python -m pymate.matenet.tester
#
__author__ = 'Jared'

import datetime
import logging
import time
from binascii import hexlify
from struct import pack

import settings
from pymate.packet_capture.wireshark_tap import WiresharkTap

from . import MateDevice, MateNET, MateNETPJON

log = logging.getLogger('mate')

class MateTester(MateNET):
    """
    Used to test a MATE controller
    (PC connected to MATE)
    EXPERIMENTAL
    """
    def send_packet(self, byte0, payload):
        """
        Send a MateNET packet
        :param payload: Packet payload (str)
        """
        data = chr(byte0) + payload
        log.info('TX     %.2x [%s]' % (
            byte0,
            ' '.join(('%.2x'%ord(c)) for c in payload)
        ))

        #log.info('TX: %s', hexlify(data))
        self.port.send(data)

        if self.tap:
            # Send the packet to the wireshark tap pipe
            # RX in this case is relative to the MATE
            data += '\xFF\xFF'  # Dummy checksum
            self.tap.capture_rx(data)

    def recv_packet(self, timeout=1.0):
        """
        Receive a MateNET packet
        :return: (port:int, type:int, payload:str) or None if no packet received
        """
        data = self.port.recv(timeout)
        if not data:
            return None

        port = ord(data[0])   # The port the device is connected to
        ptype = ord(data[1])  # Type of the packet
        payload = [ord(c) for c in data[2:]]

        PTYPES = {
            2: 'RD',
            3: 'WR',
            4: 'ST',
            22: 'LG'
        }
        #log.info('RX: %s', hexlify(data))
        log.info('\nRX P%.2x %s [%s]' % (
            port, 
            PTYPES.get(ptype), 
            ' '.join(('%.2x'%c) for c in payload)
        ))

        if self.tap:
            # Send the packet to the wireshark tap pipe
            # TX in this case is relative to the MATE
            data += '\xFF\xFF'  # Dummy checksum
            self.tap.capture_tx(data)

        return port, ptype, payload

    def run(self):
        while True:
            try:
                packet = self.recv_packet(timeout=5.0)
                if packet:
                    # print(f"Packet: [Port:{packet[0]} Type:{packet[1]} Payload:{packet[2]}]")

                    if not self.packet_received(packet):
                        # port, ptype, payload
                        print(f"Unhandled packet: [Port:{packet[0]:d} Type:{packet[1]:d} Payload:{packet[2]}]")
            except Exception as e:
                print(e)
                continue

    def packet_received(self, packet):
        """
        A packet has been received from the MATE.
        Decode it and try to figure out what to do with it.
        If we don't know what to do with it, return False and let any subclasses handle it
        """
        _, ptype, _ = packet
        if ptype == MateNET.TYPE_READ:
            self.packet_read(packet)
            return True
        elif ptype == MateNET.TYPE_WRITE:
            self.packet_write(packet)
            return True
        else:
            return False

    def packet_read(self, packet):
        """
        The MATE wants to read a register
        """
        port, _, payload = packet
        query = MateNET.QueryPacket.from_buffer(payload)
        #print(f"Query: {query}")
        log.info('Read[%.4x]', query.reg)

        result = self.process_read(port, query)
        if result is not None:
            self.send_packet(self.TYPE_READ, pack('>H', result))

    def packet_write(self, packet):
        """
        The MATE wants to write a register
        """
        port, _, payload = packet
        query = MateNET.QueryPacket.from_buffer(payload)
        #print(f"Control: {query}")
        log.info('Write[%.4x, %.4x]', query.reg, query.param)

        if query.reg == MateDevice.REG_TIME:
            return self.handle_time_update(query)
        if query.reg == MateDevice.REG_DATE:
            return self.handle_date_update(query)

        result = self.process_write(port, query)
        self.send_packet(self.TYPE_WRITE, pack('>H', result))

    def process_read(self, port, query):
        """
        Query a register, and return the value to the MATE
        (Override this in your subclass)
        """
        log.warning("Unknown query! (0x%.4x, port:%d)" % (query.reg, port))
        return 0

    def process_write(self, port, query):
        log.warning("Unknown control! (0x%.4x, port:%d)" % (query.reg, port))
        return 0

    def handle_time_update(self, query):
        self.send_packet(self.TYPE_WRITE, pack('>H', query.param))

        time = datetime.time(
            hour = ((query.param >> 11) & 0x1F),
            minute = ((query.param >> 5) & 0x3F),
            second = ((query.param & 0x1F) << 1)
        )
        print(f"Time: {time}")
        return True

    def handle_date_update(self, query):
        self.send_packet(self.TYPE_WRITE, pack('>H', query.param))

        date = datetime.date(
            year  = ((query.param >> 9) & 0x7F) + 2000,
            month = ((query.param >> 5) & 0x0F),
            day   = (query.param & 0x1F)
        )
        print(f"Date: {date}")
        return True


class MXEmulator(MateTester):
    """
    Emulates an MX charge controller, outputting dummy data
    so we can see how the MATE unit responds
    """
    DEVICE = MateNET.DEVICE_MX

    def packet_received(self, packet):
        # Let the superclass handle packets first
        handled = super(MXEmulator, self).packet_received(packet)
        if handled:
            return True

        # Unknown packet, try handle it ourselves:
        _, ptype, _ = packet
        if ptype == MateNET.TYPE_STATUS:
            self.packet_status(packet)
            return True
        elif ptype == MateNET.TYPE_LOG:
            self.packet_log(packet)
            return True
        return False

    def packet_status(self, packet):
        """
        The MATE wants a status packet, send it a dummy status packet
        to see the effect of various values
        """
        #print(f"Received status packet, sending dummy data. payload: {packet}")

        # self.send_packet(
        #     self.DEVICE, # NOTE: 1st byte is the device type for STATUS packets
        #     '\x81'  # Ah (upper)
        #     + '\x80'  # In current
        #     + '\x82'  # Out current
        #     + '\x00'  # kWH (signed, upper)
        #     + '\x00'  # Ah (lower)
        #     + '\x3F'
        #     + '\x02\x01'  # Status/Error
        #     + '\xF0'  # kWH (signed, lower)
        #     + '\x03\xE7'  # Bat voltage
        #     + '\x27\x0F'  # PV voltage
        # )
        # self.send_packet(
        #     self.DEVICE,
        #     "\x89\x84\x89\x00\x55\x3f\x02\x00\x15\x00\xfe\x02\xa8" # From real device (13 bytes)
        # )

        packet = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
        #packet = [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F]
        #packet = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        #packet = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD]
        #packet = [0x80, 0x82, 0xA0, 0xFF, 0xFF, 0xFF, 2, 0xFF, 0x05, 0x03, 0xE8, 0x00, 0x00]
        self.send_packet(self.DEVICE, ''.join(chr(c) for c in packet))

    def packet_log(self, packet):
        """
        The MATE wants to see a log entry
        """
        _, _, payload = packet
        query = MateNET.QueryPacket.from_buffer(payload)
        day = query.param
        log.info("Get log entry (day -%d)" % day)
        self.send_packet(self.TYPE_LOG, '\x02\xFF\x17\x01\x16\x3C\x00\x01\x01\x40\x00\x10\x10' + chr(day))
        #self.send_packet(self.TYPE_LOG, '\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF' + chr(day))
        #self.send_packet(self.TYPE_LOG, '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x48' + chr(day))

    def process_read(self, port, query):
        """
        The MATE wants to get the value of a register
        """
        # Get device type
        if query.reg == 0x0000:
            log.info("SCAN received, pretending to be an MX/CC")
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
            return super(MXEmulator, self).process_read(port, query)


class FXEmulator(MateTester):
    """
    Emulates an FX inverter, outputting dummy data
    so we can see how the MATE unit responds
    """
    DEVICE = MateNET.DEVICE_FX

    def packet_received(self, packet):
        # Let the superclass handle packets first
        handled = super(FXEmulator, self).packet_received(packet)
        if handled:
            return True

        # Unknown packet, try handle it ourselves:
        _, ptype, _ = packet
        if ptype == MateNET.TYPE_STATUS:
            self.packet_status(packet)
            return True
        return False

    def packet_status(self, packet):
        """
        The MATE wants a status packet, send it a dummy status packet
        to see the effect of various values
        """
        #print(f"Received status packet, sending dummy data. payload: {packet}")

        self.send_packet(
            self.DEVICE,
            "\x00\x00\x00\x03\x73\x00\x04\x00\x02\x01\x00\x09\x00" # From real device
            # '\x02\x28\x0A'
            # + '\x02\x01'
            # + '\x0A\x00\x64\x00\x00\xDC\x14\x0A'
        )

    def process_read(self, port, query):
        """
        The MATE wants to get the value of a register
        """
        # Get device type
        if query.reg == 0x0000:
            log.info("SCAN received, pretending to be an FX")
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
            #return 0xFF # All errors active
            return 0x00
        # Warnings
        elif query.reg == 0x0059:
            #return 0xFF
            return 0x00 # All warnings active

        # Disconn
        elif query.reg == 0x0084:
            return 0xFF
        # Sell
        elif query.reg == 0x008F:
            return 0xFF  # Stop sell reason

        else:
            return super(FXEmulator, self).process_read(port, query)


class FlexNETDCEmulator(MateTester):
    """
    Emulates a FlexNET DC monitor, outputting dummy data
    so we can see how the MATE unit responds
    """
    DEVICE = MateNET.DEVICE_FLEXNETDC

    def packet_received(self, packet):
        # Let the superclass handle packets first
        handled = super(FlexNETDCEmulator, self).packet_received(packet)
        if handled:
            return True
        
        # Unknown packet, try handle it ourselves:
        port, ptype, payload = packet
        if ptype == MateNET.TYPE_STATUS:
            query = MateNET.QueryPacket.from_buffer(payload)
            self.packet_status(port, query)
            return True
        return False

    def packet_status(self, port, query):
        """
        The MATE wants a status packet, send it a dummy status packet
        to see the effect of various values
        """
        #print("Received DC status packet (0x%x)" % query.reg)
        packet = None
        if query.reg == 0x0A:
            #packet = [0xff, 0xd7, 0x00, 0x12, 0x00, 0x00, 0x01, 0x02, 0x63, 0xff, 0xf5, 0x00, 0x05] # From real device
            #packet = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
            #packet = [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F]
            packet = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            #packet = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD]
            #packet = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x7F, 0x63, 0x00, 0x00, 0x00, 0x00]

            # - "SOC Critically Low" message is driven by SOC%
            # - DC NOW XX % (0x7F = 127%)
            # - DC NOW Voltage (0xFF7F = -12.7V)
            # - Shunt A/B Amps/kW
            # - Shunt C Amps

        elif query.reg == 0x0B:
            #packet = [0x00, 0x00, 0x01, 0x21, 0x00, 0x00, 0x00, 0x28, 0xff, 0xd8, 0x00, 0x00, 0x00] # From real device
            #packet = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
            #packet = [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F]
            packet = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            #packet = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD]
            #packet = [0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

            # - DC NOW In/Out/Bat Current (07F: 3263.9A)
            # - Fuel Guage
            # - DC BAT Current
            # - DC NOW In/Out kW -- In:26.390kW Out:27.670kW  
            #   Part of 'Out kW' is stored in another frame. When this is all 00, it reads 2.550kW
            # - 'Full charge settings met' flag
            # - Shunt C kW

        elif query.reg == 0x0C:
            #packet = [0x0a, 0xff, 0xf6, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01] # From real device
            #packet = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
            #packet = [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F]
            packet = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            #packet = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD]
            # - DC TODAY In/Out/Bat Current/kW (7F: 26.390kW)
            # - DC NOW Bat kW (26.390kW)

        elif query.reg == 0x0D:
            #packet = [0xff, 0xff, 0x00, 0x01, 0xff, 0xff, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00] # From real device
            #packet = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
            #packet = [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F]
            packet = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            #packet = [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F]
            #packet = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD]
            # - Days since full charge (63.)
            # - DC TODAY BAT KW (26.39kW)

        elif query.reg == 0x0E:
            #packet = [0x00, 0x00, 0x00, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] # From real device
            #packet = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
            #packet = [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F]
            packet = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            #packet = [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD]
            # - Shunt A/B AmpHours/kWH
            # - Shunt C kWH

        elif query.reg == 0x0F:
            #packet = [0x00, 0x00, 0x62, 0x00, 0x00, 0xff, 0xff, 0x13, 0x00, 0x00, 0x00, 0x00, 0x00] # From real device
            #packet = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
            #packet = [0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F]
            packet = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            #packet =  [0x00, 0x00, 50,   0x11, 0x22, 0x33, 0x44, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            #packet = [0x55, 0x66, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            # - DC TODAY MINSOC % (50%)
            # - DC BAT NET AH     (0x1122 : 4386AH)
            # - DC BAT NET KWH    (0x3344 : (6)31.24kWH (top digit truncated))
            # - ShuntC AH

        if packet:
            self.send_packet(self.DEVICE, ''.join(chr(c) for c in packet))

    def process_write(self, port, query):
        if query.reg == 0x4004:
            # This is sent periodically by the MATE to a DC, and increases with a specific pattern.
            # Unsure what it does, but if you don't reply, the MATE shows a COMMS error
            return query.param

        # RSOC reset?
        elif query.reg == 0x00D5: 
            return query.param

        # Don't use inherited registers,
        # but return the written value for any unhandled registers.
        return query.param

    def process_read(self, port, query):
        """
        The MATE wants to get the value of a register
        """
        # Get device type
        if query.reg == 0x0000:
            log.info("SCAN received, pretending to be a FlexNET DC")
            return self.DEVICE

        # Revision (2.3.4)
        elif query.reg == 0x0001:
            return 0  # Not sure what this is
        elif query.reg == 0x0002:
            return 11
        elif query.reg == 0x0003:
            return 22
        elif query.reg == 0x0004:
            return 33


        # State of charge
        elif query.reg == 0x00D5:
            return 33 # percent
        elif query.reg == 0x00D8:
            return 100

        # Don't use inherited registers
        return 0


class HubEmulator(MateTester):
    """
    Emulate a Hub, to see how it works
    """
    def __init__(self, port, *args, **kwargs):
        super(HubEmulator, self).__init__(port, *args, **kwargs)
        # Devices attached to this virtual hub:
        self.ports = {
            1: MXEmulator(self.port, *args, **kwargs),
            #2: MXEmulator(self.port, *args, **kwargs),
            2: FXEmulator(self.port, *args, **kwargs),
            3: FlexNETDCEmulator(self.port, *args, **kwargs)  # Requires an MX & FX
        }

    def get_device_at_port(self, port):
        device = self.ports.get(port)
        if device and isinstance(device, MateTester):
            return device
        return None

    def packet_received(self, packet):
        port, ptype, _ = packet
        if port == 0:
            return super(HubEmulator, self).packet_received(packet)

        else:
            # Forward packet to the respective device
            device = self.get_device_at_port(port)
            if device:
                return device.packet_received(packet)

    def process_read(self, port, query):
        # SCAN: What device is attached to the specified port?
        if query.reg == 0x0000:
            # Pretend to be a hub attached to port 0
            log.info("SCAN received, pretending to be a hub")
            return MateNET.DEVICE_HUB

        return None


if __name__ == "__main__":

    TAP_WIRESHARK = True
    
    #log.setLevel(logging.DEBUG)
    log.setLevel(logging.INFO)
    log.addHandler(logging.StreamHandler())

    if settings.SERIAL_PROTO == 'PJON':
        # NOTE: Use high baud rate to ensure we respond quickly enough for the MATE.
        # If you don't respond in time, MATE will get the hub port mappings wrong.
        port = MateNETPJON(settings.SERIAL_PORT, 1000000, target=0x0B)
    else:
        port = settings.SERIAL_PORT

    tap = None
    if TAP_WIRESHARK:
        tap =  WiresharkTap()
        tap.launch_wireshark(sideload_dissector=True)
        tap.open()
        time.sleep(2.0)
    
    unit = HubEmulator(port, tap=tap)
    #unit = MXEmulator(port)
    #unit = FXEmulator(port)
    #unit = FlexNETDCEmulator(port)

    try:
        log.info("Running")
        unit.run()

    finally:
        if tap: tap.close()
