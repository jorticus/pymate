# pyMATE FX interface
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Provides access to an Outback FX inverter
#
# UNTESTED - implementation determined by poking values at a MATE controller

__author__ = 'Jared'

from value import Value
from struct import Struct
from matenet import Mate


class FXStatusPacket(object):
    fmt = Struct('>BBBBBBBBhBB')

    STATUS_INV_OFF = 0
    STATUS_SEARCH = 1
    STATUS_INV_ON = 2
    STATUS_CHARGE = 3
    STATUS_SILENT = 4
    STATUS_FLOAT = 5
    STATUS_EQ = 6
    STATUS_CHARGER_OFF = 7
    STATUS_SUPPORT = 8          # FX is drawing power from batteries to support AC
    STATUS_SELL_ENABLED = 9     # FX is exporting more power than the loads are drawing
    STATUS_PASS_THRU = 10       # FX converter is off, passing through line AC

    def __init__(self, a=None, b=None, c=None, l=None, i=None, z=None,
                 status=None, misc=None, error=None, bat_voltage=None):
        # TODO: Determine what these variables represent
        self.a = a
        self.l = l  # Line voltage?
        self.i = i  # Inverter voltage?
        self.c = c  # Inverter current?
        self.b = b  # Line current?
        self.z = z
        self.status = status
        self.misc = misc
        self.error = error
        self.bat_voltage = bat_voltage

        # Misc byte
        self.is_230v = misc & 0x01 == 0x01
        self.aux_on = misc & 0x80 == 0x80

        # TODO: When misc:0 == 1, you must multiply voltages by 2, and divide currents by 2

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
            status=values[2],
            misc=values[3],
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
        fmt = """FX Status:
    Battery: {bat_voltage}
    Inv: {inv_power} Zer: {zer_power}
    Chg: {chg_power} Buy: {buy_power}
"""
        return fmt.format(**self.__dict__)


