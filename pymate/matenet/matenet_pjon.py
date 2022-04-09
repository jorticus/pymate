
# pyMATE over PJON interface
# Author: Jared Sanson <jared@jared.geek.nz>
#
# Specifications:
# SFSP v1.0 - https://github.com/gioblu/PJON/blob/master/specification/SFSP-frame-separation-specification-v1.0.md
# TSDL v2.1 - https://github.com/gioblu/PJON/blob/master/src/strategies/ThroughSerial/specification/TSDL-specification-v2.1.md
# PJON v3.1 - https://github.com/gioblu/PJON/blob/master/specification/PJON-protocol-specification-v3.1.md

import logging
from time import sleep, time

from serial import Serial

SFSP_START = 0x95
SFSP_END   = 0xEA
SFSP_ESC   = 0xBB

# [START:8][H:8][I:8][END:8]...[ACK:8]

TSDL_ACK        = 6

RX_IDLE = 0
RX_RECV = 1

ID_BROADCAST = 0

TARGET_DEVICE = 0x0A
TARGET_MATE = 0x0B

class MateNETPJON(object):
    def __init__(self, comport, baud=9600, target=TARGET_DEVICE):
        if isinstance(comport, Serial):
            self.ser = comport
        else:
            self.ser = Serial(comport, baud)
            self.ser.timeout = 1.0
        
        self.device_id = 1
        self.log = logging.getLogger('mate.pjon')
        self.rx_buffer = []
        self.rx_state = RX_IDLE
        self.target = target

    def _build_frame(self, data):
        yield SFSP_START
        for b in data:
            if b in [SFSP_START, SFSP_END, SFSP_ESC]:
                b ^= SFSP_ESC
                yield SFSP_ESC
            yield b
        yield SFSP_END
        
    def send(self, data, target_device_id=0):
        """
        Send a packet to PJON bus
        """
        data = [self.target] + [ord(c) for c in data] # TODO: Hacky

        # NOTE: We are using a very watered down version of the PJON spec
        # since this is intended to be used as a 1:1 communication over a USB serial bus.

        header_len = 5
        total_len = len(data) + header_len
        use_crc32 = ((len(data) + header_len) > 15)

        header = 0x02 # PJON_TX_INFO_BIT
        if use_crc32:
            header |= 0b00100000 # PJON_CRC_BIT
            total_len += 4
        else:
            total_len += 1

        # Prepare header
        buffer = []
        buffer.append(target_device_id)
        buffer.append(header)
        buffer.append(total_len)
        crc_h = self._crc8(buffer)
        buffer.append(crc_h)
        buffer.append(self.device_id)  # PJON_TX_INFO_BIT in header must be set

        # Add payload
        buffer += list(data)

        # Compute CRC(Header + Payload)
        if use_crc32:
            # If packet > 15 bytes then we must use a 32-bit CRC
            crc_p = self._crc32(buffer)
            buffer.append((crc_p >> 24) & 0xFF)
            buffer.append((crc_p >> 16) & 0xFF)
            buffer.append((crc_p >> 8) & 0xFF)
            buffer.append((crc_p) & 0xFF)
        else:
            crc_p = self._crc8(buffer)
            buffer.append(crc_p)

        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug('TX: %s', (' '.join('%.2x' % c for c in buffer)))
        
        # Escape & Frame data
        buffer = list(self._build_frame(buffer))

        self.ser.write(buffer)

    def _crc8(self, data):
        crc = 0
        for b in data:
            if b < 0: b += 256
            for i in range(8):
                odd = ((b ^ crc) & 1) == 1
                crc >>= 1
                b   >>= 1
                if odd: crc ^= 0x97
        return crc

    def _crc32(self, data):
        """
        See PJON\\src\\utils\\crc\\PJON_CRC32.h
        """
        crc = 0xFFFFFFFF
        for b in data:
            crc ^= (b & 0xFF)
            for i in range(8):
                odd = crc & 1
                crc >>= 1
                if odd:
                    crc ^= 0xEDB88320
        return crc ^ 0xFFFFFFFF

    def _recv_frame(self, timeout=1.0):
        """
        Receive an escaped frame from PJON bus
        :param timeout: seconds to wait until returning, 0 to return immediately, None to block indefinitely
        :return: bytes if packet received, None if timeout
        """
        # Example RX packet:
        # 149 0 2 11 226 44 72 69 76 76 79 69 234
        buffer = []
        escape_next = False
        t_start = time()

        self.ser.timeout = 0.01
        self.rx_state = RX_IDLE

        while (time() - t_start < timeout):
            if self.rx_state == RX_IDLE:
                # Locate start of frame
                data = self.ser.read(1)
                if data:
                    b = ord(data[0])
                    if b == SFSP_START:
                        self.rx_state = RX_RECV
                        self.log.debug('RX START')
                        continue

            elif self.rx_state == RX_RECV:
                # Read until SFSP_END encountered
                data = self.ser.read()
                if data:
                    for c in data:
                        b = ord(c)
                        if b == SFSP_END:
                            return buffer  # Complete frame received!

                        else:
                            # Unescape
                            if b == SFSP_ESC:
                                escape_next = True
                                continue

                            elif b == SFSP_START:
                                self.log.debug('RX UNEXPECTED START')
                                self.rx_state = RX_IDLE
                                buffer = []
                                escape_next = False
                                continue

                            if escape_next:
                                b ^= SFSP_ESC
                                escape_next = False

                            buffer.append(b)

        self.log.info('RX TIMEOUT')
        return None

    def recv(self, expected_len=None, timeout=1.0):
        """
        Receive a packet from PJON bus
        :param timeout: seconds to wait until returning, 0 to return immediately, None to block indefinitely
        :return: bytes if packet received, None if timeout
        """
        data = self._recv_frame(timeout)
        if data:
            if self.log.isEnabledFor(logging.DEBUG):
                self.log.debug('RX: %s', (' '.join('%.2x' % b for b in data)))

            if len(data) < 5:
                raise RuntimeError('PJON error: Not enough bytes')

            # [ID:8][Header:8][Length:8][CRC:8][Data...][CRC:8]

            i = 0

            device_id  = data[i]; i += 1
            header     = data[i]; i += 1
            packet_len = data[i]; i += 1

            if device_id != ID_BROADCAST and device_id != self.device_id:
                self.log.debug('PJON: Ignoring packet for ID:0x%.2x', device_id)
                return None  # Not addressed to us

            if packet_len < 4:
                raise RuntimeError('PJON error: Invalid length')
            if packet_len > len(data):
                raise RuntimeError('PJON error: Not enough bytes')

            use_crc32 = (header & 0b00100000)

            # Validate header CRC
            header_crc_actual = self._crc8(data[0:i])
            header_crc        = data[i]; i += 1
            if header_crc != header_crc_actual:
                raise RuntimeError('PJON error: Bad header CRC (%.2x != %.2x)' % (header_crc, header_crc_actual))
            
            # Header bits change how the packet is parsed
            if header & 0b00000001:
                raise RuntimeError('PJON error: Shared mode not supported')
            if header & 0b00000010:
                tx_id = data[i]; i += 1
            if header & 0b00000100:
                raise RuntimeError('PJON error: ACK requested but not supported')
            if header & 0b00010000:
                raise RuntimeError('PJON error: Network services not supported')
            if header & 0b01000000:
                raise RuntimeError('PJON error: Extended length (>=200 bytes) not supported')
            if header & 0b10000000:
                raise RuntimeError('PJON error: Packet identification not supported')

            payload     = data[i:packet_len-1];

            # Validate CRC(Header + Payload)
            if use_crc32:
                payload_crc_actual = self._crc32(data[0:-4])
                payload_crc        = (data[-4]<<24) | (data[-3]<<16) | (data[-2]<<8) | data[-1]
                if payload_crc != payload_crc_actual:
                    raise RuntimeError('PJON error: Bad CRC32 (%.8x != %.8x)' % (payload_crc, payload_crc_actual))
            else:
                payload_crc_actual = self._crc8(data[0:-1])
                payload_crc        = data[packet_len-1]
                if payload_crc != payload_crc_actual:
                    raise RuntimeError('PJON error: Bad CRC8 (%.2x != %.2x)' % (payload_crc, payload_crc_actual))

            if self.log.isEnabledFor(logging.DEBUG):
                self.log.debug('RX: [I:%.2X, H:%.2X, Len:%d, Data:[%s]]',
                    device_id,
                    header,
                    packet_len,
                    (' '.join('%.2x' % b for b in payload))
                )

            if len(payload) == 1:
                raise RuntimeError("PJON error: Error returned from controller: %.2x" % (payload[0]))

            # TODO: Validate payload length against expected_len

            return ''.join(chr(c) for c in payload) # TODO: Hacky

if __name__ == "__main__":
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    port = MateNETPJON('COM6')
    port.log.setLevel(logging.DEBUG)
    port.log.addHandler(ch)
    while True:
        data = port._recv()
        if data:
            port.log.debug('RX: %s', (' '.join('%.2x' % ord(b) for b in data)))
            port.log.debug('    %s', (''.join(data)))
