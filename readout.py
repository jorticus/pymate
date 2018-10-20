import sys
from matenet import MateMX
from time import sleep

print("MATE emulator (MX)")

if len(sys.argv) <= 1:
    raise Exception("COM Port not specified.\nUsage:\n    %s /dev/ttyUSB0   (Linux)\n    %s COM1           (Windows)" % (sys.argv[0], sys.argv[0]))
comport = sys.argv[1]

# Create a new MATE emulator attached to the specified serial port:
mate = MateMX(comport)

# Check that an MX unit is attached and is responding
mate.scan(0)

# Query the device revision
print("Revision:", mate.revision)


print("Getting log page... (day:-1)")
logpage = mate.get_logpage(-1)
print(logpage)

while True:
    print("Status:")
    status = mate.get_status()
    print(status)

    sleep(1.0)

