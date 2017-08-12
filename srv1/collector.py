#!/usr/bin/python

# Author: Jared Sanson <jared@jared.geek.nz>
#
# A very basic collection & upload script for pyMATE,
# designed for resource-constrained systems
# (My particular system barely has enough flash space to fit Python!)
#

from matenet import MateMX
from time import sleep
from datetime import datetime, timedelta, time
from threading import Thread, BoundedSemaphore
from collections import deque
from base64 import b64encode
import urllib2
import json
import logging

from settings import *

log = logging.getLogger('main')
log.setLevel(logging.DEBUG)

if LOGFILE:
	fh = logging.FileHandler(LOGFILE)
	fh.setLevel(logging.INFO)
	fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
	log.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

log.info("MATE Data Collector (MX)")

# Create a new MATE emulator
mate = MateMX(SERIAL_PORT)

# Check that an MX unit is attached and responding
mate.scan(MX_PORT)

log.info("Revision: " + str(mate.revision))

def timestamp():
	""" '2016-06-18T15:13:38.929000' """
	ts = datetime.utcnow()
	utcoffset = datetime.now() - ts
	return ts.isoformat(), int(utcoffset.total_seconds())

def upload_packet(packet):
	"""
	Upload a JSON packet to the server.
	If we can't communicate, just drop the packet.
	"""
	try:
		log.debug("Upload: " + str(packet))
		r = urllib2.Request(
			ENDPOINT_URL+'/'+packet['type'],
			headers={'Content-Type': 'application/json'},
			data=json.dumps(packet)
		)
		urllib2.urlopen(r)
	except:
		log.exception("EXCEPTION in upload_packet()")
	
def collect_logpage():
	"""
	Collect a log page.
	If this fails, log and continue
	"""
	try:
		logpage = mate.get_logpage(-1)  # Get yesterday's logpage

		day = datetime(now.year, now.month, now.day-1)

		ts, tz = timestamp()
		return {
			'type': 'mx-logpage',
			'data': b64encode(logpage.raw),
			'ts': ts,
			'tz': tz,
			'date': day.strftime('%Y-%m-%d')
		}
	except:
		log.exception("EXCEPTION in collect_logpage()")
		return None
	
def collect_status():
	"""
	Collect the current status.
	If this fails, log and continue
	"""
	try:
		status = mate.get_status()

		ts, tz = timestamp()
		return {
			'type': 'mx-status',
			'data': b64encode(status.raw),  # Just send the raw data, and decode it server-side
			'ts': ts,
			'tz': tz,
			'extra': {
				# To supplement the status packet data
				'chg_w': float(mate.charger_watts)
			}
		}
	except:
		log.exception("EXCEPTION in collect_status()")
		return None

##### COLLECTION STARTS #####

log.info("Starting collection...")
now = datetime.now()

# Calculate datetime of next status collection
t_next_status = now + STATUS_INTERVAL

# Calculate datetime of next logpage collection
d = now.date()
t = LOGPAGE_RETRIEVAL_TIME
t_next_logpage = datetime(d.year, d.month, d.day+1, t.hour, t.minute, t.second, t.microsecond)
log.debug("Next logpage: " + str(t_next_logpage))

# Collect status and log pages
while True:
	try:
		sleep(1.0)
		now = datetime.now()

		# Time to collect a log page
		if now >= t_next_logpage:
			t_next_logpage += timedelta(days=1)
			log.debug("Next logpage: " + str(t_next_logpage))

			packet = collect_logpage()
			if packet:
				upload_packet(packet)

		# Time to collect status
		if now >= t_next_status:
			t_next_status = now + STATUS_INTERVAL
			
			packet = collect_status()
			if packet:
				upload_packet(packet)
		
		
	except Exception as e:
		# Don't terminate the program, log and keep collecting.
		# sleep will keep things from going out of control.
		log.exception("EXCEPTION in main")

