# FX Registers

Address |Description                | Units / Value          | R/W | MATE Screen 
--------|---------------------------|------------------------|-----|-------------
0000    | Device type               | 0003 = FX              |     |
0001    | FW Revision               |                        |     |
000A    | Float setpoint            | V                      |     | 
000B    | Absorb setpoint           | V                      |     |
000C    | Equalize setpoint         | V                      |     |
000D    | Refloat Setpoint          | V                      |     |
0016    | Battery temp compensated  | V                      |     |
0019    | Battery actual            | V                      |     |
002C    | Input voltage             | V                      |     |
002D    | Output voltage            | V                      |     |
0032    | Battery temperature       | 0..255                 |     |
0033    | Air temperature           | 0..255                 |     |
0034    | MOSFET temperature        | 0..255                 |     |
0035    | Capacitor temperature     | 0..255                 |     |
0038    | Equalize mode             | 0: Off                 | R/W |
0039    | Errors                    | bitfield               |     |
003A    | AC IN mode                | 0: Drop 1: Use         | R/W |
003C    | Charger mode              | 0: Off 1: Auto 2: On   | R/W |
003D    | Inverter mode             | 0: Off 1: Search 2: On | R/W |
0059    | Warnings                  | bitfield               |     |
005A    | Aux mode                  | 0: Off 1: Auto 2: On   | R/W |
006A    | Charger current           | A                      |     |
006B    | Sell current              | A                      |     |
006C    | Input current             | A                      |     |
006D    | Inverter current          | A                      |     |
006E    | Float time remaining      | h                      |     |
0070    | Absorb time remaining     | h                      |     |
0071    | Equalize time remaining   | h                      |     |
0084    | Disconn status            | enum                   |     |
008F    | Sell status               | enum                   |     |

**NOTE**: Do not rely on this information as it was determined by poking values at a MATE, not by observing actual communication. Ensure you do your on testing before relying on this information!

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