#!/usr/bin/python
#
# MATE Collector
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Simple bare-bones server for collecting MATE data and storing it on a remote server,
# via a baisc REST service.
# See srv2/receiver.py for the other side of this.
#

from matenet import MateMX
from time import sleep
from datetime import datetime, timedelta, time
from threading import Thread, BoundedSemaphore
from collections import deque
from base64 import b64encode
import urllib2
import json

from settings import *

print "MATE Data Collector (MX)"

# Create a new MATE emulator
mate = MateMX(SERIAL_PORT)

# Check that an MX unit is attached and responding
mate.scan(MX_PORT)

print "Revision:", mate.revision

packet_queue = deque()
mate_sem = BoundedSemaphore(value=1)  # Only one thread at a time should be allowed to access the MATE bus

print
print "Starting collection..."


def timestamp():
    """ '2016-06-18T15:13:38.929000' """
    ts = datetime.utcnow()
    utcoffset = datetime.now() - ts
    return ts.isoformat(), int(utcoffset.total_seconds())


def collect_status():
    """
    This thread collects status packets at regular intervals
    """
    interval = STATUS_INTERVAL.total_seconds()
    while True:
        try:
            sleep(interval)

            with mate_sem:
                status = mate.get_status()

            ts, tz = timestamp()
            packet_queue.appendleft({
                'type': 'mx-status',
                'data': b64encode(status.raw),  # Just send the raw data, and decode it server-side
                'ts': ts,
                'tz': tz,
                'extra': {
                    # To supplement the status packet data
                    'chg_w': float(mate.charger_watts)
                }
            })
        except Exception as e:
            print "ERROR in collect_status():", e


def collect_logpage():
    """
    This thread collects daily logpages (after midnight)
    """

    d = datetime.now().date()
    t = LOGPAGE_RETRIEVAL_TIME
    t_next = datetime(d.year, d.month, d.day+1, t.hour, t.minute, t.second, t.microsecond)
    print "Next logpage:", t_next
    while True:
        try:
            now = datetime.now()
            if now > t_next:
                t_next += timedelta(days=1)
                print "Next logpage:", t_next

                with mate_sem:
                    logpage = mate.get_logpage(-1)  # Get yesterday's logpage

                day = datetime(now.year, now.month, now.day-1)

                ts, tz = timestamp()
                packet_queue.appendleft({
                    'type': 'mx-logpage',
                    'data': b64encode(logpage.raw),
                    'ts': ts,
                    'tz': tz,
                    'date': day.strftime('%Y-%m-%d')
                })
        except Exception as e:
            print "ERROR in collect_logpage():", e
        sleep(60.0)


status_thread = Thread(target=collect_status, name='status-collector')
logpage_thread = Thread(target=collect_logpage, name='logpage-collector')

# Make sure the threads terminate when the application is killed
status_thread.daemon = True
logpage_thread.daemon = True

status_thread.start()
logpage_thread.start()


def upload_packet(packet):
    while True:
        try:
            print "Upload:", packet

            r = urllib2.Request(
                ENDPOINT_URL+'/'+packet['type'],
                headers={'Content-Type': 'application/json'},
                data=json.dumps(packet)
            )
            urllib2.urlopen(r)
            return
        except Exception as e:
            print "EXCEPTION in upload_packet()", e
            print "Retrying..."
            sleep(1.0)

# Upload (main thread)
while True:
    sleep(1.0)
    try:
        while True:
            packet = packet_queue.pop()
            upload_packet(packet)
    except IndexError:
        continue  # No more packets in queue
    except Exception as e:
        print "EXCEPTION in main()", e

