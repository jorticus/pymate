# FLEXnet DC Registers

Address |Description                        | Units / Values                                    | R/W           | MATE Screen 
--------|-----------------------------------|---------------------------------------------------|---------------|-------------
0000    | Device type                       | 0004 = DC                                         |               |
0001    | ??                                | 0000                                              |               |
0002    | FW Rev A (AAA.BBB.CCCC)           | AAA                                               |               |
0003    | FW Rev B                          | BBB                                               |               |
0004    | FW Rev C                          | CCCC                                              |               |
00D5    | State of Charge                   | % 0064 = 100%                                     |               |
00D8    | Aux control voltage/SOC           | ???                                               |               |
~       |                                   |                                                   |               |
0024    | Shunt A Charged                   | ??                                                |               | METER/DC/SHUNT
0026    | Shunt B Charged                   | ??                                                |               | METER/DC/SHUNT
0028    | Shunt C Charged                   | ??                                                |               | METER/DC/SHUNT
002A    | Shunt A Removed                   | ??                                                |               | METER/DC/SHUNT
002C    | Shunt B Removed                   | ??                                                |               | METER/DC/SHUNT
002E    | Shunt C Removed                   | ??                                                |               | METER/DC/SHUNT
003E    | Shunt A Charged                   | ??                                                |               | METER/DC/SHUNT
0040    | Shunt B Charged                   | ??                                                |               | METER/DC/SHUNT
0042    | Shunt C Charged                   | ??                                                |               | METER/DC/SHUNT
0044    | Shunt A Removed                   | ??                                                |               | METER/DC/SHUNT
0046    | Shunt B Removed                   | ??                                                |               | METER/DC/SHUNT
0048    | Shunt C Removed                   | ??                                                |               | METER/DC/SHUNT
~       |                                   |                                                   |               |
0066    | Shunt A Max Charged Amps          | A  2920 = 1052.8A                                 | RESET         | METER/DC/SHUNT
0068    | Shunt A Max Charged kWatts        | kW 1C38 = 72.240kW                                | RESET         | METER/DC/SHUNT
006A    | Shunt B Max Charged Amps          |                                                   | RESET         | METER/DC/SHUNT
006C    | Shunt B Max Charged kWatts        |                                                   | RESET         | METER/DC/SHUNT
006E    | Shunt C Max Charged Amps          |                                                   | RESET         | METER/DC/SHUNT
0070    | Shunt C Max Charged kWatts        |                                                   | RESET         | METER/DC/SHUNT
0072    | Shunt A Max Removed Amps          | A                                                 | RESET         | METER/DC/SHUNT
0074    | Shunt A Max Removed kWatts        |   kW                                              | RESET         | METER/DC/SHUNT
0076    | Shunt B Max Removed Amps          | A                                                 | RESET         | METER/DC/SHUNT
0078    | Shunt B Max Removed kWatts        |                                                   | RESET         | METER/DC/SHUNT
007A    | Shunt C Max Removed Amps          |                                                   | RESET         | METER/DC/SHUNT
007C    | Shunt C Max Removed kWatts        |                                                   | RESET         | METER/DC/SHUNT
~       |                                   |                                                   |               |
0010    | Temp comp'd batt setpoint         | V DC      011F = 28.7 vdc                         |               | STATUS/DC/BATT 
001C    | Lifetime kAh removed              | kAh                                               | RESET = 00FF  | STATUS/DC/BATT    
0058    | Battery min today                 | V DC                                              | RESET*        | STATUS/DC/BATT    
00EC    | RESET Battery min today           | -                                                 | RESET = 00FF  | STATUS/DC/BATT 
005A    | Battery max today                 | V DC     02D2 = 72.2 vdc                          | RESET*        | STATUS/DC/BATT 
00EB    | RESET Battery max today           | -                                                 | RESET = 00FF  | STATUS/DC/BATT 
0062    | Days since charge parameters met  | days /10                                          | RESET*        | STATUS/DC/BATT 
0064    | Total days at 100                 | days                                              | RESET = 0000  | STATUS/DC/BATT     
00D1    | Cycle kWhr charge efficiency      | % (0064 = 100%)                                   |               | STATUS/DC/BATT 
00D7    | Cycle charge factor               | % (0064 = 100%)                                   |               | STATUS/DC/BATT 
00F0    | System battery temperature        | degC (00FE = Not present)                         |               | STATUS/DC/BATT 
~       |                                   |                                                   |               |
0034    | Battery capacity                  | 0 Ah, 0190 = 400Ah, 0208 =  520Ah                 | [INC DEC ±10] | ADV/DC/…  (Setup)
00CA    | Shunt A Mod                       | 0:Enabled<br/>1:Disabled<br/>(Default: Enabled)   | [EN DIS]      | ADV/DC/…  (Setup)
00CB    | Shunt B Mode                      | 0:Enabled<br/>1:Disabled<br/>(Default: Disabled)  | [EN DIS]      | ADV/DC/…  (Setup)
00CC    | Shunt C Mode                      | 0:Enabled<br/>1:Disabled<br/>(Default: Disabled)  | [EN DIS]      | ADV/DC/…  (Setup)
005C    | Return Amps                       | 0.0 A (0050 = 8.0A)                               | [INC DEC ±0.1]| ADV/DC/…  (Setup)
005E    | Battery voltage                   | 00.0 V (011F = 28.7V)                             | [INC DEC ±0.1]| ADV/DC/…  (Setup)
00DA    | Parameters met time               | minutes (0001=1 min)                              | [INC DEC ±1]  | ADV/DC/…  (Setup)
00D4    | Charge factor                     | %  (005E = 94%)                                   | [INC DEC ±1]  | ADV/DC/…  (Setup)
00D8    | Aux Control                       | 0:Off, 1:Auto, 2:On (Default: Off)                | [OFF AUTO ON] | ADV/DC/…  (Setup)
0060    | High volts                        | 00.0 V DC       (008C = 14.0 vdc)                 | [INC DEC ±0.1]| ADV/DC/…  (Setup)
007E    | Low volts                         | 00.0 V DC       (0078 = 12.0 vdc)                 | [INC DEC ±0.1]| ADV/DC/…  (Setup)
00D9    | SOC High                          | %   (Default: 0%)                                 | [INC DEC ±1]  | ADV/DC/…  (Setup)
00DB    | SOC Low                           | %   (Default: 0%)                                 | [INC DEC ±1]  | ADV/DC/…  (Setup)
00E0    | High setpoint delay               | minutes     (0001 = 1 min)                        | [INC DEC ±1]  | ADV/DC/…  (Setup)
00E1    | Low setpoint delay                | minutes     (0001 = 1 min)                        | [INC DEC ±1]  | ADV/DC/…  (Setup)
00D3    | Aux logic invert                  | 0:No**, 1:Yes** (Default: No)                     | [YES:0 NO:1]  | ADV/DC/…  (Setup)

**NOTE**: Do not rely on this information as it was determined by poking values at a MATE, not by observing actual communication. Ensure you do your on testing before relying on this information!

All values are 16-bit signed integers

For rows marked `RESET`, writing to these registers will reset them to 0.
For rows marked `RESET*`, registers are reset by writing to a *different* register.

**Bug: In register `00D3` The YES button sends 0000, which is read back as NO.
