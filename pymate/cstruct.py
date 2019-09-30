__author__ = 'Jared'

from struct import calcsize, unpack_from, Struct


def struct(fmt, fields):
    """
    Construct a new struct class which matches the provided format and fields.
    The fields must be defined in the same order as the struct format elements.
    fmt: a python struct format (str)
    fields: a tuple of names to match to each member in the struct (tuple of str)
    """
    fmt = Struct(fmt)
    test = fmt.unpack_from(b''.join(b'\0' for i in range(fmt.size)))
    nfields = len(test)

    if len(fields) != nfields:
        raise RuntimeError("Number of fields provided does not match the struct format (Format: %d, Fields: %d)" % (nfields, len(fields)))

    class _struct(object):
        """
        C-style struct class
        """
        _fmt = fmt
        _fields = fields
        _size = fmt.size
        _nfields = nfields

        def __init__(self, *args, **kwargs):
            """
            Initialize the struct's fields from the provided args.
            Named arguments take presedence over un-named args.
            """
            assert(len(args) <= self._nfields)

            # Default values
            for name in self._fields:
                setattr(self, name, None)

            # Un-named args
            for name, value in zip(self._fields, args):
                if not hasattr(self, name):
                    raise RuntimeError("Struct does not have a field named '%s'" % name)
                setattr(self, name, value)

            # Named args
            for name, value in kwargs.iteritems():
                if not hasattr(self, name):
                    raise RuntimeError("Struct does not have a field named '%s'" % name)
                setattr(self, name, value)

        @classmethod
        def from_buffer(cls, data):
            """
            Unpack a buffer of data into a struct object
            """

            if data is None:
                raise RuntimeError("Error parsing struct - no data provided")

            # Length validation
            data_len = len(data)
            if data_len != cls._size:
                raise RuntimeError("Error parsing struct - invalid length (Got %d bytes, expected %d)" % (data_len, cls._size))

            # Convert to binary string if necessary
            if not isinstance(data, (str, unicode)):
                data = ''.join(chr(c) for c in data)

            # Construct new struct class
            values = cls._fmt.unpack(data)
            return cls(*values)

        def to_buffer(self):
            """
            Convert the struct into a packed data format
            """
            values = [getattr(self, name) for name in self._fields]
            return self._fmt.pack(*values)

        def __repr__(self):
            return "struct:%s" % self.__dict__

    return _struct
