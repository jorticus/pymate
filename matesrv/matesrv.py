#!/usr/bin/python

# Author: Jared Sanson <jared@jared.geek.nz>
#
# MATE<->MQTT bridge
#
# Bridges MATE with MQTT, and samples status packets regularly
#

from pymate.matenet import MateNET, MateNETPJON, MateMXDevice, MateFXDevice
import paho.mqtt.client as mqtt
import logging
import settings

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

log = logging.getLogger('mate')
log.setLevel(logging.INFO)
log.addHandler(ch)

if settings.LOGFILE:
    fh = logging.FileHandler(settings.LOGFILE)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log.addHandler(fh)

log.info("MATEsrv v1.0")

# Set up class for interfacing with the serial bus
if settings.SERIAL_PROTO == 'PJON':
    port = MateNETPJON(settings.SERIAL_PORT)
    bus = MateNET(port)

    # PJON is more reliable, so we don't need to retry packets
    bus.RETRY_PACKET = 0
    bus.RX_TIMEOUT = 0.05

elif settings.SERIAL_PROTO == 'MATE':
    bus = MateNET(settings.SERIAL_PORT)
else:
    raise RuntimeError('Invalid setting SERIAL_PROTO. Must be PJON or MATE')

log.info('Scanning for attached devices...')
ports = bus.enumerate()

# Find and connect to an MX charge controller
try:
    port = bus.find_device(MateNET.DEVICE_MX)
    mx = MateMXDevice(bus, port)
    mx.scan()
    log.info('Connected to MX device')
    log.info('Revision: ' + str(mx.revision))
except Exception as ex:
    log.exception("Error connecting to MX")

# Find and connect to an FX inverter
try:
    port = bus.find_device(MateNET.DEVICE_FX)
    fx = MateFXDevice(bus, port)
    fx.scan()
    log.info('Connected to FX device')
    log.info('Revision: ' + str(fx.revision))
except Exception as ex:
    log.exception("Error connecting to FX")



# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    #client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #print(msg.topic+" "+str(msg.payload))
    pass


# Connect to MQTT server
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASSWORD)

log.info('Connecting to MQTT server: %s:%d', settings.MQTT_SERVER, settings.MQTT_PORT)
mqtt_client.connect(settings.MQTT_SERVER, settings.MQTT_PORT)


# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
mqtt_client.loop_forever()

# TODO... create more threads for servicing MATE devices