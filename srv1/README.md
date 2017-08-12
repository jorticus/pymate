A very basic collection & upload script for pyMATE,
designed for resource-constrained systems.

My particular system barely has enough flash space to fit Python!

This script will collect the status every 10 seconds (configurable), and a log page at the end of every day,
and upload the result to a server as a JSON-formatted packet

The server should have two POST handlers which accept JSON:

```
POST /mx-logpage
	{
		'type': 'mx-logpage',
		'data': 'BASE64-encoded logpage data',
		'ts': '2017-08-12T17:43:45.029141',
		'tz': 43200,
		'date': '2017-08-11'
	}
```

```
POST /mx-status
	{
		'type': 'mx-status',
		'data': 'BASE64-encoded status data',
		'ts': '2017-08-12T17:43:45.029141',
		'tz': 43200,
		'extra': {
			'chg_w': 0.0
		}
	}
```
