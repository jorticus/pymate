
from datetime import timedelta, time

SERIAL_PORT             = 'COM6'
SERIAL_PROTO            = 'PJON'  # 'PJON' or 'MATE'

MQTT_SERVER             = 'edoras.middle-earth'
MQTT_PORT               = 1883
MQTT_USER               = 'homeassistant'
MQTT_PASSWORD           = 'meme machine'
MQTT_TOPIC_PREFIX       = 'mate'

MX_STATUS_INTERVAL      = timedelta(seconds=10)
FX_STATUS_INTERVAL      = timedelta(seconds=60)
LOGPAGE_RETRIEVAL_TIME  = time(hour=0, minute=5)  # 5 minutes past midnight (retrieves previous day)

#LOGFILE                 = '/tmp/log/matesrv.log'
LOGFILE                 = 'matesrv.log'