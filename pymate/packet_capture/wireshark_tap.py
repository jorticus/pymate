#
# Utility library for piping protocol data to wireshark
#
# Usage:
# python -m pymate.packet_capture.wireshark_tap COMxx
#
# NOTE: Currently only supported on Windows.
# Linux support should be possible with modifications to the named pipe interface.
#
# https://wiki.wireshark.org/CaptureSetup/Pipes
#

from time import sleep
from serial import Serial  # pySerial
from datetime import datetime
import os
import sys
import time
import win32pipe, win32file, win32event, pywintypes, winerror # pywin32
import subprocess
import struct
import errno

LUA_SCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 
    'mate_dissector.lua'
)

# TODO: Don't hard-code this...
WIRESHARK_PATH = r'C:\Program Files\Wireshark\Wireshark.exe'

class WiresharkTap(object):
    WIRESHARK_PIPENAME = r'\\.\pipe\wireshark-mate'
    WIRESHARK_DLT  = 147 # DLT_USER0

    FRAME_TX = 0x0A
    FRAME_RX = 0x0B

    def __init__(self):
        self._pipe = None
        self._prev_bus = None
        self._prev_pkt = None

        self.combine_frames = True

    def open(self, timeout_ms=30000):
        """
        Start the wireshark pipe
        """
        # Create named pipe
        self._pipe = self._create_pipe(self.WIRESHARK_PIPENAME)

        # Connect pipe
        print(f"PCAP pipe created: {self.WIRESHARK_PIPENAME}")
        print("Waiting for connection...")
        self._connect_pipe(timeout_ms)
        print("Pipe opened")

        self._send_wireshark_header()

    def close(self):
        """
        Close the wireshark pipe
        """
        if self._pipe is not None:
            self._pipe.close()
            self._pipe = None

    @staticmethod
    def launch_wireshark(sideload_dissector=True, path=WIRESHARK_PATH):
        if sideload_dissector:
            if not os.path.exists(LUA_SCRIPT_PATH):
                raise Exception('mate_dissector.lua not found: ' + LUA_SCRIPT_PATH)

        #open Wireshark, configure pipe interface and start capture (not mandatory, you can also do this manually)
        wireshark_cmd=[
            path, 
            '-i'+WiresharkTap.WIRESHARK_PIPENAME,
            '-k',
            '-o','capture.no_interface_load:TRUE'
        ]
        if sideload_dissector:
            wireshark_cmd += ['-X','lua_script:'+LUA_SCRIPT_PATH]
        proc=subprocess.Popen(wireshark_cmd)

    @staticmethod
    def _create_pipe(name):
        # WINDOWS:
        return win32pipe.CreateNamedPipe(
            name,
            win32pipe.PIPE_ACCESS_OUTBOUND | win32file.FILE_FLAG_OVERLAPPED,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
            1, 65536, 65536,
            300,
            None)
        # UNIX:
        # try:
        #     return os.mkfifo(name);
        # except FileExistsError:
        #     pass
        # except:
        #     raise

    def _connect_pipe(self, timeoutMillisec = 1000):
        # WINDOWS:
        overlapped = pywintypes.OVERLAPPED()
        overlapped.hEvent = win32event.CreateEvent(None, 0, 0, None)
        rc = win32pipe.ConnectNamedPipe(self._pipe, overlapped)
        if rc == winerror.ERROR_PIPE_CONNECTED:
            win32event.SetEvent(overlapped.hEvent)
        rc = win32event.WaitForSingleObject(overlapped.hEvent, timeoutMillisec)
        overlapped = None
        if rc != win32event.WAIT_OBJECT_0:
            raise TimeoutError("Timeout while waiting for pipe to connect")
        # UNIX:
        #self._pipe.open()

    def _write_pipe(self, buf):
        try:
            # WINDOWS:
            win32file.WriteFile(self._pipe, bytes(buf))
            # UNIX:
            #self._pipe.write(buf)
        except OSError as e:
            # SIGPIPE indicates the fifo was closed
            if e.errno == errno.SIGPIPE:
                return False
        return True

    def _send_wireshark_header(self):
        # Send PCAP header
        buf = struct.pack("=IHHiIII",
            0xa1b2c3d4,   # magic number
            2,            # major version number
            4,            # minor version number
            0,            # GMT to local correction
            0,            # accuracy of timestamps
            65535,        # max length of captured packets, in octets
            self.WIRESHARK_DLT, # data link type (DLT)
        )
        if not self._write_pipe(buf):
            raise Exception('Could not write to wireshark pipe')
        
    def send_frame(self, bus, data):
        # send pcap packet through the pipe
        now = datetime.now()
        timestamp = int(time.mktime(now.timetuple()))
        pcap_header = struct.pack("=iiiiB",
            timestamp,        # timestamp seconds
            now.microsecond,  # timestamp microseconds
            len(data)+1,        # number of octets of packet saved in file
            len(data)+1,        # actual length of packet
            bus
        )
        if not self._write_pipe(pcap_header + bytes(data)):
            return
        
    def send_combined_frames(self, busa, busb):
        if not busa: busa = []
        if not busb: busb = []
        
        data = struct.pack("=BBB", 0x0F, len(busa), len(busb))
        data += bytes(busa)
        data += bytes(busb)

        # send pcap packet through the pipe
        now = datetime.now()
        timestamp = int(time.mktime(now.timetuple()))
        pcap_header = struct.pack("=iiii",
            timestamp,        # timestamp seconds
            now.microsecond,  # timestamp microseconds
            len(data),        # number of octets of packet saved in file
            len(data),        # actual length of packet
        )
        if not self._write_pipe(pcap_header + bytes(data)):
            return

    def capture_tx(self, packet):
        if not self.combine_frames:
            self.send_frame(0x0A, packet)
        else:
            if (self._prev_bus == 0x0A) and (self._prev_pkt is not None):
                # Previous frame was from the same bus, better
                # send this to wireshark even though it has 
                # no corresponding frame from bus B
                self.send_frame(0x0A, self._prev_pkt)
            
            self._prev_bus = 0x0A
            self._prev_pkt = packet

    def capture_rx(self, packet):
        if not self.combine_frames:
            self.send_frame(0x0B, packet)
        else:
            # Combine packet from A & B
            self.send_combined_frames(self._prev_pkt, packet)

            self._prev_pkt = None
            self._prev_bus = 0x0B

    def capture(self, packet_tx, packet_rx):
        self.send_combined_frames(packet_tx, packet_rx)

