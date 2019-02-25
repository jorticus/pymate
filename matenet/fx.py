# pyMATE FX interface
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Provides access to an Outback FX inverter
#
# UNTESTED - implementation determined by poking values at a MATE controller

__author__ = 'Jared'

from value import Value
from struct import Struct
from matenet import MateDevice, MateNET


class FXStatusPacket(object):
    fmt = Struct('>BBBBBBBBBhBB')

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
        self.l = l  # Line voltage? Input AC voltage?
        self.i = i  # Inverter voltage?
        self.c = c  # Inverter current?
        self.b = b  # Line current?
        self.z = z  # Zer voltage? Output AC voltage?
        self.status = status
        self.misc = misc
        self.error = error
        self.bat_voltage = bat_voltage

        # Inverter Current (amps), AC current the FX is delivering to loads
        # Charger current (amps), AC current the FX is taking from AC input and delivering to batteries
        # Buy current (amps), AC current the FX is taking from the AC input and delivering to batteries AND pass-thru loads.
        # AC input voltage (V, 0-255). Voltage seen at FX's AC input. May need x2 multiplier
        # AC output voltage
        # Sell current (amps). The Ac current the FX is delivering from batteries to the AC input.

        # Misc byte
        self.is_230v = misc & 0x01 == 0x01
        self.aux_on = misc & 0x80 == 0x80

        # TODO: When misc:0 == 1, you must multiply voltages by 2, and divide currents by 2
        if self.is_230v:
            # self.z *= 2.0
            # self.l *= 2.0
            # self.i *= 2.0
            # self.c /= 2.0
            # self.b /= 2.0
            pass

        # Calculations
        self.chg_power = Value((self.a * self.l) / 1000.0, units='kW', resolution=2)
        self.buy_power = Value((self.b * self.l) / 1000.0, units='kW', resolution=2)
        self.inv_power = Value((self.c * self.i) / 1000.0, units='kW', resolution=2)
        self.zer_power = Value((self.z * self.i) / 1000.0, units='kW', resolution=2)

        # chg_power: Power into batteries, from AC Input
        # buy_power: Power into batteries + loads, from AC Input
        # inv_power: Power to loads
        # zer_power: ??

    @classmethod
    def from_buffer(cls, data):
        values = cls.fmt.unpack(data)

        # [0, 0, 0, 3, 115, 0, 4, 0, 2, (0, 244), 9, 0]
        # [0, 0, 0, 3, 115, 0, 4, 0, 2, (0, 246), 9, 0]
        # [0, 0, 0, 3, 114, 0, 4, 0, 2, (0, 242), 9, 0]
        status = FXStatusPacket(
            a=values[0],
            l=values[1],
            status=values[2],
            misc=values[3], # 3
            z=values[4],  # 115, Output Voltage?
            #values[5] # Unknown?
            i=values[6], # 4
            error=bool(values[7] != 0), # 0
            #values[8], # 2, Unknown?
            bat_voltage=Value(values[9] / 10.0, units='V', resolution=1),
            c=values[10], # 9
            b=values[11] # 0
        )

        # Also add the raw packet, in case any of the above changes
        status.raw = data

        return status

    def __repr__(self):
        return "<FXStatusPacket>"

    def __str__(self):
        fmt = """FX Status:
    Battery: {bat_voltage}
    Inv: {inv_power} Zer: {zer_power}
    Chg: {chg_power} Buy: {buy_power}
"""
        return fmt.format(**self.__dict__)


