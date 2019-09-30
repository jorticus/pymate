
class MateDevice(object):
    """
    Abstract class representing a device attached to the MateNET bus or to a hub.

    Usage:
    bus = MateNET('COM1')
    dev = MateDevice(bus, port=0)
    dev.scan()
    """

    def __init__(self, matenet, port=0):
        #assert(isinstance(matenet, [MateNET]))
        self.matenet = matenet
        self.port    = port

    # def __init__(self, comport, supports_spacemark=None):
    #     super(Mate, self).__init__(comport, supports_spacemark)

    def scan(self):
        return self.matenet.scan(self.port)

    def send(self, ptype, addr, param=0):
        return self.matenet.send(ptype, addr, param=param, port=self.port)

    def query(self, reg, param=0):
        return self.matenet.query(reg, param=param, port=self.port)

    def control(self, reg, value):
        return self.matenet.control(reg, value, port=self.port)

    @property
    def revision(self):
        """
        :return: The revision of the attached device (Format "000.000.000")
        """
        a = self.query(0x0002)
        b = self.query(0x0003)
        c = self.query(0x0004)
        return '%.3d.%.3d.%.3d' % (a, b, c)

# For backwards compatibility
# DEPRECATRED
class Mate(MateDevice):
    def __init__(self, comport, supports_spacemark=None):
        self.bus = MateNET(comport, supports_spacemark)
        super(Mate, self).__init__(self.bus, port=0)