def main():
    """
    Demo wireshark tap program to be used in conjunction with 
    uMATE/examples/Sniffer/Sniffer.ino
    """
    if len(sys.argv) < 2:
        print("Usage:")
        print(os.path.basename(sys.argv[0]) + " COM1")
        exit(1)

    COM_PORT = sys.argv[1]
    COM_BAUD = 115200

    BUS_A = 'A' 
    BUS_B = 'B'

    SIDELOAD_DISSECTOR = True

    END_OF_PACKET_TIMEOUT = 0.02 # seconds
    PIPE_CONNECT_TIMEOUT = 30000 # millisec

    s = Serial(COM_PORT, COM_BAUD)
    s.timeout = 1.0 # seconds
    try:

        tap = WiresharkTap()
        try:
            tap.launch_wireshark(SIDELOAD_DISSECTOR)
            tap.open(PIPE_CONNECT_TIMEOUT)

            print("Serial port opened, listening for MateNET data...")
            
            prev_bus = None
            prev_packet = None

            while True:
                s.timeout = END_OF_PACKET_TIMEOUT
                try:
                    ln = s.readline()
                    if ln:
                        ln = ln.decode('ascii', 'ignore').strip()
                    if ln and ':' in ln:
                        print(ln)
                        bus, rest = ln.split(': ')
                        payload = [int(h, 16) for h in rest.split(' ')]

                        data = bytes([])

                        if len(payload) > 2:
                            if (payload[0] & 0x100) == 0:
                                print("Invalid frame: bit9 not set!")
                                continue
                            if any([b & 0x100 for b in payload[1:]]):
                                print("Invalid frame: bit9 set in middle of frame!")
                                continue

                        for b in payload:
                            # Discard 9th bit before encoding PCAP
                            data += bytes([b & 0x0FF])

                        if bus == 'A':
                            tap.capture_tx(data)
                        elif bus == 'B':
                            tap.capture_rx(data)

                except ValueError as e:
                    raise
                    continue

                sleep(0.001)

        finally:
            tap.close()
    finally:
        s.close()

if __name__ == "__main__":
    main()