class MateFXDevice(MateDevice):
    """
    Communicate with an FX unit attached to the MateNET bus
    """
    # Error bit-field
    ERROR_LOW_VAC_OUTPUT = 0x01 # Inverter could not supply enough AC voltage to meet demand
    ERROR_STACKING_ERROR = 0x02 # Communication error among stacked FX inverters (eg. 3 phase system)
    ERROR_OVER_TEMP      = 0x04 # FX has reached maximum allowable temperature
    ERROR_LOW_BATTERY    = 0x08 # Battery voltage below low battery cut-out setpoint
    ERROR_PHASE_LOSS     = 0x10
    ERROR_HIGH_BATTERY   = 0x20 # Battery voltage rose above safe level for 10 seconds
    ERROR_SHORTED_OUTPUT = 0x40 
    ERROR_BACK_FEED      = 0x80 # Another power source was connected to the FX's AC output

    # Warning bit-field
    WARN_ACIN_FREQ_HIGH         = 0x01 # >66Hz or >56Hz
    WARN_ACIN_FREQ_LOW          = 0x02 # <54Hz or <44Hz
    WARN_ACIN_V_HIGH            = 0x04 # >140VAC or >270VAC
    WARN_ACIN_V_LOW             = 0x08 # <108VAC or <207VAC
    WARN_BUY_AMPS_EXCEEDS_INPUT = 0x10
    WARN_TEMP_SENSOR_FAILED     = 0x20 # Internal temperature sensors have failed
    WARN_COMM_ERROR             = 0x40 # Communication problem between us and the FX
    WARN_FAN_FAILURE            = 0x80 # Internal cooling fan has failed

    # Reasons that the FX has stopped selling power to the grid
    # (see self.sell_status)
    SELL_STOP_REASONS = [
        1: 'Frequency shift greater than limits',
        2: 'Island-detected wobble',
        3: 'VAC over voltage',
        4: 'Phase lock error',
        5: 'Charge diode battery volt fault',
        7: 'Silent command',
        8: 'Save command',
        9: 'R60 off at go fast',
        10: 'R60 off at silent relay',
        11: 'Current limit sell',
        12: 'Current limit charge',
        14: 'Back feed',
        15: 'Brute sell charge VAC over'
    ]

    def __init__(self, *args, **kwargs):
        super(MateFXDevice, self).__init__(*args, **kwargs)
        self._is_230v = None

    def scan(self, *args):
        """
        Query the attached device to make sure we're communicating with an FX unit
        """
        devid = super(MateFXDevice, self).scan()
        if devid == None:
            raise RuntimeError("No response from the FX unit")
        if devid != MateNET.DEVICE_FX:
            raise RuntimeError("Attached device is not an FX unit! (DeviceID: %s)" % devid)

    def get_status(self):
        """
        Request a status packet from the inverter
        :return: A FXStatusPacket
        """
        resp = self.send(MateNET.TYPE_STATUS, addr=1)
        if resp:
            status = FXStatusPacket.from_buffer(resp)
            self._is_230v = status.is_230v
            return status

    @property
    def is_230v(self):
        if self._is_230v is not None:
            return self._is_230v
        else:
            s = self.get_status()
            if not s:
                raise Exception('No response received when trying to read status')
            return self._is_230v

    @property
    def revision(self):
        # The FX doesn't return a revision;
        # instead it returns a firmware version number
        fw = self.query(0x0001)
        return 'FW:%.3d' % (fw)

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
        ## WARNING: THIS CAN TURN OFF THE INVERTER! ##
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
        """ Equalize mode (0:Off, 1: Auto?, 2: On?) """
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
        """ Temperature of the battery (DegC, 0..25.5?) """
        # Not verified. I don't have a battery thermometer.
        return Value(self.query(0x0032) / 10.0, units='C', resolution=1)

    @property
    def temp_air(self):
        """ Temperature of the air (DegC, 0..25.5) """
        return Value(self.query(0x0033) / 10.0, units='C', resolution=1)

    @property
    def temp_fets(self):
        """ Temperature of the MOSFET switches (DegC, 0..255) """
        return Value(self.query(0x0034) / 10.0, units='C', resolution=1)

    @property
    def temp_capacitor(self):
        """ Temperature of the capacitor (DegC, 0..25.5) """
        return Value(self.query(0x0035) / 10.0, units='C', resolution=1)

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
        return Value(self.query(0x0019) / 10.0, units='V', resolution=1)

    @property
    def battery_temp_compensated(self):
        return Value(self.query(0x0016) / 10.0, units='V', resolution=1)

    @property
    def absorb_setpoint(self):
        return Value(self.query(0x000B) / 10.0, units='V', resolution=1)

    @property
    def absorb_time_remaining(self):
        return Value(self.query(0x0070), units='h', resolution=0)

    @property
    def float_setpoint(self):
        return Value(self.query(0x000A) / 10.0, units='V', resolution=1)

    @property
    def float_time_remaining(self):
        return Value(self.query(0x006E), units='h', resolution=0)

    @property
    def refloat_setpoint(self):
        return Value(self.query(0x000D) / 10.0, units='V', resolution=1)

    @property
    def equalize_setpoint(self):
        return Value(self.query(0x000C) / 10.0, units='V', resolution=1)

    @property
    def equalize_time_remaining(self):
        return Value(self.query(0x0071), units='h', resolution=0)

# For backwards compatibility
# DEPRECATED
def MateFX(comport, supports_spacemark=None, port=0):
    bus = MateNET(comport, supports_spacemark)
    return MateFXDevice(bus, port)


if __name__ == "__main__":
    status = FXStatusPacket.from_buffer('\x28\x0A\x00\x00\x0A\x00\x64\x00\x00\xDC\x14\x0A')
    print status
