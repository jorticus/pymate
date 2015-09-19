from matenet import MateMX
from time import sleep

print "MATE emulator (MX)"

# Create a new MATE emulator attached to the specified serial port:
mate = MateMX('/dev/ttyUSB0')

# Check that an MX unit is attached and is responding
mate.scan(0)

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

