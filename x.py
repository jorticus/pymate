from settings import *
from pymate.matenet import *

b = MateNET(SERIAL_PORT)

mx = MateMXDevice(b,b.find_device(MateNET.DEVICE_MX))
fx = MateFXDevice(b,b.find_device(MateNET.DEVICE_FX))
