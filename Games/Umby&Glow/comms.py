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

