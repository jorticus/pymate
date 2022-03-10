from pymate.matenet import MateNET, MateDCDevice
from time import sleep

print("MATE emulator (FLEXnet DC)")

# Create a MateNET bus connection
bus = MateNET('/dev/ttyUSB0', supports_spacemark=False)

# Create a new MATE emulator attached to the specified port
mate = MateDCDevice(bus, port=bus.find_device(MateNET.DEVICE_FLEXNETDC))

# Check that an FX unit is attached and is responding
mate.scan()

# Query the device revision
print("Revision:", mate.revision)

print(mate.get_status())

print(mate.get_logpage(-2))
