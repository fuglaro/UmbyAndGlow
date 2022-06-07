# Copyright © 2022 John van Leeuwen <jvl@convex.cc>
'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

# TODO: Make level 1 patterns
# TODO: Make basic game dynamics (Umby)
# TODO: Extend game dynamics (Glow)
# TODO: Make 2 player
# TODO: Write script / story
# TODO: Extend game dynamics and add 8 more levels
# TODO: Full game description and overview (for arcade_description.txt file)
# TODO: Make demo video
# TODO: Submit to https://github.com/TinyCircuits/TinyCircuits-Thumby-Games


''' # TODO turn story into script and delete.

1 - player can switch characters (hold both buttons)
2 - 2 players connect if devices have different characters

Umby and Glow save their cave.

1.1) Umby, Glow in cave, with monsters and traps being about.
1.2) Umby and Glow find monsters have infiltrated their cave.
1.3) They suspect it is Lung.
1.4) They decide to find out where they have come from.
1.5) They leave their cave.

Suspect bad worm
Follow monsters to alien spaceship
Find Lung held hostage
Lung gives info as sacrifice
Flood spaceship mainframe
Go back home
Cave -> forest -> air -> rocket -> space -> spaceship -> spaceship computer mainframe -> dolphin aquarium -> flooded spaceship -> forrest -> cave

'''

##
# Script of the two worms.
# Umby, Glow
script = [
(,)    
]

import time
import thumby
from array import array

##
# Fast bitwise abs
@micropython.viper
def abs(v: int) -> int:
    m = v >> 31
    return (v + m) ^ m

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
# and then the frame number counter and vertical offset appended on the end.
# The vertical offset (yPos), cannot be different per layer (horizontal parallax only).
# [L1, L2, L3, L4, L5, frameCounter, yPos]
tapeScroll = array('i', [0, 0, 0, 0, 0, 0, 0])
# The patterns to feed into each tape section
feed = [None, None, None, None, None]

##
# comp
# Composite all the render layers together and render directly to the display buffer,
# taking into account the scroll position of each render layer, and dimming the
# background layers.
@micropython.viper
def comp():
    tape_ = ptr32(tape)
    scroll = ptr32(tapeScroll)
    frame = ptr8(thumby.display.display.buffer)
    # Get the scoll position of each tape section (render layer)
    tp0 = scroll[0]
    tp1 = scroll[1]
    tp3 = scroll[3]
    # Obtain and increase the frame counter
    scroll[5] += 1
    ctr = scroll[5]
    yPos = scroll[6]
    # Loop through each column of pixels
    for x in range(0, 72):
        # Create a modifier for dimming background layer pixels.
        # The magic number here is repeating on and off bits, which is alternated
        # horizontally and in time. Someone say "time crystal".
        dim = int(1431655765) << (ctr+x)%2
        # Compose the first 32 bits vertically.
        a = uint((tape_[(x+tp0)%72*2] & dim)
            | (tape_[(x+tp1)%72*2+144] & dim)
            | tape_[(x+tp3)%72*2+432])
        # Compose the second 32 bits vertically.
        b = uint((tape_[(x+tp0)%72*2+1] & dim)
            | (tape_[(x+tp1)%72*2+144+1] & dim)
            | tape_[(x+tp3)%72*2+432+1])
        # Apply the relevant pixels to next vertical column of the display buffer,
        # while also accounting for the vertical offset.
        frame[x] = a >> yPos
        frame[72+x] = (a >> 8 >> yPos) | (b << (32 - yPos) >> 8)
        frame[144+x] = (a >> 16 >> yPos) | (b << (32 - yPos) >> 16)
        frame[216+x] = (a >> 24 >> yPos) | (b << (32 - yPos) >> 24)
        frame[288+x] = (b >> yPos)

##
# scroll_tape
# Scroll the tape one pixel forwards, or backwards for a specified layer.
# Updates the tape scroll position of that layer.
# Fills in the new column with pattern data from a specified
# pattern function. Since this is a rotating buffer, this writes
# over the column that has been scrolled offscreen.
# @param pattern: a function, returning fill data, given x and y paramaters.
# @param layer: the layer to scroll and write to.
# @param direction: -1 -> rewind backwards, 1 -> extend forwrds.
@micropython.viper
def scroll_tape(pattern, layer: int, direction: int):
    tape_ = ptr32(tape)
    scroll = ptr32(tapeScroll)
    # Advance the tapeScroll position for the layer
    tapePos = scroll[layer] + direction
    scroll[layer] = tapePos
    # Find the tape position for the column that needs to be filled
    x = tapePos + 72 - (1 if direction == 1 else 0)
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
        tape_[layer*144 + x%72*2+w] = v

##
# offset_vertically
# Shift the view on the tape to a new vertical position, by
# specifying the offset from the top position. This cannot
# exceed the total vertical size of the tape (minus the tape height).
@micropython.viper
def offset_vertically(offset: int):
    ptr32(tapeScroll)[6] = (offset if offset >= 0 else 0) if offset <= 24 else 24

##
# PATTERN [none]: empty
@micropython.viper
def pattern_none(x: int, y: int) -> int:
    return 0
##
# PATTERN [fence]: - basic dotted fences at roof and high floor
@micropython.viper
def pattern_fence(x: int, y: int) -> int:
    return int(int(abs(y-19)) > 19 - 12) & int(x%10 == 0) & int(y%2 == 0)
##
# PATTERN [room]:- basic flat roof and high floor
@micropython.viper
def pattern_room(x: int, y: int) -> int:
    return int(int(abs(y-19)) > 19 - 3)
##
# PATTERN [test]: long slope plus walls
@micropython.viper
def pattern_test(x: int, y: int) -> int:
    return int(x%120 == y*3) | (int(x%12 == 0) & int(y%2 == 0))
##
# PATTERN [wall]: dotted vertical lines repeating
@micropython.viper
def pattern_wall(x: int, y: int) -> int:
    return int(x%16 == 0) & int(y%3 == 0)


##
# Prepare everything for a level of gameplay including
# the starting tape, and the feed patterns for each layer.
def start_level():
    # Fill the tape with the starting area
    for i in range(0, 72):
        scroll_tape(pattern_fence, 1, 1)
        scroll_tape(pattern_room, 3, 1)
    # Set the feed patterns for each layer.
    feed[:] = [pattern_none, pattern_none, None, pattern_test, None]
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
    comp()
    # Flush to the display, waiting on the next frame interval
    thumby.display.update()


    # TESTING: infinitely scroll the tape
    offset_vertically((c // 10)%24)
    scroll_tape(feed[3], 3, 1)
    if (c % 2 == 0):
        scroll_tape(feed[1], 1, 1)
        if (c % 4 == 0):
            scroll_tape(feed[0], 0, 1)
    c += 1


