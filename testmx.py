from pymate.matenet import MateNET, MateMXDevice
from time import sleep

import logging

log = logging.getLogger('mate')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

mate_bus = MateNET('COM4')         # Windows

mate_mx = MateMXDevice(mate_bus, port=0) # 0: No hub. 1-9: Hub port
mate_mx.scan()  # This will raise an exception if the device isn't found

status = mate_mx.get_status()
print(status)