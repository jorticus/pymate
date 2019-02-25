# pyMATE

![pyMATE](http://jared.geek.nz/pymate/images/thumbs/tile_thumbB.png "pyMATE")

pyMATE is a python library that can be used to emulate an Outback MATE unit, and talk to any supported
Outback Power Inc. device such as an MX charge controller, an FX inverter, a FlexNET DC monitor, or a hub with
multiple devices attached to it.

You will need a simple adapter circuit and a TTL serial port. For more details, see [jared.geek.nz/pymate](http://jared.geek.nz/pymate)

Also, to see the library in action, check out my post on connecting it with Grafana! [jared.geek.nz/grafana-outback-solar](http://jared.geek.nz/grafana-outback-solar)

## MX Interface

To set up communication with an MX charge controller:
    
```python
mate_bus = MateNET('COM1')         # Windows
mate_bus = MateNET('/dev/ttyUSB0') # Linux

mate_mx = MateMX(mate_bus, port=0) # 0: No hub. 1-9: Hub port
mate_mx.scan()  # This will raise an exception if the device isn't found
```
    
You can now communicate with the MX as though you are a MATE device.

### Status

You can query a status with `mate_mx.get_status()`. This will return an [MXStatusPacket](matenet/mx.py#L14) with the following information:

```python
status = mate_mx.get_status()
status.amp_hours       # 0 - 255 Ah
status.kilowatt_hours  # 0.0 - 6553.5 kWh
status.pv_current      # 0 - 255 A
status.bat_current     # 0 - 255 A
status.pv_voltage      # 0.0 - 6553.5 V
status.bat_voltage     # 0.0 - 6553.5 V
status.status          # A status code. See MXStatusPacket.STATUS_* constants.
status.errors          # A 8 bit bit-field (documented in Outback's PDF)
```

All values are floating-point numbers with units attached. You can convert them to real floats with eg. `float(status.pv_voltage) # 123.4`, or display them as a human-friendly string with `str(status.pv_voltage) # '123.4 V'`
    
### Log Pages
    
You can also query a log page (just like you can on the MATE), up to 127 days in the past: (Logpages are stored at midnight, 0 is the current day so far)

```python
logpage = mate_mx.get_logpage(-1)  # Yesterday's logpage
logpage.bat_max         # 0.0 - 102.3 V
logpage.bat_min         # 0.0 - 102.3 V
logpage.kilowatt_hours  # 0.0 - 409.5 kWh
logpage.amp_hours       # 0 - 16383 Ah
logpage.volts_peak      # 0 - 255 Vpk
logpage.amps_peak       # 0.0 - 102.3 Apk
logpage.absorb_time     # 4095 min  (minutes)
logpage.float_time      # 4095 min
logpage.kilowatts_peak  # 0.000 - 2.047 kWpk
logpage.day             # 0 .. -127
```
    
### Properties
    
Additionally, you can query individual registers (just like you can on the MATE - though it's buried quite deep in the menus somewhere)

```python
mate_mx.charger_watts
mate_mx.charger_kwh
mate_mx.charger_amps_dc
mate_mx.bat_voltage
mate_mx.panel_voltage
mate_mx.status
mate_mx.aux_relay_mode
mate_mx.max_battery
mate_mx.voc
mate_mx.max_voc
mate_mx.total_kwh_dc
mate_mx.total_kah
mate_mx.max_wattage
mate_mx.setpt_absorb
mate_mx.setpt_float
```
    
Note that to read each of these properties a separate message must be sent, so it will be slower than getting values from a status packet.

## FX Interface

I don't have an FX unit to test with, so I cannot guarantee this will function. I determined everything by poking values at the MATE, and seeing what it sends back.

To set up communication with an FX inverter:

```python
mate_bus = MateNET('COM1')         # Windows
mate_bus = MateNET('/dev/ttyUSB0') # Linux

mate_mx = MateFX(mate_bus, port=0) # 0: No hub. 1-9: Hub port
mate_fx.scan()

status = mate_fx.get_status()
errors = mate_fx.errors
warnings = mate_fx.warnings
```

There's still a few unknowns, so you'll have to look through the source code ([fx.py](matenet/fx.py) to work out what this produces, at least until I have a unit to test with myself.

### Controls

You can control an FX unit like you can through the MATE unit (untested though!):

```python
mate_fx.inverter_control = 0  # 0: Off, 1: Search, 2: On
mate_fx.acin_control = 0      # 0: Drop, 1: Use
mate_fx.charge_control = 0    # 0: Off, 1: Auto, 2: On
mate_fx.aux_control = 0       # 0: Off, 1: Auto, 2: On
mate_fx.eq_control = 0        # 0: Off, ??? not sure
```
    
These are implemented as python properties, so you can read and write them. Writing to them affects the FX unit.
    
### Properties

There are a bunch of interesting properties, a lot not available from the status packet

```python
mate_fx.disconn_status
mate_fx.sell_status
mate_fx.temp_battery
mate_fx.temp_air
mate_fx.temp_fets
mate_fx.temp_capacitor
mate_fx.output_voltage
mate_fx.input_voltage
mate_fx.inverter_current
mate_fx.charger_current
mate_fx.input_current
mate_fx.sell_current
mate_fx.battery_actual
mate_fx.battery_temp_compensated
mate_fx.absorb_setpoint
mate_fx.absorb_time_remaining
mate_fx.float_setpoint
mate_fx.float_time_remaining
mate_fx.refloat_setpoint
mate_fx.equalize_setpoint
mate_fx.equalize_time_remaining
```

## Example Server

For convenience, a simple server is included that captures data periodically
and uploads it to a remote server via a REST API.
The remote server then stores the received data into a database of your choice.



I am open to contributions, especially if you can test it with any devices I don't have.
