__author__ = 'Jared'

class Value(object):
    """
    Formatted value with units
    Provides a way to represent a number with units such as Volts and Watts.
    """
    def __init__(self, value, units=None, resolution=0):
        self.value = float(value)
        self.units = units
        self.resolution = resolution
        self.fmt = "%%.%df" % resolution
        if self.units:
            self.fmt += str(self.units)

    def __str__(self):
        return self.fmt % self.value

    def __repr__(self):
        return self.__str__()

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)
