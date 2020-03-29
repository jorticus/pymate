# pyMATE FLEXnet-DC interface
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Provides access to an Outback FLEXnet DC power monitor
#
# NOTE: You will need a MATE to program the FLEXnet DC before use. 
# See the OutBack user guide for the product.
#

__author__ = 'Jared'

from pymate.value import Value
from pymate.cstruct import Struct
from . import MateDevice, MateNET

class DCStatusPacket(object):
    fmt = Struct('>'+
        'HHHHBHH'+      # Page A (7 values)
        'HBBHHHH'+      # Page B (7 values)
        'H'+            # Shared between page B/C
        'HHHHHH'+       # Page C (6 values)
        'HHBBBBBBBBB'+  # Page D (11 values)
        'BBBHHHHH'+     # Page E (8 values)
        'HBHHB5B'       # Page F (6 values)
    )

    def __init__(self):

        # User Guide mentions:
        # Volts for one battery bank (0-80V in 0.1V resolution)
        # Current range: 2000A (+/- 1000A DC), 0.1A resolution

        self.bat_voltage = None
        self.state_of_charge = None
        
        self.shunta_power = None
        self.shuntb_power = None
        self.shuntc_power = None
        self.shunta_current = None
        self.shuntb_current = None
        self.shuntc_current = None

        self.shunta_kwh_today = None
        self.shuntb_kwh_today = None
        self.shuntc_kwh_today = None
        self.shunta_ah_today = None
        self.shuntb_ah_today = None
        self.shuntc_ah_today = None

        self.bat_net_kwh = None
        self.bat_net_ah = None
        self.min_soc_today = None
        self.in_ah_today = None
        self.out_ah_today = None
        self.bat_ah_today = None
        self.in_kwh_today = None
        self.out_kwh_today = None
        self.bat_kwh_today = None

        self.in_power = None
        self.out_power = None
        self.bat_power = None
        
        self.in_current = None
        self.out_current = None
        self.bat_current = None

        self.days_since_full = None

        self.flags = None

        pass

    @classmethod
    def from_buffer(cls, data):
        values = cls.fmt.unpack(data)
        status = DCStatusPacket()

        # Page A
        status.shunta_current   = Value(values[0] / 10.0, units='A', resolution=1)
        status.shuntb_current   = Value(values[1] / 10.0, units='A', resolution=1)
        status.shuntc_current   = Value(values[2] / 10.0, units='A', resolution=1)
        status.bat_voltage      = Value(values[3] / 10.0, units='V', resolution=1)
        status.state_of_charge  = Value(values[4], units='%', resolution=0)
        status.shunta_power     = Value(values[5] / 100.0, units='kW', resolution=2)
        status.shuntb_power     = Value(values[6] / 100.0, units='kW', resolution=2)

        # Page B
        status.shuntc_power     = Value(values[7] / 100.0, units='kW', resolution=2)
        # unknown values[8]
        status.flags            = values[9]
        status.in_current       = Value(values[10] / 10.0, units='A', resolution=1)
        status.out_current      = Value(values[11] / 10.0, units='A', resolution=1)
        status.bat_current      = Value(values[12] / 10.0, units='A', resolution=1)
        status.in_power         = Value(values[13] / 100.0, units='kW', resolution=2)
        status.out_power        = Value(values[14] / 100.0, units='kW', resolution=2)  # NOTE: Split between Page B/C
        
        # Page C
        status.bat_power        = Value(values[15] / 100.0, units='kW', resolution=2)
        status.in_ah_today      = Value(values[16], units='Ah', resolution=0)
        status.out_ah_today     = Value(values[17], units='Ah', resolution=0)
        status.bat_ah_today     = Value(values[18], units='Ah', resolution=0)
        status.in_kwh_today     = Value(values[19] / 100.0, units='kWh', resolution=2)
        status.out_kwh_today    = Value(values[20] / 100.0, units='kWh', resolution=2)

        # Page D
        status.bat_kwh_today    = Value(values[21] / 100.0, units='kWh', resolution=2)
        status.days_since_full  = Value(values[22] / 10.0, units='days', resolution=1)
        # values[23..31] (9 values) unknown

        # Page E
        # values[32..34] (3 values) unknown
        status.shunta_kwh_today = Value(values[35] / 100.0, units='kWh', resolution=2)
        status.shuntb_kwh_today = Value(values[36] / 100.0, units='kWh', resolution=2)
        status.shuntc_kwh_today = Value(values[37] / 100.0, units='kWh', resolution=2)
        status.shunta_ah_today  = Value(values[38], units='Ah', resolution=0)
        status.shuntb_ah_today  = Value(values[39], units='Ah', resolution=0)

        # Page F
        status.shuntc_ah_today  = Value(values[40], units='Ah', resolution=0)
        status.min_soc_today    = Value(values[41], units='%', resolution=0)
        status.bat_net_ah       = Value(values[42], units='Ah', resolution=0)
        status.bat_net_kwh      = Value(values[43] / 100.0, units='kWh', resolution=2)

        return status

    def __repr__(self):
        return "<DCStatusPacket>"

    def __str__(self):
        fmt = """DC Status: 
        
"""
        return fmt.format(**self.__dict__)

class MateDCDevice(MateDevice):
    """
    Communicate with a FLEXnet DC unit attached to the MateNET bus
    """
    def scan(self):
        """
        Query the attached device to make sure we're communicating with an FLEXnet DC unit
        """
        devid = super(MateFlexNetDC, self).scan()
        if devid == None:
            raise RuntimeError("No response from the FLEXnet DC unit")
        if devid != MateNET.DEVICE_FLEXNETDC:
            raise RuntimeError("Attached device is not a FLEXnet DC unit! (DeviceID: %s)" % devid)

    def get_status(self):
        """
        Request a status packet from the FLEXnet DC
        :return: A DCStatusPacket
        """

        data = self.get_status_raw()
        # TODO:
        #return DCStatusPacket.from_buffer(data)
        return None

    def get_status_raw():
        data = ''
        for i in range(0x0A,0x0F):
            resp = self.send(MateNET.TYPE_STATUS, addr=i)
            if not resp:
                return None
            data += str(resp)

        if len(data) != 13*5:
            raise Exception('Size of status packets invalid')

        return None

    def get_logpage(self, day):
        """
        Get a log page for the specified day
        :param day: The day, counting backwards from today (0:Today, -1..-255)
        :return: A DCLogPagePacket
        """
        # TODO: This doesn't return anything. It must have a different command.
        # The UserGuide does mention having access to log pages
        #resp = self.send(MateNET.TYPE_LOG, addr=0, param=-day)
        #if resp:
        #    print 'RAW:', (' '.join("{:02x}".format(ord(c)) for c in resp[1:]))
        #    #return DCLogPagePacket.from_buffer(resp)
