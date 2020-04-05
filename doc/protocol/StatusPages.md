# Status Packets #

All Outback devices provide Status packets in response to a Status command:

```
        Port (00: No Hub)
        |  Command (04: Status)
        |  | Address (01: Status Page 01)
        |  | |     Value (Unused)
        |  | |     |     Checksum
        |  | |………| |………| |………|
  TX: 100 02 00 01 00 00 00 03                           (Command)
  RX: 102 11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF   (Response)
        | |………………………………………………………………………………………………| |………|
        | |                                      Checksum
        | Status page
        Device Type
```

Status responses are always 13 bytes long, but unlike other commands the first byte indicates the type of device (and therefore the type of status packet) that is being transmitted.

Checksum is a simple sum of all bytes (not including the 9th bit)

The MATE asks for a status page once per second, except for the FLEXnet DC status pages 0D..0F which are only queried when a particular screen is shown.

# MX/CC #

```
81 22 33 44 55 66 77 88 99 AA BB CC DD
||  |  |  |  |  |  |  |  | |---| |---|  
||  |  |  |  |  |  |  |  |     |     +- in_voltage      (uint16 / 10.0)
||  |  |  |  |  |  |  |  |     +------- out_voltage     (uint16 / 10.0)
||  |  |  |  |  |  |  |  +------------- kwh             (int16 / 10.0, lower byte)
||  |  |  |  |  |  |  +---------------- error           (bit field)
||  |  |  |  |  |  +------------------- status          (01..04)
||  |  |  |  |  +---------------------- aux mode / state
||  |  |  |  +------------------------- AH lower byte   (int12)
||  |  |  +---------------------------- kwh             (int16 / 10.0, upper byte)
||  |  +------------------------------- out_amps_dc     (int8, 0x80=0.0)
||  +---------------------------------- in_amps_dc      (int8, 0x80=0.0)
|+------------------------------------- out_amps_dc     (tenths, 0x01=0.1A, 0x0F=1.5A)  FM80/FM60 only
+-------------------------------------- AH upper nibble (int12, 0x800=0.0)
```

This status packet is quite tightly packed, and the signed integers are not your typical 2's complement.

Also, the LCD cannot display all possible values and will truncate the top digit. In practice these undisplayable values should never be encountered.

If bit7 in byte[0] is 0, then AH is not displayed in CC TOTALS screen.
Presumably this is because the LCD can't display negative AmpHours, but the value is signed? Either that or there is a flag jammed into the upper nibble.

Aux Mode is bits 0..5 (0x3F), Aux State is bit 6 (0x40)

Sample values:
```
Mode: (blank)
In 244.5 vdc (?)62 adc
Out 70.7 vdc (?)79 adc
```

# FX #

```
11 22 33 44 55 66 77 88 99 AA BB CC DD
 |  |  |  |  |  |  |  |  | |---|  |  |
 |  |  |  |  |  |  |  |  |     |  |  +- warnings
 |  |  |  |  |  |  |  |  |     |  +---- misc_byte       (bit0: 230V, bit7: Aux State)
 |  |  |  |  |  |  |  |  |     +------- battery_voltage (int16 / 10.0)
 |  |  |  |  |  |  |  |  +------------- ac_mode         (0: No AC, 1: AC Drop, 2: AC Use)
 |  |  |  |  |  |  |  +---------------- errors          
 |  |  |  |  |  |  +------------------- operational_mode
 |  |  |  |  |  +---------------------- sell_current    (uint8*)
 |  |  |  |  +------------------------- output_voltage  (uint8*)
 |  |  |  +---------------------------- input_voltage   (uint8*)
 |  |  +------------------------------- buy_current     (uint8*)
 +------------------------------------- chg_current     (uint8*)
```

**NOTE:** When misc.230V == 1, you must multiply voltages by 2, and divide currents by 2


# FLEXnet DC #

The FLEXnet DC power monitor has multiple status pages, which are queried and combined. Pages 0A..0C are queried once per second, while pages 0D..0F are queried only every ~13 seconds.

Pages 0A..0C should be combined before parsing, as some values straddle adjacent pages.

**TODO:** The following is unaccounted for:
- Shunt A/B/C enabled flag
- Battery temperature
- Status flags
- Charge factor corrected  battery AH/KWH

## PAGE 0A ##
```
ff c8 00 5b 00 00 01 00 4c ff f2 00 17 (Capture from real device)
11 22 33 44 55 66 77 88 99 AA BB CC DD
|---| |---| |---| |---|  | |---| |---|
    |     |     |     |  |     |     +- shuntb_kw  (int16 / 100.0)
    |     |     |     |  |     +------- shunta_kw  (int16 / 100.0)
    |     |     |     |  +------------- soc        (uint8) %
    |     |     |     +---------------- bat_v      (int16 / 10.0)
    |     |     +---------------------- shuntc_cur (int16 / 10.0)
    |     +---------------------------- shuntb_cur (int16 / 10.0)
    +---------------------------------- shunta_cur (int16 / 10.0)
```

