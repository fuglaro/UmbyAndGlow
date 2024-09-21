import engine_link
ready_comms = engine_link.start


# Read/write buffers (last byte is checksum)
inbuf = bytearray(0 for x in range(160))
outbuf = bytearray(0 for x in range(160))

@micropython.viper
def _prep_checksum():
    chs = 0
    for i in range(159):
        chs += int(outbuf[i])
    outbuf[159] = chs&0xff
@micropython.viper
def _check_checksum() -> int:
    chs = 0
    for i in range(159):
        chs += int(inbuf[i])
    return 1 if int(inbuf[159]) == chs&0xff else 0

send = 2
skips = 0
@micropython.native
def comms():
    """ Attempt to send outbuf and recieve inbuf.
    Only sends if it gets a recieve.
    """
    global send, skips
    skips += 1
    # Ensure the connection is established.
    while not engine_link.connected():
        if not engine_link.is_started():
            engine_link.start()
    # Attempt to exchange data packets.
    res = 0
    # Read a whole packet if available.
    if engine_link.available() >= 160:
        engine_link.read_into(inbuf)
        res = _check_checksum()
        if res:
            send += 1
    # Send entire packet if ready.
    if send:
        _prep_checksum()
        engine_link.send(outbuf)
        skips = 0
        send -= 1
    if skips > 10:
        skips = 0
        engine_link.clear_read()
        engine_link.clear_send()
        if engine_link.is_host():
            send = 2
    return res

