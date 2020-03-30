
from datetime import timedelta, time

SERIAL_PORT = '/dev/ttyUSB0'
STATUS_INTERVAL = timedelta(seconds=10)
FXSTATUS_INTERVAL = timedelta(seconds=60)
DCSTATUS_INTERVAL = timedelta(seconds=10)
LOGPAGE_RETRIEVAL_TIME = time(hour=0, minute=5)  # 5 minutes past midnight (retrieves previous day)
ENDPOINT_URL = 'http://localhost:5000/mate'
LOGFILE = '/tmp/log/mate-collector.log'
