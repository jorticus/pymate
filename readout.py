from pymate.matenet import MateNET, MateMXDevice
from time import sleep
from settings import SERIAL_PORT

print "MATE emulator (MX)"


# Create a MateNET bus connection
bus = MateNET(SERIAL_PORT)

# Find an MX device on the bus
port = bus.find_device(MateNET.DEVICE_MX)

# Create a new MATE emulator attached to the specified port
mate = MateMXDevice(bus, port)

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

