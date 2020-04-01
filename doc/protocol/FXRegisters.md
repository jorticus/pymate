# FX Registers

Address |Description                | Units / Value          | R/W | MATE Screen 
--------|---------------------------|------------------------|-----|-------------
0000    | Device type               | 0003 = FX              |     |
0001    | FW Revision               |                        |     |
0002    | FW Rev A (AAA.BBB.CCCC)   | AAA                    |     | STATUS/FX/METER
0003    | FW Rev B                  | BBB                    |     | STATUS/FX/METER
0004    | FW Rev C                  | CCC                    |     | STATUS/FX/METER
000A    | Float setpoint            | V/10                   |     | STATUS/FX/BATT
000B    | Absorb setpoint           | V/10                   |     | STATUS/FX/BATT
000C    | Equalize setpoint         | V/10                   |     | STATUS/FX/BATT
000D    | Refloat Setpoint          | V/10                   |     | STATUS/FX/BATT
0016    | Battery temp compensated  | V/10                   |     | STATUS/FX/BATT
0019    | Battery actual            | V/10                   |     | STATUS/FX/BATT
002C    | Input voltage             | V                      |     | STATUS/FX/METER
002D    | Output voltage            | V                      |     | STATUS/FX/METER
0032    | Battery temperature       | 0..255                 |     | STATUS/FX/BATT
0033    | Air temperature           | 0..255                 |     | STATUS/FX/WARN
0034    | MOSFET temperature        | 0..255                 |     | STATUS/FX/WARN
0035    | Capacitor temperature     | 0..255                 |     | STATUS/FX/WARN
0038    | Equalize mode             | 0: Off                 | R/W | STATUS/FX/MODE
0039    | Errors                    | bitfield               |     | STATUS/FX/ERROR
003A    | AC IN mode                | 0: Drop 1: Use         | R/W | STATUS/FX/MODE
003C    | Charger mode              | 0: Off 1: Auto 2: On   | R/W | STATUS/FX/MODE
003D    | Inverter mode             | 0: Off 1: Search 2: On | R/W | STATUS/FX/MODE
0059    | Warnings                  | bitfield               |     | STATUS/FX/WARN
005A    | Aux mode                  | 0: Off 1: Auto 2: On   | R/W | STATUS/FX/MODE
006A    | Charger current           | A/10                   |     | STATUS/FX/METER
006B    | Sell current              | A/10                   |     | STATUS/FX/METER
006C    | Input current             | A/10                   |     | STATUS/FX/METER
006D    | Inverter current          | A/10                   |     | STATUS/FX/METER
006E    | Float time remaining      | h/10                   |     | STATUS/FX/BATT
0070    | Absorb time remaining     | h/10                   |     | STATUS/FX/BATT
0071    | Equalize time remaining   | h/10                   |     | STATUS/FX/BATT
0084    | Disconn status            | enum                   |     | STATUS/FX/DISCONN
008F    | Sell status               | enum                   |     | STATUS/FX/SELL
0029    | Search sensitivity        | int                    | R/W [INC/DEC] | ADV/FX/INVERTER
0062    | Search pulse length       | 0 cycles               | R/W [INC/DEC] | ADV/FX/INVERTER
0063    | Search pulse spacing      | 0 cycles               | R/W [INC/DEC] | ADV/FX/INVERTER
000E    | Low battery cutout setpt  | V/10                   | R/W [INC/DEC] | ADV/FX/INVERTER
000F    | Low battery cutin setpt   | V/10                   | R/W [INC/DEC] | ADV/FX/INVERTER
0083    | Adjust output voltage     | VAC                    | R/W [INC/DEC] | ADV/FX/INVERTER
0028    | Charger limit             | AAC/10                 | R/W [INC/DEC] | ADV/FX/CHARGER
000B    | Absorb setpoint           | VDC/10                 | R/W [INC/DEC] | ADV/FX/CHARGER
001F    | Absorb time limit         | hrs/10                 | R/W [INC/DEC] | ADV/FX/CHARGER
000A    | Float setpoint            | VDC/10                 | R/W [INC/DEC] | ADV/FX/CHARGER
0021    | Float time period         | hrs/10                 | R/W [INC/DEC] | ADV/FX/CHARGER
000D    | Refloat setpoint          | VDC/10                 | R/W [INC/DEC] | ADV/FX/CHARGER
000C    | Equalize setpoint         | VDC/10                 | R/W [INC/DEC] | ADV/FX/CHARGER
0020    | Equalize time period      | hrs/10                 | R/W [INC/DEC] | ADV/FX/CHARGER
002A    | AC1/Grid lower limit      | VAC                    | R/W [INC/DEC] | ADV/FX/GRID
002B    | AC1/Grid upper limit      | VAC                    | R/W [INC/DEC] | ADV/FX/GRID
0027    | AC1/Grid input limit      | AAC/10                 | R/W [INC/DEC] | ADV/FX/GRID
004D    | AC1/Grid transfer delay   | cycles                 | R/W [INC/DEC] | ADV/FX/GRID
0037    | Gen input connect delay   | min/10                 | R/W [INC/DEC] | ADV/FX/GEN
0044    | AC2/Gen lower limit       | VAC                    | R/W [INC/DEC] | ADV/FX/GEN
0045    | AC2/Gen upper limit       | VAC                    | R/W [INC/DEC] | ADV/FX/GEN
007B    | AC2/Gen input limit       | AAC/10                 | R/W [INC/DEC] | ADV/FX/GEN
0022    | AC2/Gen transfer delay    | cycles                 | R/W [INC/DEC] | ADV/FX/GEN
003B    | AC2/Gen support           | ON/OFF                 | R/W [OFF/ON] | ADV/FX/GEN
005A    | Aux output control        | Auto                   | R/W [INC/DEC] | ADV/FX/AUX
003E    | Aux output function       | Remote/...             | R/W [INC/DEC] | ADV/FX/AUX
0011    | Genalert on setpont       | VDC/10                 | R/W [INC/DEC] | ADV/FX/AUX
003F    | Genalert on delay         | minutes                | R/W [INC/DEC] | ADV/FX/AUX
0010    | Genalert off setpoint     | VDC/10                 | R/W [INC/DEC] | ADV/FX/AUX
0040    | Genalert off delay        | minutes                | R/W [INC/DEC] | ADV/FX/AUX
0012    | Loadshed off setpoint     | VDC/10                 | R/W [INC/DEC] | ADV/FX/AUX
0013    | Ventfan on setpoint       | VDC/10                 | R/W [INC/DEC] | ADV/FX/AUX
0042    | Ventfan off period        | minutes                | R/W [INC/DEC] | ADV/FX/AUX
0014    | Diversion on setpoint     | VDC/10                 | R/W [INC/DEC] | ADV/FX/AUX
006F    | Diversion off delay       | seconds                | R/W [INC/DEC] | ADV/FX/AUX
0079    | Stack 1-2ph phase         | Master/...             | R/W [INC/DEC] | ADV/FX/STACK
0075    | Power save level (master) | 0                      | R/W [INC/DEC] | ADV/FX/STACK
0074    | Power save level (slave)  | 0                      | R/W [INC/DEC] | ADV/FX/STACK
001B    | Sell RE volts             | VDC/10                 | R/W [INC/DEC] | ADV/FX/SELL
0067    | Grid tie window           | "IEEE"/...             | R/W [INC/DEC] | ADV/FX/SELL
008A    | Grid tie authority        | "No sell"/...          | R/W [INC/DEC] | ADV/FX/SELL
002C    | VAC input adjustment      | VAC                    | R/W [INC/DEC] | ADV/FX/CALIBRATE
002D    | VAC output adjustment     | VAC                    | R/W [INC/DEC] | ADV/FX/CALIBRATE
0019    | Battery adjustment        | VDC/10                 | R/W [INC/DEC] | ADV/FX/CALIBRATE
0058    | RESET SEQUENCE 1          | 0062                   | R/W | ADV/FX/INVERTER
????    | RESET SEQUENCE 2          | ????                   | R/W | ADV/FX/INVERTER
 

