from pymate.matenet import MateNET, MateMXDevice
from time import sleep

print "MATE emulator (MX)"


# Create a MateNET bus connection
bus = MateNET('/dev/ttyUSB0')

# Create a new MATE emulator attached to the specified port
mate = MateMXDevice(bus)

# Check that an MX unit is attached and is responding
mate.scan()

# Query the device revision
print "Revision:", mate.revision


print "Getting log page... (day:-1)"
logpage = mate.get_logpage(-1)
print logpage

while True:
    print "Status:"
    status = mate.get_status()
    print status

    sleep(1.0)

