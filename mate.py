# pyMate controller
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Allows communication with an Outback Systems MATE controller panel,
# which provides diagnostic information of current charge state and power use
#

import serial
import threading

class Value(object):
    """
    Formatted value with units
    Provides a way to represent a number with units such as Volts and Watts.
    """
    def __init__(self, value, units=None, resolution=0):
        self.value = float(value)
        self.units = units
        self.resolution = resolution
        self.fmt = "%%.%df" % resolution
        if self.units:
            self.fmt += str(self.units)

    def __str__(self):
        return self.fmt % self.value

    def __repr__(self):
        return self.__str__()

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)

class MXStatusPacket(object):
    """
    Represents an MX status packet, containing useful information
    such as charge current and PV voltage.
    """
    def __init__(self, packet):
        fields = packet.split(',')
        self.address = fields[0]
        # fields[1] unused
        self.charge_current = Value(float(fields[2]) + (float(fields[6]) / 10.0), 'A', resolution=1)
        self.pv_current = Value(fields[3], 'A', resolution=0)
        self.pv_voltage = Value(fields[4], 'V', resolution=0)
        self.daily_kwh = Value(float(fields[5]) / 10.0, 'kWh', resolution=1)
        self.aux_mode = fields[7]
        self.error_mode = fields[8]
        self.charger_mode = fields[9]
        self.bat_voltage = Value(float(fields[10]) / 10, 'V', resolution=1)
        self.daily_ah = Value(float(fields[11]), 'Ah', resolution=1)
        # fields[12] unused

        chk_expected = int(fields[13])
        chk_actual = sum(ord(x)-48 for x in packet[:-4] if ord(x)>=48)
        if chk_expected != chk_actual:
            raise Exception("Checksum error in received packet")


class MateController(object):
    """
    Interfaces with the MATE controller on a specific COM port.
    Must be a proper RS232 port with RTS/DTR pins.
    """
    def __init__(self, port, baudrate=19200):
        self.ser = serial.Serial(port, baudrate, timeout=2)

        # Provide power to the Mate controller
        self.ser.setDTR(True)
        self.ser.setRTS(False)

        self.ser.readline()

    def read_status(self):
        ln = self.ser.readline().strip()
        return MXStatusPacket(ln) if ln else None


if __name__ == "__main__":
    mate = MateController('COM19')
    status = mate.read_status()
    print status.__dict__
