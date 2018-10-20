from pymate.matenet import MateNET, MateMXDevice
import sysfrom time import sleep

print("MATE emulator (MX)")

if len(sys.argv) <= 1:
    raise Exception("COM Port not specified.\nUsage:\n    %s /dev/ttyUSB0   (Linux)\n    %s COM1           (Windows)" % (sys.argv[0], sys.argv[0]))
comport = sys.argv[1]

mate = MateMX(comport)

# Create a MateNET bus connection
bus = MateNET(comport)

# Find an MX device on the bus
port = bus.find_device(MateNET.DEVICE_MX)

# Create a new MATE emulator attached to the specified port
mate = MateMXDevice(bus, port)

# Check that an MX unit is attached and is responding
mate.scan()

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