class MateFX(Mate):
    """
    Communicate with an FX unit attached to the MateNET bus
    """
    # Error bit-field
    ERROR_LOW_VAC_OUTPUT = 0x01
    ERROR_STACKING_ERROR = 0x02
    ERROR_OVER_TEMP = 0x04
    ERROR_LOW_BATTERY = 0x08
    ERROR_PHASE_LOSS = 0x10
    ERROR_HIGH_BATTERY = 0x20
    ERROR_SHORTED_OUTPUT = 0x40
    ERROR_BACK_FEED = 0x80

    # Warning bit-field
    WARN_ACIN_FREQ_HIGH = 0x01
    WARN_ACIN_FREQ_LOW = 0x02
    WARN_ACIN_V_HIGH = 0x04
    WARN_ACIN_V_LOW = 0x08
    WARN_BUY_AMPS_EXCEEDS_INPUT = 0x10
    WARN_TEMP_SENSOR_FAILED = 0x20
    WARN_COMM_ERROR = 0x40
    WARN_FAN_FAILURE = 0x80

    def __init__(self, comport, supports_spacemark=None):
        super(MateFX, self).__init__(comport, supports_spacemark)
        self.is_230v = False

    def scan(self, port=0):
        """
        Query the attached device to make sure we're communicating with an FX unit
        TODO: Support Hubs
        :param port: int, 0-10 (root:0)
        """
        devid = super(MateFX, self).scan(port)
        if devid == None:
            raise RuntimeError("No response from the FX unit")
        if devid != Mate.DEVICE_FX:
            raise RuntimeError("Attached device is not an FX unit! (DeviceID: %s)" % devid)

    def get_status(self):
        """
        Request a status packet from the inverter
        :return: A FXStatusPacket
        """
        resp = self.send(Mate.TYPE_STATUS, addr=1)
        if resp:
            status = FXStatusPacket.from_buffer(resp[1:])
            self.is_230v = status.is_230v
            return status

    @property
    def errors(self):
        """ Errors bit-field (See ERROR_* constants) """
        return self.query(0x0039)

    @property
    def warnings(self):
        """ Warnings bit-field (See WARN_* constants) """
        return self.query(0x0059)

    @property
    def inverter_control(self):
        """ Inverter mode (0: Off, 1: Search, 2: On) """
        return self.query(0x003D)
    @inverter_control.setter
    def inverter_control(self, value):
        self.control(0x003D, value)

    @property
    def acin_control(self):
        """ AC IN mode (0: Drop, 1: Use) """
        return self.query(0x003A)
    @acin_control.setter
    def acin_control(self, value):
        self.control(0x003A, value)

    @property
    def charge_control(self):
        """ Charger mode (0: Off, 1: Auto, 2: On) """
        return self.query(0x003C)
    @charge_control.setter
    def charge_control(self, value):
        self.control(0x003C, value)

    @property
    def aux_control(self):
        """ AUX mode (0: Off, 1: Auto, 2: On) """
        return self.query(0x005A)
    @aux_control.setter
    def aux_control(self, value):
        self.control(0x005A, value)

    @property
    def eq_control(self):
        """ Equalize mode (0:Off, ???) """
        return self.query(0x0038)
    @eq_control.setter
    def eq_control(self, value):
        self.control(0x0038, value)

    @property
    def disconn_status(self):
        return self.query(0x0084)

    @property
    def sell_status(self):
        return self.query(0x008F)

    @property
    def temp_battery(self):
        """ Temperature of the battery (RAW, 0..255) """
        return self.query(0x0032)

    @property
    def temp_air(self):
        """ Temperature of the air (RAW, 0..255) """
        return self.query(0x0033)

    @property
    def temp_fets(self):
        """ Temperature of the MOSFET switches (RAW, 0..255) """
        return self.query(0x0034)

    @property
    def temp_capacitor(self):
        """ Temperature of the capacitor (RAW, 0..255) """
        return self.query(0x0035)

    @property
    def output_voltage(self):
        x = self.query(0x002D)
        if self.is_230v:
            x *= 2.0
        return Value(x, units='V', resolution=0)

    @property
    def input_voltage(self):
        x = self.query(0x002C)
        if self.is_230v:
            x *= 2.0
        return Value(x, units='V', resolution=0)

    @property
    def inverter_current(self):
        x = self.query(0x006D)
        if self.is_230v:
            x /= 2.0
        return Value(x, units='A', resolution=0)

    @property
    def charger_current(self):
        x = self.query(0x006A)
        if self.is_230v:
            x /= 2.0
        return Value(x, units='A', resolution=0)

    @property
    def input_current(self):
        x = self.query(0x006C)
        if self.is_230v:
            x /= 2.0
        return Value(x, units='A', resolution=0)

    @property
    def sell_current(self):
        x = self.query(0x006B)
        if self.is_230v:
            x /= 2.0
        return Value(x, units='A', resolution=0)

    @property
    def battery_actual(self):
        return Value(self.query(0x0019), units='V', resolution=0)

    @property
    def battery_temp_compensated(self):
        return Value(self.query(0x0016), units='V', resolution=0)

    @property
    def absorb_setpoint(self):
        return Value(self.query(0x000B), units='V', resolution=0)

    @property
    def absorb_time_remaining(self):
        return Value(self.query(0x0070), units='h', resolution=0)

    @property
    def float_setpoint(self):
        return Value(self.query(0x000A), units='V', resolution=0)

    @property
    def float_time_remaining(self):
        return Value(self.query(0x006E), units='h', resolution=0)

    @property
    def refloat_setpoint(self):
        return Value(self.query(0x000D), units='V', resolution=0)

    @property
    def equalize_setpoint(self):
        return Value(self.query(0x000C), units='V', resolution=0)

    @property
    def equalize_time_remaining(self):
        return Value(self.query(0x0071), units='h', resolution=0)


if __name__ == "__main__":
    status = FXStatusPacket.from_buffer('\x28\x0A\x00\x00\x0A\x00\x64\x00\x00\xDC\x14\x0A')
    print(status)
