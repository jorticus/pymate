from matenet import MateFX
from time import sleep

print "MATE emulator (FX)"

# Create a new MATE emulator attached to the specified serial port:
mate = MateFX('COM9', supports_spacemark=False)

# Check that an FX unit is attached and is responding
mate.scan(0)

# Query the device revision
print "Revision:", mate.revision
