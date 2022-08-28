
## Files and Explanations

### Games/Umby&Glow/Umby&Glow.py

Game loading screen and setup.

Main entry point to the program, this shows a loading screen while the game loads (thanks to Doogle!).

This is also a useful place to place testing code for fast testing and development. Place the following code into this file before the title screen is loaded to perform specific tests.

#### Pattern Testing

View patterns easily for quick iteration of level design.

```python
from patterns import *
from tape import Tape, display_update
tape = Tape()
tape.feed = [pattern_testing_back,
            pattern_none, pattern_fill,
            pattern_testing, pattern_testing_fill]
tape.reset(0)
t = 0
while True:
    t += 1
    tape.scroll_tape(1 if t%4==0 else 0, 1 if t%2==0 else 0, 1)
    tape.offset_vertically(t//10%23)
    tape.comp()
    display_update()
```

#### Comms Testing

For testing 2 player coop comms in the WebIDE emulator, or with 1 device.

```python
@micropython.native
def _comms():
    ### Fakes 2 play comms (relays p1 data, offset horizontally) ###
    inbuf[:] = outbuf[:]
    px = inbuf[0]<<24 | inbuf[1]<<16 | inbuf[2]<<8 | inbuf[3]
    px += 10
    inbuf[0] = px>>24
    inbuf[1] = px>>16
    inbuf[2] = px>>8
    inbuf[3] = px
    return 1
import comms
comms.comms = _comms
```

#### Audio Testing

Sets the audio, plays, then quits

```python
from audio import *
from time import sleep_ms
play(rocket_bang, 40, True)
for i in range(250):
    audio_tick()
    sleep_ms(1000//60)
raise Exception("STOP")
```

#### Script Testing

For scanning for syntax errors in script.txt quickly.

```python
from patterns import *
from monsters import *
with open("/Games/Umby&Glow/script.txt") as fp:
    for ln, line in enumerate(fp):
        if line and line[0] != "#" and line[0] != "\n":
            dist, _, ev_str = line.partition(",")
            try:
                int(dist), eval(ev_str.strip())
            except SyntaxError:
                print(ln+1, line)
                raise
```
