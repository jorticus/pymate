# pyMATE tester
# Author: Jared Sanson <jared@jared.geek.nz>
#
# NOTE:
# This assumes the PC is connected to a MATE, instead of pretending to be a MATE.
# Thus RX/TX must be swapped.
#
# This pretends to be an MX device so we can test the MATE unit without
# needing it to be connected to the unit.
#
__author__ = 'Jared'

from matenet import MateNET

class MateTester(MateNET):
    """
    Used to test a MATE controller
    (PC connected to MATE)
    EXPERIMENTAL
    """
    def wait_for_packet(self, timeout=1.0):
        packet = self._recv(timeout=1.0)
        if not packet:
            return None

        return packet


from util import bin2hexstr, hexstr2bin


if __name__ == "__main__":
    tester = MateTester('COM8')

    print "Reading packets:"
    while True:
        packet = tester.wait_for_packet(timeout=5.0)
        if packet:
            print "Received:", bin2hexstr(packet)