**NOTE**: Do not rely on this information as it was determined by poking values at a MATE, not by observing actual communication. Ensure you do your on testing before relying on this information!

**TODO**: The FX has an interesting sequence for performing factory reset.

All values are 16-bit signed integers

## Enums / Bitfields

``` python
    # Error bit-field
    ERROR_LOW_VAC_OUTPUT = 0x01 # Inverter could not supply enough AC voltage to meet demand
    ERROR_STACKING_ERROR = 0x02 # Communication error among stacked FX inverters (eg. 3 phase system)
    ERROR_OVER_TEMP      = 0x04 # FX has reached maximum allowable temperature
    ERROR_LOW_BATTERY    = 0x08 # Battery voltage below low battery cut-out setpoint
    ERROR_PHASE_LOSS     = 0x10
    ERROR_HIGH_BATTERY   = 0x20 # Battery voltage rose above safe level for 10 seconds
    ERROR_SHORTED_OUTPUT = 0x40 
    ERROR_BACK_FEED      = 0x80 # Another power source was connected to the FX's AC output
```
``` python
    # Warning bit-field
    WARN_ACIN_FREQ_HIGH         = 0x01 # >66Hz or >56Hz
    WARN_ACIN_FREQ_LOW          = 0x02 # <54Hz or <44Hz
    WARN_ACIN_V_HIGH            = 0x04 # >140VAC or >270VAC
    WARN_ACIN_V_LOW             = 0x08 # <108VAC or <207VAC
    WARN_BUY_AMPS_EXCEEDS_INPUT = 0x10
    WARN_TEMP_SENSOR_FAILED     = 0x20 # Internal temperature sensors have failed
    WARN_COMM_ERROR             = 0x40 # Communication problem between us and the FX
    WARN_FAN_FAILURE            = 0x80 # Internal cooling fan has failed
```
``` python
    # Operational Mode enum
    STATUS_INV_OFF = 0
    STATUS_SEARCH = 1
    STATUS_INV_ON = 2
    STATUS_CHARGE = 3
    STATUS_SILENT = 4
    STATUS_FLOAT = 5
    STATUS_EQ = 6
    STATUS_CHARGER_OFF = 7
    STATUS_SUPPORT = 8          # FX is drawing power from batteries to support AC
    STATUS_SELL_ENABLED = 9     # FX is exporting more power than the loads are drawing
    STATUS_PASS_THRU = 10       # FX converter is off, passing through line AC
```
``` python
    # Reasons that the FX has stopped selling power to the grid
    # (Sell Status)
    SELL_STOP_REASONS = {
        1: 'Frequency shift greater than limits',
        2: 'Island-detected wobble',
        3: 'VAC over voltage',
        4: 'Phase lock error',
        5: 'Charge diode battery volt fault',
        7: 'Silent command',
        8: 'Save command',
        9: 'R60 off at go fast',
        10: 'R60 off at silent relay',
        11: 'Current limit sell',
        12: 'Current limit charge',
        14: 'Back feed',
        15: 'Brute sell charge VAC over'
    }
```