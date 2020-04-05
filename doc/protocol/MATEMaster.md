# MATE Master Duties

The MATE itself periodically sends commands by itself to other devices in the system.

In particular it has the following duties:

- Date / Time synchronization
- Battery Temperature synchronization
- FBX (Battery Recharging)
- AGS (Automatic Generator System)
- FN-DC Net AmpHours charge float feature


If you are replacing the MATE with pyMATE, I recommend you implement the below features, or connect pyMATE as a 2nd mate.

See `MateDevice.synchronize()`.

## Time / Date Synchronization ##

The registers [`4004`/`4005`] are written every 30 sec to MX/DC devices (not FX), encoded in a particular format:

```
[4004] (TIME)
Bits 15..11 : Hour (24h)
Bits 10..5  : Minute
Bits 4..0   : Second (*2)

[4005] (DATE)
Bits 15..9 : Year  (2000..2127)
Bits 8..5  : Month (0..12)
Bits 4..0  : Day   (0..31)
```

9:09:49 PM would encode as `(21<<11) | (09<<5) | (49>>1) ==  0xA938`.

2020-04-31 would encode as `((2020-2000)<<9) | (04<<5) | (31) == 0x289F`.

Presumably this is used to synchronize the MX/DC's internal clock to the MATE, so they know when to do things like resetting counters at midnight. Without this they still seem to be able to function properly, but I imagine they would get out of sync over time.


## Battery Temperature Synchronization ##

Every 1 minute the MATE will read register [`4000`] from the MX/CC and forward the value to register [`4001`] for attached FX/DC devices.

I believe this register contains the raw battery NTC temperature sensor value, which the DC converts to DegC.

The battery temperature can be read from the DC at register [`00f0`], and reports the temperature in DegC. This register gets updated when register [`4001`] is written to.

```
Temperature Mapping: (CC[`4000`] : DC[`00f0`])
118 : 28C : 0076
125 : 25C : 007d
129 : 24C : 0081
131 : 23C : 0083
133 : 23C : 0085
134 : 22C : 0086
138 : 21C : 008a
139 : 20C : 008b

Approximate formula:
DegC = Round((-0.3576 * raw_temp) + 70.1)
```
