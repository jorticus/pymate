# pyMATE MX interface
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Provides access to an Outback MX solar charge controller
#

__author__ = 'Jared'

from struct import Struct
from pymate.value import Value
from . import MateDevice, MateNET


class MXStatusPacket(object):
    fmt = Struct('>BbbbBBBBBHH')

    STATUS_SLEEPING = 0
    STATUS_FLOATING = 1
    STATUS_BULK = 2
    STATUS_ABSORB = 3
    STATUS_EQUALIZE = 4

    # NOTE: MX Manual doesn't match real-world values:
    AUX_MODE_DIVERSION_RELAY = 1 
    AUX_MODE_REMOTE = 4
    AUX_MODE_VENTFAN = 5
    AUX_MODE_PVTRIGGER = 6
    AUX_MODE_FLOAT = 0
    AUX_MODE_ERROR_OUT = 7
    AUX_MODE_NIGHT_LIGHT = 8
    AUX_MODE_PWM_DIVERSION = 2
    AUX_MODE_LOW_BATTERY = 3
    AUX_MODE_MANUAL = 0x3F  # If Aux is not configured for Auto on MX unit.

    def __init__(self):
        self.amp_hours = None
        self.kilowatt_hours = None
        self.pv_current = None
        self.bat_current = None
        self.pv_voltage = None
        self.bat_voltage = None
        self.status = None
        self.errors = None
        self.aux_state = None
        self.aux_mode = None
        self.raw = None

    @classmethod
    def from_buffer(cls, data):
        values = cls.fmt.unpack(data)
        status = MXStatusPacket()
        # The following was determined by poking values at the MATE unit...
        raw_ah = ((values[0] & 0x70) >> 4) | values[4] # Ignore bit7 (if 0, MATE hides the AH reading)
        bat_current_milli = (values[0] & 0x0F) / 10.0
        status.amp_hours = Value(raw_ah, units='Ah', resolution=0)
        status.pv_current = Value((128 + values[1]) % 256, units='A', resolution=0)
        status.bat_current = Value(((128 + values[2]) % 256 + bat_current_milli), units='A', resolution=1)
        raw_kwh = (values[3] << 8) | values[8]
        status.kilowatt_hours = Value(raw_kwh / 10.0, units='kWh', resolution=1)
        status.aux_state = ((values[5] & 0x40) == 0x40)  # 0: Off, 1: On
        status.aux_mode = (values[5] & 0x3F)
        status.status = values[6]
        status.errors = values[7]
        status.bat_voltage = Value(values[9] / 10.0, units='V', resolution=1)
        status.pv_voltage = Value(values[10] / 10.0, units='V', resolution=1)

        # Also add the raw packet, in case any of the above changes
        status.raw = data

        return status

    def __repr__(self):
        return "<MXStatusPacket>"

    def __str__(self):
        fmt = """MX Status:
    PV:  {pv_voltage} {pv_current}
    Bat: {bat_voltage} {bat_current}
    Today: {kilowatt_hours} {amp_hours}
"""
        return fmt.format(**self.__dict__)


class MXLogPagePacket(object):
    fmt = Struct('>BBBBBBBBBBBBBB')

    def __init__(self):
        self.day = None
        self.amp_hours = None
        self.kilowatt_hours = None
        self.volts_peak = None
        self.amps_peak = None
        self.kilowatts_peak = None
        self.bat_min = None
        self.bat_max = None
        self.absorb_time = None
        self.float_time = None
        self.raw = None

    @classmethod
    def from_buffer(cls, data):
        values = cls.fmt.unpack(data)
        page = MXLogPagePacket()

        # Parse the mess of binary values
        page.bat_max = ((values[1] & 0xFC) >> 2) | ((values[2] & 0x0F) << 6)
        page.bat_min = ((values[9] & 0xC0) >> 6) | (values[10] << 2) | ((values[11] & 0x03) << 10)
        page.kilowatt_hours = ((values[2] & 0xF0) >> 4) | (values[3] << 4)
        page.amp_hours = values[8] | ((values[9] & 0x3F) << 8)
        page.volts_peak = values[4]
        page.amps_peak = values[0] | ((values[1] & 0x03) << 8)
        page.absorb_time = values[5] | ((values[6] & 0x0F) << 8)
        page.float_time = ((values[6] & 0xF0) >> 4) | (values[7] << 4)
        page.kilowatts_peak = ((values[12] & 0xFC) >> 2) | (values[11] << 6)
        page.day = values[13]

        # Convert to human-readable values
        page.bat_max = Value(page.bat_max / 10.0, units='V', resolution=1)
        page.bat_min = Value(page.bat_min / 10.0, units='V', resolution=1)
        page.volts_peak = Value(page.volts_peak, units='Vpk')
        page.amps_peak = Value(page.amps_peak / 10.0, units='Apk', resolution=1)
        page.kilowatts_peak = Value(page.kilowatts_peak / 1000.0, units='kWpk', resolution=3)
        page.amp_hours = Value(page.amp_hours, units='Ah')
        page.kilowatt_hours = Value(page.kilowatt_hours / 10.0, units='kWh', resolution=1)
        page.absorb_time = Value(page.absorb_time, units='min')
        page.float_time = Value(page.float_time, units='min')

        # Also add the raw packet
        page.raw = data

        return page

    def __str__(self):
        fmt = """MX Log Page:
    Day: -{day}
    {amp_hours} {kilowatt_hours}
    {volts_peak} {amps_peak} {kilowatts_peak}
    Min: {bat_min} Max: {bat_max}
    Absorb: {absorb_time} Float: {float_time}
"""
        return fmt.format(**self.__dict__)


class MateMXDevice(MateDevice):
    """
    Communicate with an MX unit attached to the MateNET bus
    """
    def scan(self, *args):
        """
        Query the attached device to make sure we're communicating with an MX unit
        """
        devid = super(MateMXDevice, self).scan()
        if devid == None:
            raise RuntimeError("No response from the MX unit")
        if devid != MateNET.DEVICE_MX:
            raise RuntimeError("Attached device is not an MX unit! (DeviceID: %s)" % devid)

    def get_status(self):
        """
        Request a status packet from the controller
        :return: A MXStatusPacket
        """
        resp = self.send(MateNET.TYPE_STATUS, addr=1, param=0x00)
        if resp:
            return MXStatusPacket.from_buffer(resp)

    def get_logpage(self, day):
        """
        Get a log page for the specified day
        :param day: The day, counting backwards from today (0:Today, -1..-255)
        :return: A MXLogPagePacket
        """
        resp = self.send(MateNET.TYPE_LOG, addr=0, param=-day)
        if resp:
            return MXLogPagePacket.from_buffer(resp)

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

# For backwards compatibility
# DEPRECATED
def MateMX(comport, supports_spacemark=None, port=0):
    bus = MateNET(comport, supports_spacemark)
    return MateMXDevice(bus, port)


if __name__ == "__main__":
    status = MXStatusPacket.from_buffer('\x85\x82\x85\x00\x69\x3f\x01\x00\x1d\x01\x0c\x02\x6a')
    print status

    #logpage = MXLogPagePacket.from_buffer('\x02\xFF\x17\x01\x16\x3C\x00\x01\x01\x40\x00\x10\x10\x01')
    logpage = MXLogPagePacket.from_buffer('\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x01')
    print logpage
