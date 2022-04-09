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
        self._fmt = f"%.{self.resolution:d}f" % self.value
        if self.units:
            self._fmt += str(self.units)

    def __str__(self):
        return self._fmt

    def __repr__(self):
        return self.__str__()

    def __float__(self):
        return float(self.value)

    def __int__(self):
        return int(self.value)
