# pyMATE FLEXnet-DC interface
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Provides access to an Outback FLEXnet DC power monitor
#
# NOTE: You will need a MATE to program the FLEXnet DC before use. 
# See the OutBack user guide for the product.
#

__author__ = 'Jared'

from value import Value
from struct import Struct
from matenet import Mate

class DCStatusPacket(object):
    fmt = Struct('>28B')

    def __init__(self):
        # TODO: Fields??

        # User Guide mentions:
        # Volts for one battery bank (0-80V in 0.1V resolution)
        # For each channel (A,B,C):
        #   Amps
        #   kW
        #   kWh removed from batteries
        #   kWh returned to batteries
        #   Ah removed from batteries
        #   Ah returned to batteries
        # Battery bank state-of-charge
        # Lifetime kAh removed from batteries*
        # Days since charge parameters last met
        # Lowest SoC reached
        # For each channel (A,B,C):
        #   Min bat voltage*
        #   Max bat voltage*
        #   Max current charged*
        #   Max current discharged*
        #   Max kWh charged*
        #   Max kWh discharged*
        # 
        # Current range: 2000A (+/- 1000A DC), 0.1A resolution
        #
        # * Can be reset by user
        pass

    @classmethod
    def from_buffer(cls, data):
        values = cls.fmt.unpack(data)

        return DCStatusPacket() # TODO

    def __repr__(self):
        return "<DCStatusPacket>"

    def __str__(self):
        fmt = """DC Status: 
        
"""
        return fmt.format(**self.__dict__)

class MateDCDevice(Mate):
    """
    Communicate with a FLEXnet DC unit attached to the MateNET bus
    """
    def scan(self):
        """
        Query the attached device to make sure we're communicating with an FLEXnet DC unit
        """
        devid = super(MateFlexNetDC, self).scan(port)
        if devid == None:
            raise RuntimeError("No response from the FLEXnet DC unit")
        if devid != Mate.DEVICE_FLEXNETDC:
            raise RuntimeError("Attached device is not a FLEXnet DC unit! (DeviceID: %s)" % devid)

    def get_status(self):
        """
        Request a status packet from the FLEXnet DC
        :return: A DCStatusPacket
        """
        resp1 = self.send(Mate.TYPE_STATUS, addr=1)
        resp2 = self.send(Mate.TYPE_STATUS, addr=2) # TODO: This also returns data!
        if resp1 and resp2:
            print 'RAW[1]:', (' '.join("{:02x}".format(ord(c)) for c in resp1[1:]))
            print 'RAW[2]:', (' '.join("{:02x}".format(ord(c)) for c in resp2[1:]))
            return DCStatusPacket.from_buffer(resp1[1:])

    def get_logpage(self, day):
        """
        Get a log page for the specified day
        :param day: The day, counting backwards from today (0:Today, -1..-255)
        :return: A DCLogPagePacket
        """
        # TODO: This doesn't return anything. It must have a different command.
        # The UserGuide does mention having access to log pages
        #resp = self.send(Mate.TYPE_LOG, addr=0, param=-day)
        #if resp:
        #    print 'RAW:', (' '.join("{:02x}".format(ord(c)) for c in resp[1:]))
        #    #return DCLogPagePacket.from_buffer(resp)


# Status packets
# 03 00 00 00 00 00 00 64 00 00 00 00 00 00 01 21 00 03 00 00 00 03 00 00 00 00 00 00
# 01 00 00 00 00 00 00 64 00 00 00 00 00 00 01 21 00 01 00 00 00 01 00 00 00 00 00 00
# 02 00 00 00 00 00 00 64 00 00 00 00 00 00 01 21 00 02 00 00 00 02 00 00 00 00 00 00
# 06 00 00 00 00 00 00 64 00 00 00 00 00 00 01 21 00 06 00 00 00 06 00 00 00 00 00 00

# With 24V applied to BAT -/+ terminals: 
# f5 00 00 00 00 00 40 64 00 51 00 00 00 00 01 21 04 f5 00 00 04 f5 00 51 00 00 00 51 (but current limited to ~6V)
# 03 00 00 00 00 00 f4 64 00 01 00 00 00 00 01 21 00 03 00 00 00 03 00 01 00 00 00 01 (actually 24V applied)

# 03 00 00 00 00
# 00 f4  : 244 = 24.4V : Current battery voltage /10
# 64     : 100         : SoC?
# 00 01 
# 00 00 
# 00 00 
# 01 21  : 289 = 28.9V
# 00 03 
# 00 00 
# 00 03 
# 00 01 
# 00 00 
# 00 01
