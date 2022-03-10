#!/usr/bin/python
#
# Scans the Mate bus for any attached devices,
# and displays the result.
#

from pymate.matenet import MateNET, MateNETPJON, MateDevice
import settings
import serial
import logging
import time

#log = logging.getLogger('mate')
#log.setLevel(logging.DEBUG)
#log.addHandler(logging.StreamHandler())

print("MATE Bus Scan")

# Create a MateNET bus connection

if settings.SERIAL_PROTO == 'PJON':
    port = MateNETPJON(settings.SERIAL_PORT)
    bus = MateNET(port)

    # PJON is more reliable, so we don't need to retry packets
    bus.RETRY_PACKET = 0

    # Time for the Arduino to boot (connecting serial may reset it)
    time.sleep(1.0)

else:
    bus = MateNET(settings.SERIAL_PORT)


def print_device(d):
    dtype = d.scan()

    # No response from the scan command.
    # there is nothing at this port.
    if dtype is None:
        print(f'Port{d.port}: -')
    else:
        try:
            rev = d.revision
        except Exception as e:
            rev = str(e)

        if dtype not in MateNET.DEVICE_TYPES:
            print(f"Port{d.port}: Unknown device type: {dtype}")
        else:
            print(f"Port{d.port}: {MateNET.DEVICE_TYPES[dtype]} (Rev: {rev})")
    return dtype

# The root device
d0 = MateDevice(bus, port=0)
dtype = d0.scan()
if not dtype:
    print('No device connected!')
    exit()
print_device(d0)

# Child devices attached to a hub
# (Only valid if the root device is a hub)
if dtype == MateNET.DEVICE_HUB:
    for i in range(1,10):
        subdev = MateDevice(bus, port=i)
        print_device(subdev)

print()
print('Finished!')