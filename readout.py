from mate import MateController

mate = MateController('COM19')

status = mate.read_status()

print "PV Voltage:", status.pv_voltage
print "PV Current:", status.pv_current
print "Charge Current:", status.charge_current
print "Daily kWh:", status.daily_kwh
print "Daily Ah:", status.daily_ah
print "Battery Voltage:", status.bat_voltage
