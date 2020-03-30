# MX Registers

Address |Description                | Units / Value     | R/W | MATE Screen 
--------|---------------------------|-------------------|-----|-------------
0000    | Device type               | 0002 = MX         |
0001    | ??                        | 0000              |
0002    | FW Rev A (AAA.BBB.CCCC)   | AAA               |
0003    | FW Rev B                  | BBB               |
0004    | FW Rev C                  | CCCC              |
0008    | Battery Voltage           |                   |     |
000F    | Max Battery               | V*10              |     |
0010    | VOC                       | *10               |     |
0012    | Max VOC                   | *10               |     |
0013    | Total kWh DC              | kWh               |     |
0014    | Total kAh kAh             |                   |     |
0015    | Max Wattage               | W                 |     |
0017    | Output current limit      | A (tenths)        | R/W | ADV/CC/CHGR
0018    | Float voltage             | V                 | R/W | ADV/CC/CHGR
0019    | Absorb voltage            | V                 | R/W | ADV/CC/CHGR
001E    | Eq Voltage                | V tenths          | R/W | ADV/CC/EQ
00D2    | Eq Time                   | Hours             | R/W | ADV/CC/EQ
00D3    | Auto Eq Interval          | Days              | R/W | ADV/CC/EQ
00CB    | Aux Mode                  | 0: Float          | R/W | ADV/CC/AUX
01C9    | Aux Output Control        | 03: Off, 83: On   | R/W | ADV/CC/AUX
0020    | Absorb end amps           | A                 | R/W | ADV/CC/ADVANCED
00D4    | Snooze Mode               | A (tenths)        | R/W | ADV/CC/ADVANCED
0021    | Wakeup mode VOC change    |  V (tenths)       | R/W | ADV/CC/ADVANCED
0022    | Wakeup mode time          | Minutes           | R/W | ADV/CC/ADVANCED
00D5    | MPPT mode                 | 0: Auto Track     | R/W | ADV/CC/ADVANCED
00D6    | Grid tie mode             | 0: NonGT          | R/W | ADV/CC/ADVANCED
0023    | Park MPP                  | % tenths          | R/W | ADV/CC/ADVANCED
00D7    | Mpp range limit %VOC      | 0: minimum full   | R/W | ADV/CC/ADVANCED
00D8    | Mpp range limit %VOC      | 0: maximum 80%    | R/W | ADV/CC/ADVANCED
00D9    | Absorb time               | Hours tenths      | R/W | ADV/CC/ADVANCED
001F    | Rebulk voltage            | VDC tenths        | R/W | ADV/CC/ADVANCED
00DA    | Vbatt Calibration         | VDC               | R/W | ADV/CC/ADVANCED
00DB    | RTS Compensation          | 0: Wide           | R/W | ADV/CC/ADVANCED
0025    | RTS comp upper limit      | V tenths          | R/W | ADV/CC/ADVANCED
0024    | RTS comp lower limit      | V tenths          | R/W | ADV/CC/ADVANCED
00DC    | Auto restart mode         | ?                 | R/W | ADV/CC/ADVANCED
00C8    | RESET TO FACTORY DEFAULTS | -                 | W   | ADV/CC/ADVANCED
0170    | SetPt Absorb              | V*10              |     |
0172    | SetPt Float               | V*10              |     |
016A    | Charger Watts             | W                 |     |
01C6    | Panel Voltage             | V                 |     |
01C7    | Charger Amps DC           | A (0:+128)        |     |
01C8    | Status                    |                   |     |
01C9    | Aux Relay Mode            |                   |     |
01EA    | Charger kWh               | kWh*10            |     |

**NOTE**: Do not rely on this information as it was determined by poking values at a MATE, not by observing actual communication. Ensure you do your on testing before relying on this information!

All values are 16-bit signed integers

## Enums ##

    STATUS_SLEEPING = 0
    STATUS_FLOATING = 1
    STATUS_BULK = 2
    STATUS_ABSORB = 3
    STATUS_EQUALIZE = 4