# pyMATE FX interface
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Provides access to an Outback FX inverter
#
# UNTESTED - implementation determined by poking values at a MATE controller

__author__ = 'Jared'

from pymate.value import Value
from struct import Struct
from . import MateDevice, MateNET


class FXStatusPacket(object):
    fmt = Struct('>BBBBBBBBBhBB')

    def __init__(self, misc=None):
        self.raw = None

        self.misc             = misc
        self.warnings         = None  # See MateFXDevice.WARN_ enum
        self.error_mode       = None  # See MateFXDevice.ERROR_ bitfield
        self.ac_mode          = None  # 0: No AC, 1: AC Drop, 2: AC Use
        self.operational_mode = None  # See MateFXDevice.STATUS_ enum

        self.is_230v = None
        self.aux_on  = None
        if misc is not None:
            self.is_230v = (misc & 0x01 == 0x01)
            self.aux_on  = (misc & 0x80 == 0x80)

        self.inverter_current = None  # Ouptut/Inverter AC Current the FX is delivering to loads
        self.output_voltage   = None  # Output/Inverter AC Voltage (to loads)
        self.input_voltage    = None  # Input/Line AC Voltage (from grid)
        self.sell_current     = None  # AC Current the FX is delivering from batteries to AC input (sell)
        self.chg_current      = None  # AC Current the FX is taking from AC input and delivering to batteries
        self.buy_current      = None  # AC Current the FX is taking from AC input and delivering to batteries + loads
        self.battery_voltage  = None  # Battery Voltage

    @property
    def inv_power(self):
        """
        BATTERIES -> AC_OUTPUT
        Power produced by the inverter from the battery
        """
        if self.inverter_current is not None and self.output_voltage is not None:
            return Value((float(self.inverter_current) * float(self.output_voltage)) / 1000.0, units='kW', resolution=2)
        return None

    @property
    def sell_power(self):
        """
        BATTERIES -> AC_INPUT
        Power produced by the inverter from the batteries, sold back to the grid (AC input)
        """
        if self.sell_current is not None and self.output_voltage is not None:
            return Value((float(self.sell_current) * float(self.output_voltage)) / 1000.0, units='kW', resolution=2)
        return None

    @property
    def chg_power(self):
        """
        AC_INPUT -> BATTERIES
        Power consumed by the inverter from the AC input to charge the battery bank
        """
        if self.chg_current is not None and self.input_voltage is not None:
            return Value((float(self.chg_current) * float(self.input_voltage)) / 1000.0, units='kW', resolution=2)
        return None

    @property
    def buy_power(self):
        """
        AC_INPUT -> BATTERIES + AC_OUTPUT
        """
        if self.buy_current is not None and self.input_voltage is not None:
            return Value((float(self.buy_current) * float(self.input_voltage)) / 1000.0, units='kW', resolution=2)
        return None

    @classmethod
    def from_buffer(cls, data):
        values = cls.fmt.unpack(data)

        # Need this to determine whether the system is 230v or 110v
        misc = values[10]

        status = FXStatusPacket(misc)

        # When misc:0 == 1, you must multiply voltages by 2, and divide currents by 2
        if status.is_230v:
            vmul = 2.0; imul = 0.5
        else:
            vmul = 1.0; imul = 1.0

        # From MATE2 doc the status packet contains:
        # Inverter address
        # Inverter current - AC current the FX is delivering to loads
        # Charger current - AC current the FX is taking from AC input and delivering to batteries
        # Buy current - AC current the FX is taking from AC input and delivering to batteries AND loads
        # AC input voltage
        # AC output voltage
        # Sell current - AC current the FX is delivering from batteries to AC input
        # FX operational mode (0..10)
        # FX error mode
        # FX AC mode
        # FX Bat Voltage
        # FX Misc
        # FX Warnings

        status.inverter_current  = Value(values[0] * imul, units='A', resolution=1)
        status.chg_current       = Value(values[1] * imul, units='A', resolution=1)
        status.buy_current       = Value(values[2] * imul, units='A', resolution=1)
        status.input_voltage     = Value(values[3] * vmul, units='V', resolution=1)
        status.output_voltage    = Value(values[4] * vmul, units='V', resolution=1)
        status.sell_current      = Value(values[5] * imul, units='A', resolution=1)
        status.operational_mode  = values[6]
        status.error_mode        = values[7]
        status.ac_mode           = values[8]
        status.battery_voltage   = Value(values[9] / 10.0, units='V', resolution=1)
        # values[10]: misc byte
        status.warnings          = values[11]

        # Also add the raw packet, in case any of the above changes
        status.raw = data

        return status

    def __repr__(self):
        return "<FXStatusPacket>"

    def __str__(self):
        # Format matches MATE2 LCD readout (FX->STATUS->METER)
        fmt = """FX Status:
    Battery: {battery_voltage}
    Inv: {inv} Zer: {sell}
    Chg: {chg} Buy: {buy}
"""
        return fmt.format(
            battery_voltage=self.battery_voltage,
            inv=self.inv_power,
            chg=self.chg_power,
            sell=self.sell_power,
            buy=self.buy_power
        )


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

    # Operational Mode enum
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

    # Reasons that the FX has stopped selling power to the grid
    # (see self.sell_status)
    SELL_STOP_REASONS = {
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
    }

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
        """ Temperature of the battery (Raw, 0..255) """
        # Not verified. I don't have a battery thermometer.
        return self.query(0x0032)

    @property
    def temp_air(self):
        """ Temperature of the air (Raw, 0..255) """
        return self.query(0x0033)

    @property
    def temp_fets(self):
        """ Temperature of the MOSFET switches (Raw, 0..255) """
        return self.query(0x0034)

    @property
    def temp_capacitor(self):
        """ Temperature of the capacitor (Raw, 0..255) """
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
    print(status)
