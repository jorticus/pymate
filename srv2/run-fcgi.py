#!/usr/bin/python

# Usage:
# run-fcgi.py 127.0.0.1 3001
# run-fcgi.py /tmp/mate-collector.sock

import sys
from flup.server.fcgi import WSGIServer
from receiver import app

bindAddress=None
if len(sys.argv) == 2:
	bindAddress = sys.argv[1]
elif len(sys.argv) == 3:
	bindAddress = sys.argv[1:]

if __name__ == '__main__':
	WSGIServer(app, bindAddress=bindAddress).run()
