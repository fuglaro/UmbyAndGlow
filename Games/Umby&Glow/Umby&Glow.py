# Copyright © 2022 John van Leeuwen <jvl@convex.cc>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of 
# this software and associated documentation files (the “Software”), to deal in 
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


# TODO: Full gave description and overview.


import time
import thumby
from array import array

##
# Scrolling tape with each render layer being a section one after the other.
# Each section is a buffer that cycles (via the tapeScroll positions) as the world
# scrolls horizontally. Each section can scroll independently so background layers can
# move slower than foreground layers.
# Layers each have 1 bit per pixel from top left, descending then wrapping to the right.
# The vertical height is 64 pixels and comprises of 2 ints each with 32 bits. 
# Each layer is a layer in the composited render stack.
# Layers from left to right:
# - 0: far background
# - 144: close background
# - 288: close background fill (opaque off pixels)
# - 432: landscape including ground, platforms, and roof
# - 720: landscape fill (opaque off pixels)
tape = array('I', (0 for i in range(0, 72*2*5)))
# The scroll distance of each layer in the tape,
# and then the frame number counter appended on the end.
# [L1, L2, L3, L4, L5, frameCounter]
tapeScroll = array('i', [0, 0, 0, 0, 0, 0])
# The patterns to feed into each tape section
feed = [None, None, None, None, None]

##
# Composite all the render layers together and render directly to the display buffer,
# taking into account the scroll position of each render layer, and dimming the
# background layers.
@micropython.viper
def comp(tape: ptr32, tapeScroll: ptr32):
    frame = ptr8(thumby.display.display.buffer)
    # Get the scoll position of each tape section (render layer)
    tp0 = tapeScroll[0]
    tp1 = tapeScroll[1]
    tp3 = tapeScroll[3]
    # Obtain and increase the frame counter
    tapeScroll[5] += 1
    ctr = tapeScroll[5]
    # Loop through each column of pixels
    for x in range(0, 72):
        # Create a modifier for dimming background layer pixels.
        # The magic number here is repeating on and off bits, which is alternated
        # horizontally and in time. Someone say "time crystal".
        dim = int(1431655765) << (ctr+x)%2
        # Compose the first 32 bits vertically.
        a = ((tape[(x+tp0)%72*2] & dim)
            | (tape[(x+tp1)%72*2+144] & dim)
            | tape[(x+tp3)%72*2+432])
        # Compose the second 32 bits vertically.
        b = ((tape[(x+tp0)%72*2+1] & dim)
            | (tape[(x+tp1)%72*2+144+1] & dim)
            | tape[(x+tp3)%72*2+432+1])
        # Apply the relevant pixels to next vertical column of the display buffer
        frame[x] = a
        frame[72+x] = a >> 8
        frame[144+x] = a >> 16
        frame[216+x] = a >> 24
        frame[288+x] = b

##
# Scroll the tape one pixel to the right for a specified layer.
# Updates the tape scroll position of that layer.
# Fills in the new column with pattern data from a specified
# pattern function. Since this is a rotating buffer, this writes
# over the column that has been scrolled offscreen.
# @param pattern: a function, returning fill data, given x and y paramaters.
# @param layer: the layer to scroll and write to.
@micropython.viper
def extend_tape(pattern, tape: ptr32, tapeScroll: ptr32, layer: int):
    # Advance the tapeScroll position for the layer
    tapePos = tapeScroll[layer] + 1
    tapeScroll[layer] = tapePos
    # Find the tape position for the column that needs to be filled
    x = tapePos + 72 - 1
    # Do the top 32 bits, then the bottom 32 bits
    for w in range(0, 2):
        # y will iterate through the vertical tape position, for the 32 bits
        y = w*32
        # v collects the data for the current 32 bits
        v = 0
        # Loop through each bit in this 32 bit word
        for b in range(0, 32):
            # Update this 32 bit word with the next bit of fill data from the pattern
            v |= int(pattern(x, y)) << b
            y+=1
        # write the current 32 bits to tape
        tape[layer*144 + x%72*2+w] = v





# TODO rewind_tape (change extend_tape to scroll tape, and add direction argument)





##
# Fast bitwise abs
@micropython.viper
def abs(v: int) -> int:
    m = v >> 31
    return (v + m) ^ m

##
# PATTERN [wall]: dotted vertical lines repeating
@micropython.viper
def pattern_wall(x: int, y: int) -> int:
    return int(x%16 == 0) & int(y%3 == 0)
##
# PATTERN [room]:- basic flat roof and high floor
@micropython.viper
def pattern_room(x: int, y: int) -> int:
    return int(int(abs(y-19)) > 19 - 3)
##
# PATTERN [fence]: - basic dotted fences at roof and high floor
@micropython.viper
def pattern_fence(x: int, y: int) -> int:
    return int(int(abs(y-19)) > 19 - 12) & int(x%10 == 0) & int(y%2 == 0)
##
# PATTERN [test]: long slope plus walls
@micropython.viper
def pattern_test(x: int, y: int) -> int:
    return int(x%120 == y*3) | (int(x%12 == 0) & int(y%3 == 0))


##
# Prepare everything for a level of gameplay including
# the starting tape, and the feed patterns for each layer.
def start_level():
    # Fill the tape with the starting area
    for i in range(0, 72):
        extend_tape(pattern_fence, memoryview(tape), tapeScroll, 1)
        extend_tape(pattern_room, memoryview(tape), tapeScroll, 3)
    # Set the feed patterns for each layer.
    feed[:] = [pattern_wall, pattern_fence, None, pattern_room, None]
start_level()


# FPS
thumby.display.setFPS(2400) # TESTING: for speed profiling
#thumby.display.setFPS(120) # Intended game speed

# Main gameplay loop
c = 0;
profiler = time.ticks_ms()
while(1):
    # Speed profiling
    if (c % 60 == 0):
        print(time.ticks_ms() - profiler)
        profiler = time.ticks_ms()

    # Update the display buffer new frame data
    comp(tape, tapeScroll)
    # Flush to the display, waiting on the next frame interval
    thumby.display.update()


    # TESTING: infinitely scroll the tape
    extend_tape(feed[3], memoryview(tape), tapeScroll, 3)
    if (c % 2 == 0):
        extend_tape(feed[1], memoryview(tape), tapeScroll, 1)
        if (c % 4 == 0):
            extend_tape(feed[0], memoryview(tape), tapeScroll, 0)
    c += 1


