# Setup #

1. Install Wireshark

2. Copy dissector.lua to `%APPDATA%\Wireshark\plugins`
   (Note: CTRL+SHIFT+L to re-load plugins when Wireshark is running)

3. Launch Wireshark and add the custom user protocol:
    1. Edit -> Preferences
    2. Protocols -> DLT_USER, Edit Encapsulations Table
    3. Add (+): `User 0 (DLT = 147)`, Payload protocol: `matenet`
    (https://wiki.wireshark.org/HowToDissectAnything)

4. Install Python 3.x + prerequisites:
   - pySerial
   - pyWin32

5. Flash an Arduino Mega 2560 with the Sniffer.ino sketch.

```
[MATE] --------\   /-------- [MX/FX/DC]
               |   |
            [ Arduino ]
                 |       
            [ Tap.py ]
                 |
           [ Wireshark ]
```

# Usage #

1. Connect the sniffer tap circuit to the Arduino Mega, Outback MATE, and Outback Device under test.

2. Run:
   `python -m pymate.packet_capture.wireshark_tap COM1`

3. The script will print the name of the PCAP pipe, and automatically launch Wireshark.
   Wireshark should connect to the named pipe and the Tap script should print
   `Serial port opened, listening for MateNET data...`

You can manually launch wireshark with the following command-line:
`Wireshark.exe -i\\.\pipe\wireshark-mate -k`
Or add the named pipe under Capture -> Options -> Input -> Manage Interfaces -> Pipes

When capturing packets in Wireshark, you can filter out uninteresting packets.
For example, `matenet.cmd != 4` will filter out all STATUS packets (both TX & RX)

# PCAPNG Anaylsis #

Once you've captured some traffic and saved it to a PCAPNG file, you can open it back up for analysis
with the custom mate dissector:

Wireshark.exe <capture.pcapng> -X lua_script:.\mate_dissector.lua

