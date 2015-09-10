# pyMATE FX interface
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Provides access to an Outback FX inverter
#

__author__ = 'Jared'

from value import Value
from struct import Struct
from matenet import MateNET

class FXStatusPacket(object):
    fmt = Struct('>BBBBBBBBHBB')

    def __init__(self, a=None, b=None, c=None, l=None, i=None, z=None, error=None, bat_voltage=None):
        # TODO: Determine what these variables represent
        self.a = a
        self.l = l  # Line voltage?
        self.i = i  # Inverter voltage?
        self.c = c  # Inverter current?
        self.b = b  # Line current?
        self.z = z
        self.error = error
        self.bat_voltage = bat_voltage

        # Calculations
        self.inv_power = Value((self.i * self.c) / 1000.0, units='kW', resolution=2)
        self.buy_power = Value((self.l * self.b) / 1000.0, units='kW', resolution=2)
        self.chg_power = Value((self.l * self.a) / 1000.0, units='kW', resolution=2)
        self.zer_power = Value((self.z * self.i) / 1000.0, units='kW', resolution=2)

    @classmethod
    def from_buffer(cls, data):
        values = cls.fmt.unpack(data)

        return FXStatusPacket(
            a=values[0],
            l=values[1],
            #values[2] # TODO
            #values[3] # TODO
            z=values[4],
            #values[5] # TODO
            i=values[6],
            error=bool(values[7] != 0),
            bat_voltage=Value(values[8] / 10.0, units='V', resolution=1),
            c=values[9],
            b=values[10]
        )

    def __repr__(self):
        return "<FXStatusPacket>"

    def __str__(self):
        fmt = \
"""FX Status:
    Battery: {bat_voltage}
    Inv: {inv_power} Zer: {zer_power}
    Chg: {chg_power} Buy: {buy_power}
"""
        return fmt.format(**self.__dict__)

class MateFX(MateNET):
    """
    Communicate with an FX unit attached to the MateNET bus
    """
    def get_status(self):
        """
        Request a status packet from the inverter
        :return: A FXStatusPacket
        """
        resp = self.send(MateNET.TYPE_STATUS, addr=1)
        if resp:
            return FXStatusPacket.from_buffer(resp[1:])

if __name__ == "__main__":
    status = FXStatusPacket.from_buffer('\x28\x0A\x00\x00\x0A\x00\x64\x00\x00\xDC\x14\x0A')
    print status