Sample values:
```
DC NOW 60.0V 153%
DC BAT 60.0V 153%

Shunt A 438.6A -18.290kW
Shunt B 1312.4A -30.910kW
Shunt C 2186.2A  0.000kW
```

## PAGE 0B ##
```
00 00 00 21 00 5b 00 38 00 23 00 17 00 (Capture from real device)
11 22 33 44 55 66 77 88 99 AA BB CC DD
|---|  |  | |---| |---| |---| |---|  +- now_out_kw   (upper byte / 100.0)
    |  |  |     |     |     |     +---- now_in_kw    (int16 / 100.0)
    |  |  |     |     |     +---------- now_bat_cur  (int16 / 10.0)
    |  |  |     |     +---------------- now_out_cur  (int16 / 10.0)
    |  |  |     +---------------------- now_in_cur   (int16 / 10.0)
    |  |  +---------------------------- flags
    |  +------------------------------- unknown
    +---------------------------------- shuntc_kw    (int16 / 100.0)
```

Sample values:
```
DC NOW
In   2186.2A -74.600kW
Out  3060.0A -89.600kW
Bat -2619.8A -0.000kW
```

flags:
- bit7 : Full settings met
- bit6 : Unknown
- bit5 : Unknown
- bit0 : Unknown


## PAGE 0C ##
```
0e 00 09 00 51 00 6a ff e7 00 cf 01 02 (Capture from real device)
11 22 33 44 55 66 77 88 99 AA BB CC DD
 | |---| |---| |---| |---| |---| |---|
 |     |     |     |     |     |     +- today_out_kwh (int16 / 100.0)
 |     |     |     |     |     +------- today_in_kwh  (int16 / 100.0)
 |     |     |     |     +------------- today_bat_ah  (int16)
 |     |     |     +------------------- today_out_ah  (int16)
 |     |     +------------------------- today_in_ah   (int16)
 |     +------------------------------- now_bat_kw    (int16 / 100.0)
 +------------------------------------- now_out_kw    (lower byte / 100.0)
```

Sample values:
```
DC NOW BAT KW : 87.550kW
DC NOW OUT KW : .170kW  DC TODAY IN AH : 7493AH -18.29kWH
DC TODAY OUT AH : 6231AH -30.91kWH
DC TODAY BAT AH : -567AH 0.00kWH  

DC TODAY OUT KWH : FF FF : 26.39kWH
```

## PAGE 0D ##
```
ff cd 00 13 fe fa 02 76 01 70 ff 91 00 (Capture from real device)
11 22 33 44 55 66 77 88 00 00 00 00 00
|---| |---|     |
    |     |     +---------------------- unknown (0x01)
    |     +---------------------------- days_since_full (int16 / 10.0)
    +---------------------------------- today_bat_kwh   (int16 / 100.0)
```

Sample values:
```
DC TODAY BAT KWH : 43.86kWH

Days since full charge: 12.4
```

## PAGE 0E ##
```
ff 00 90 fd 90 01 6a 00 00 ff 05 00 8c (Capture from real device)
11 22 33 44 55 66 77 88 99 AA BB CC DD
         |---| |---| |---| |---| |---|
             |     |     |     |     +- shuntb_ah  (int16)
             |     |     |     +------- shunta_ah  (int16)
             |     |     +------------- shuntc_kwh (int16 / 100.0)
             |     +------------------- shuntb_kwh (int16 / 100.0)
             +------------------------- shunta_kwh (int16 / 100.0)
```

Sample values:
```
Shunt A -1829AH 74.93kWH
Shunt B -3091AH 62.31kWH
Shunt C     0AH -5.67kWH
```

## PAGE 0F ##
```
00 00 47 ff 88 fe e4 0f 00 00 00 00 00 (Capture from real device)
55 66 62 11 22 33 44 0f 00 00 00 00 00
|---|  | |---| |---|  |
    |  |     |     |  +---------------- unknown (0x0F)
    |  |     |     +------------------- bat_net_kwh   (int16 / 100.0)
    |  |     +------------------------- bat_net_ah    (int16)
    |  +------------------------------- min_soc_today (uint8)
    +---------------------------------- shuntc_ah     (int16)
```

Sample values:
```
0x1122 : 4386AH
0x3344 : (6)31.24kWH  (Note: 5th digit truncated)
0xFFFF : -1AH
0x5566 : (2)1862AH
```
