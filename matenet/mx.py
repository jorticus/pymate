# pyMATE MX interface
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Provides access to an Outback MX solar charge controller
#

__author__ = 'Jared'

from struct import Struct
from value import Value
from matenet import Mate

class MXStatusPacket(object):
    fmt = Struct('>BbbbBBBBBHH')

    STATUS_SLEEPING = 0
    STATUS_FLOATING = 1
    STATUS_BULK = 2
    STATUS_ABSORB = 3
    STATUS_EQUALIZE = 4

    def __init__(self):
        self.amp_hours = None
        self.kilowatt_hours = None
        self.pv_current = None
        self.bat_current = None
        self.pv_voltage = None
        self.bat_voltage = None
        self.status = None
        self.errors = None

    @classmethod
    def from_buffer(cls, data):
        values = cls.fmt.unpack(data)
        status = MXStatusPacket()
        # Gaahh their protocol is messed up
        # The following was determined by poking values at the MATE unit...
        raw_ah = ((values[0] & 0x70) >> 4) | values[4]
        status.amp_hours = Value(raw_ah, units='Ah', resolution=0)
        status.pv_current = Value((128 + values[1]) % 256, units='A', resolution=0)
        status.bat_current = Value((128 + values[2]) % 256, units='A', resolution=0)
        raw_kwh = (values[3] << 8) | values[8]  # whyyyy
        status.kilowatt_hours = Value(raw_kwh / 10.0, units='kWh', resolution=1)
        # TODO: values[5] - Kilowatts peak??
        status.status = values[6]
        status.errors = values[7]
        status.bat_voltage = Value(values[9] / 10.0, units='V', resolution=1)
        status.pv_voltage = Value(values[10] / 10.0, units='V', resolution=1)
        return status

    def __repr__(self):
        return "<MXStatusPacket>"

    def __str__(self):
        fmt = \
"""MXStatus:
    PV:  {pv_voltage} {pv_current}
    Bat: {bat_voltage} {bat_current}
    Today: {kilowatt_hours} {amp_hours}
"""
        return fmt.format(**self.__dict__)


class MateMX(Mate):
    """
    Communicate with an MX unit attached to the MateNET bus
    """
    def get_status(self):
        """
        Request a status packet from the controller
        :return: A MXStatusPacket
        """
        resp = self.send(Mate.TYPE_STATUS, addr=1, param=0x00)
        # TODO: Unsure what the payload is supposed to do
        # param is 00 with no hub attached, or FF with a hub attached?

        if resp:
            return MXStatusPacket.from_buffer(resp[1:])

    @property
    def charger_watts(self):
        return Value(self.query(0x016A), units='W', resolution=0)

    @property
    def charger_kwh(self):
        return Value(self.query(0x01EA) / 10.0, units='kWh', resolution=1)

    @property
    def charger_amps_dc(self):
        return Value(self.query(0x01C7) - 128, units='A', resolution=0)

    @property
    def bat_voltage(self):
        return Value(self.query(0x0008) / 10.0, units='V', resolution=1)

    @property
    def panel_voltage(self):
        return Value(self.query(0x01C6), units='V', resolution=0)

    @property
    def status(self):
        return self.query(0x01C8)

    @property
    def aux_relay_mode(self):
        x = self.query(0x01C9)
        mode = x & 0x7F
        on = (x & 0x80 == 0x80)
        return mode, on

    @property
    def max_battery(self):
        return Value(self.query(0x000F) / 10.0, units='V', resolution=1)

    @property
    def voc(self):
        return Value(self.query(0x0010) / 10.0, resolution=1)

    @property
    def max_voc(self):
        return Value(self.query(0x0012) / 10.0, resolution=1)

    @property
    def total_kwh_dc(self):
        return Value(self.query(0x0013), units='kWh', resolution=0)

    @property
    def total_kah(self):
        return Value(self.query(0x0014), units='kAh', resolution=1)

    @property
    def max_wattage(self):
        return Value(self.query(0x0015), units='W', resolution=0)

    @property
    def setpt_absorb(self):
        return Value(self.query(0x0170) / 10.0, units='V', resolution=1)

    @property
    def setpt_float(self):
        return Value(self.query(0x0172) / 10.0, units='V', resolution=1)


if __name__ == "__main__":
    status = MXStatusPacket.from_buffer('\x85\x82\x85\x00\x69\x3f\x01\x00\x1d\x01\x0c\x02\x6a')
    print status
