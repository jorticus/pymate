import datetime

class MateDevice(object):
    """
    Abstract class representing a device attached to the MateNET bus or to a hub.

    Usage:
    bus = MateNET('COM1')
    dev = MateDevice(bus, port=0)
    dev.scan()
    """
    DEVICE_TYPE = None

    DEVICE_HUB = 1
    DEVICE_FX = 2
    DEVICE_MX = 3
    DEVICE_DC = 4

    # Common registers
    REG_DEVID = 0x0000
    REG_REV_A = 0x0002
    REG_REV_B = 0x0003
    REG_REV_C = 0x0004

    REG_SET_BATTERY_TEMP = 0x4001
    REG_TIME  = 0x4004
    REG_DATE  = 0x4005

    def __init__(self, matenet, port=0):
        #assert(isinstance(matenet, [MateNET]))
        self.matenet = matenet
        self.port    = port

    # def __init__(self, comport, supports_spacemark=None):
    #     super(Mate, self).__init__(comport, supports_spacemark)

    def scan(self):
        return self.matenet.scan(self.port)

    def send(self, ptype, addr, param=0, response_len=None):
        return self.matenet.send(ptype, addr, param=param, port=self.port, response_len=None)

    def query(self, reg, param=0):
        return self.matenet.query(reg, param=param, port=self.port)

    def control(self, reg, value):
        return self.matenet.control(reg, value, port=self.port)

    def read(self, register, param=0):
        # Alias of control()
        return self.matenet.read(register, param, port=self.port)

    def write(self, register, value):
        # Alias of query()
        return self.matenet.write(register, value, port=self.port)

    @property
    def revision(self):
        """
        :return: The revision of the attached device (Format "000.000.000")
        """
        a = self.query(self.REG_REV_A)
        b = self.query(self.REG_REV_B)
        c = self.query(self.REG_REV_C)
        return '%.3d.%.3d.%.3d' % (a, b, c)

    def update_time(self, dt):
        """
        Update the time on the connected device
        This should be sent every 15 seconds.
        NOTE: not supported on FX devices.
        """
        assert(isinstance(dt, datetime.datetime))
        x1 = (
            ((dt.hour & 0x1F) << 11) | 
            ((dt.minute & 0x3F) << 5) | 
            ((dt.second & 0x1F) >> 1)
        )
        x2 = (
            (((dt.year-2000) & 0x7F) << 9) | 
            ((dt.month & 0x0F) << 5) | 
            (dt.day & 0x1F)
        )
        self.write(self.REG_TIME, x1)
        self.write(self.REG_DATE, x2)
        
    def update_battery_temp(self, raw_temp):
        """
        Update the battery temperature for FX/DC devices
        """
        self.write(self.REG_SET_BATTERY_TEMP, raw_temp)

    @staticmethod
    def synchronize(master, devices):
        """
        Synchronize connected outback devices.
        Should be called once per minute.

        :param master: The master MateMXDevice
        :param devices: All connected MateDevices (including master)
        """
        assert(all([isinstance(d, MateDevice) for d in devices]))
        assert(isinstance(master, MateDevice)) # Should be MateMXDevice
        assert(master.DEVICE_TYPE == MateDevice.DEVICE_MX)

        # 1. Update date & time for attached MX/DC units
        dt = datetime.datetime.now()
        for dev in devices:
            if (dev is not None):
                if (dev.DEVICE_TYPE in (MateDevice.DEVICE_MX, MateDevice.DEVICE_DC)):
                    dev.update_time(dt)

        # 2. Update battery temperature for attached FX/DC units
        bat_temp = master.battery_temp_raw
        for dev in devices:
            if (dev is not None) and (dev is not master):
                if (dev.DEVICE_TYPE in (MateDevice.DEVICE_FX, MateDevice.DEVICE_DC)):
                    dev.update_battery_temp(bat_temp)

        return bat_temp

# For backwards compatibility
# DEPRECATRED
# class Mate(MateDevice):
#     def __init__(self, comport, supports_spacemark=None):
#         self.bus = MateNET(comport, supports_spacemark)
#         super(Mate, self).__init__(self.bus, port=0)
