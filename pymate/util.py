__author__ = 'Jared'

def hexstr2bin(s):
    return ''.join([chr(int(x, 16)) for x in s.split()])

def bin2hexstr(s):
    return ' '.join('%.2x' % ord(x) for x in s)
