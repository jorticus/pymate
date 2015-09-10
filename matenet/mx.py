# pyMATE MX interface
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Provides access to an Outback MX solar charge controller
#

__author__ = 'Jared'

from cstruct import struct
from value import Value
from matenet import MateNET

# Raw mate status packet
_MXStatusStruct = struct('>B4sBBBHHH', (
    'sop',              # Start-of-packet? has the 9th bit set to denote the start of the packet
    'q',                # TODO: Unsure what this contains
    'amp_hours',        # Daily accumulated amp-hours (0-255 AH)
    'kilowatt_peak',    # Daily kilowatts-peak (hundredths: 0.00-2.55 kW)
    'status',           # Status (Same as the MATE serial protocol)
    'kilowatt_hours',   # Kilowatt-hours (tenths: 0.0-6553.5 kWh)
    'v_bat',            # Battery/Out voltage (tenths: 0.0-6553.5 V)
    'v_pv'              # PV/In voltage (tenths: 0.0-6553.5 V)
))

class MXStatusPacket(_MXStatusStruct):
    STATUS_SLEEPING = 0
    STATUS_FLOATING = 1
    STATUS_BULK = 2
    STATUS_ABSORB = 3
    STATUS_EQUALIZE = 4

    @classmethod
    def from_buffer(cls, data):
        raw = super(MXStatusPacket, cls).from_buffer(data)
        # Wrap members in Value objects to make it more human-readable
        raw.amp_hours       = Value(raw.amp_hours,             units='Ah', resolution=0)
        raw.kilowatt_peak   = Value(raw.kilowatt_peak / 100.0, units='kW', resolution=2)
        raw.kilowatt_hours  = Value(raw.kilowatt_hours / 10.0, units='kW', resolution=1)
        raw.v_bat           = Value(raw.v_bat / 10.0,          units='V',  resolution=1)
        raw.v_pv            = Value(raw.v_pv / 10.0,           units='V',  resolution=1)
        # TODO: What does the 'q' member contain?
        return raw

class MateMX(MateNET):
    """
    Communicate with an MX unit attached to the MateNET bus
    """
    def get_status(self):
        """
        Request a status packet from the controller
        :return: A MateStatusPacket
        """
        self._send('\x00\x04\x00\x01\x00\x00\x00')
        data = self._recv()
        return MXStatusPacket.from_buffer(data)
