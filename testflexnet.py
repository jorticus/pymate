from matenet import MateFlexNetDC
from time import sleep

print "MATE emulator (FLEXnet DC)"

# Create a new MATE emulator attached to the specified serial port:
mate = MateFlexNetDC('COM9', supports_spacemark=False)

# Check that an FX unit is attached and is responding
mate.scan(0)

# Query the device revision
print "Revision:", mate.revision

print mate.get_status()

print mate.get_logpage(-2)
