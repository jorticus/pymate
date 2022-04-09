from pymate.matenet import MateNET, MateFXDevice
from time import sleep

print("MATE emulator (FX)")

# Create a MateNET bus connection
bus = MateNET('/dev/ttyUSB0', supports_spacemark=False)

# Create a new MATE emulator attached to the specified port:
mate = MateFXDevice(bus, port=bus.find_device(MateNET.DEVICE_FX))

# Check that an FX unit is attached and is responding
mate.scan()

# Query the device revision
print(f"Revision: {mate.revision}")
