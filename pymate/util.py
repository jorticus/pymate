__author__ = 'Jared'

import sys
import collections

is_py3 = (sys.version_info >= (3,0)) 

def to_byte(c):
    if is_py3: return int(c & 0xFF)
    else:      return ord(c) & 0xFF

def to_bchr(b):
    if is_py3: return b & 0xFF
    else:      return chr(b & 0xFF)

def to_bytestr(x):
    if x is None:       return None
    if isinstance(x, bytes):
        return x
    if isinstance(x, collections.Iterable):
        if is_py3: return bytes(x)
        else:      return b''.join(to_bchr(b) for b in x)
    return bytes([to_byte(x)]) # Scalar

def hexstr2bin(s):
    return b''.join([to_bchr(int(x, 16)) for x in s.split()])

def bin2hexstr(s):
    return ' '.join('%.2x' % to_byte(x) for x in s)
