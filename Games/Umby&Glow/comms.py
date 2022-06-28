# Copyright © 2022 John van Leeuwen <jvl@convex.cc>
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

## 2 player network communication ##

from machine import Pin, UART

_rxPin = Pin(1, Pin.IN)
_uart = UART(0, baudrate=115200, rx=_rxPin, tx=Pin(0, Pin.OUT), timeout=0,
    txbuf=164, rxbuf=328)
Pin(2, Pin.OUT).value(1)

# Read and write (and dump) buffers for comms messages.
# Don't use the last byte as it is the checksum.
_echobuf = bytearray(0 for x in range(160))
inbuf = bytearray(0 for x in range(160))
outbuf = bytearray(0 for x in range(160))
_echo = _wait = _uanyc = 0 # Listen counters

@micropython.viper
def _prep_checksum():
    chs = 0
    for i in range(159):
        chs ^= int(outbuf[i])
    outbuf[159] = chs
@micropython.viper
def _check_checksum() -> int:
    chs = 0
    for i in range(159):
        chs ^= int(inbuf[i])
    return 1 if int(inbuf[159]) == chs else 0

@micropython.native
def comms():
    ### Communicate with the other Thumby.
    # Each call might not complete a full message and might instead
    # only recieve some bytes. This will send the inbuf
    # if it is this Thumby's turn to send, otherwise it will receive
    # data into the outbuf. This will only recieve a message after
    # trying to send a message. If the communication channel is not
    # responsive, this will attempt to reattemp sending data once
    # every 60 calls.
    # @returns: True if a complete message was just recieved
    ###
    global _echo, _wait, _uanyc
    res = 0
    # Sending will echo back on the wire (from half duplex) so
    # swallow up the echo since its not from the connected Thumby.
    _echo -= _uart.readinto(_echobuf, _echo) or 0
    if _echo == 0 and _wait > 0:
        # Listen for some of the real response message from the other Thumby
        _wait -= _uart.readinto(memoryview(inbuf)[160-_wait:], _wait) or 0
        # If the message arrives in full and intact, return success
        if not _wait and _check_checksum():
            res = 1
    # Check if it is our turn to send
    if _echo == 0 and _wait == 0 and _rxPin.value:
        # Wipe and junk or half messages
        while _uart.any():
            _uart.readinto(_echobuf)
        # Now send the next message with a checksum
        _prep_checksum()
        _uart.write(outbuf)
        # Get ready to recieve the self-echo then the real response 
        _echo = _wait = 160
    # Check if we are waiting for a message, but the line is empty
    elif _wait != 0 and not _uart.any():
        _uanyc += 1 # Increment counter
        # After listening for nothing 60 times, abandon and send again
        if _uanyc > 60:
            _echo = _wait = _uanyc = 0
    return res

