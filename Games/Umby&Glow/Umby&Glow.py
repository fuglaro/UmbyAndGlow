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
# TODO: Remove unused functions
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
Cave -> forest -> air -> rocket -> space -> spaceship ->
    spaceship computer mainframe -> dolphin aquarium ->
    flooded spaceship -> forrest -> cave

'''
##
# Script - the story through the dialog of the characters.
script = [
]

import time
import thumby
from array import array


## Utility Functions ##

##
# Fast bitwise abs
@micropython.viper
def abs(v: int) -> int:
    m = v >> 31
    return (v + m) ^ m

##
# 32 bit deterministic semi-random hash fuction
# Credit: Thomas Wang
@micropython.viper
def ihash(x: uint) -> int:
    x = (x ^ 61) ^ (x >> 16)
    x += (x << 3)
    x ^= (x >> 4)
    x *= 0x27d4eb2d
    return int(x ^ (x >> 15))
##
# (smooth) deterministic semi-random hash.
# For x, this will get two random values,
# one for the nearest interval of 'step' before x,
# and one for the nearest interval of 'step' after x.
# The result will be the interpolation between the two
# random values for where x is positioned along the step.
# @param x: the position to retrieve the interpolated random value.
# @param step: the interval between random samples.
# @param size: the maximum magnitude of the random values.
@micropython.viper
def shash(x: int, step: int, size: int) -> int:
    a = int(ihash(x//step)) % size
    b = int(ihash(x//step + 1)) % size
    return a + (b-a) * (x%step) // step


## Tape Management ##

##
# Scrolling tape with each render layer being a section one after the other.
# Each section is a buffer that cycles (via the tapeScroll positions) as the
# world scrolls horizontally. Each section can scroll independently so
# background layers can move slower than foreground layers.
# Layers each have 1 bit per pixel from top left, descending then wrapping to
# the right.
# The vertical height is 64 pixels and comprises of 2 ints each with 32 bits. 
# Each layer is a layer in the composited render stack.
# Layers from left to right:
# - 0: far background
# - 144: close background
# - 288: close background fill (opaque off pixels)
# - 432: landscape including ground, platforms, and roof
# - 576: landscape fill (opaque off pixels)
tape = array('I', (0 for i in range(0, 72*2*5)))
# The scroll distance of each layer in the tape,
# and then the frame number counter and vertical offset appended on the end.
# The vertical offset (yPos), cannot be different per layer (horizontal
# parallax only).
# [L1, L2, L3, L4, L5, frameCounter, yPos]
tapeScroll = array('i', [0, 0, 0, 0, 0, 0, 0])
# The patterns to feed into each tape section
feed = [None, None, None, None, None]
# Simple cache used across the writing of a single column of the tape.
# Since the tape patterns must be stateless across columns for rewinding, this
# should not store data across columns.
buf = array('i', [0])

# TODO remove unused values from tapeScroll (fill layers)


##
# comp
# Composite all the render layers together and render directly to the display
# buffer, taking into account the scroll position of each render layer, and
# dimming the background layers.
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
        # The magic number here is repeating on and off bits, which is
        # alternated horizontally and in time. Someone say "time crystal".
        dim = int(1431655765) << (ctr+x)%2
        # Compose the first 32 bits vertically.
        p0 = (x+tp0)%72*2
        p1 = (x+tp1)%72*2
        p3 = (x+tp3)%72*2
        a = uint(((tape_[p0] | tape_[p1+144]) & tape_[p1+288] & dim
            | tape_[p3+432]) & tape_[p3+576])
        # Compose the second 32 bits vertically.
        b = uint(((tape_[p0+1] | tape_[p1+145]) & tape_[p1+289] & dim
            | tape_[p3+433]) & tape_[p3+577])
        # Apply the relevant pixels to next vertical column of the display
        # buffer, while also accounting for the vertical offset.
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
            # Update this 32 bit word with the next bit of pattern data
            v |= int(pattern(x, y)) << b
            y+=1
        # write the current 32 bits to tape
        tape_[layer*144 + x%72*2+w] = v

##
# scroll_tape_with_fill
# Similar to scroll_tape but also fills out the fill layer
# with a fill pattern.
@micropython.viper
def scroll_tape_with_fill(pattern, fill_pattern, layer: int, direction: int):
    tape_ = ptr32(tape)
    scroll = ptr32(tapeScroll)
    # Advance the tapeScroll position for the layer
    tapePos = scroll[layer] + direction
    scroll[layer] = tapePos
    # Find the tape position for the column that needs to be filled
    x = tapePos + 72 - (1 if direction == 1 else 0)
    offX = x%72*2
    # Do the top 32 bits, then the bottom 32 bits
    for w in range(0, 2):
        # y will iterate through the vertical tape position, for the 32 bits
        y = w*32
        # v collects the data for the current 32 bits
        v = 0
        # f collects the data for the current 32 bits of the fill layer
        f = 0
        # Loop through each bit in this 32 bit word
        for b in range(0, 32):
            # Update this 32 bit word with the next bit of pattern data
            v |= int(pattern(x, y)) << b
            # And also for the fill pattern
            f |= int(fill_pattern(x, y)) << b
            y+=1
        # write the current 32 bits to tape
        tape_[layer*144 + offX+w] = v
        # same for the fill later
        tape_[(layer+1)*144 + offX+w] = f

##
# offset_vertically
# Shift the view on the tape to a new vertical position, by
# specifying the offset from the top position. This cannot
# exceed the total vertical size of the tape (minus the tape height).
@micropython.viper
def offset_vertically(offset: int):
    ptr32(tapeScroll)[6] = (offset if offset>=0 else 0) if offset<=24 else 24


# TODO: check speed of abs equivelents

##
# PATTERN [none]: empty
@micropython.viper
def pattern_none(x: int, y: int) -> int:
    return 0
##
# PATTERN [fill]: completely filled
@micropython.viper
def pattern_fill(x: int, y: int) -> int:
    return 1
##
# PATTERN [fence]: - basic dotted fences at roof and high floor
@micropython.viper
def pattern_fence(x: int, y: int) -> int:
    return (1 if y<12 else 1 if y>32 else 0) & int(x%10 == 0) & int(y%2 == 0)
##
# PATTERN [room]:- basic flat roof and high floor
@micropython.viper
def pattern_room(x: int, y: int) -> int:
    return 1 if y < 3 else 1 if y > 37 else 0
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
# PATTERN [toothsaw]: TODO use
@micropython.viper
def pattern_toothsaw(x: int, y: int) -> int:
    return int(y > (113111^x+11) % 64 // 2 + 24)

##
# PATTERN [revtoothsaw]: TODO use
@micropython.viper
def pattern_revtoothsaw(x: int, y: int) -> int:
    return int(y > (11313321^x) % 64)

##
# PATTERN [diamondsaw]: TODO use
@micropython.viper
def pattern_diamondsaw(x: int, y: int) -> int:
    return int(y > (32423421^x) % 64)

##
# PATTERN [fallentree]: TODO use
@micropython.viper
def pattern_fallentree(x: int, y: int) -> int:
    return int(y > (32423421^(x+y)) % 64)





##
# PATTERN [cave]: TODO
@micropython.viper
def pattern_cave(x: int, y: int) -> int:
    # buff: [ground-height]
    buff = ptr32(buf)
    if (y == 0):
        buff[0] = int(shash(x,32,48)) + int(shash(x,16,24)) + int(shash(x,4,16))
    return int(y > buff[0])
##
# PATTERN [cave_fill]: TODO
@micropython.viper
def pattern_cave_fill(x: int, y: int) -> int:
    # buff: [ground-height]
    buff = ptr32(buf)
    return int(y < buff[0]+5)

##
# PATTERN [dev]: TODO
@micropython.viper
def pattern_dev(x: int, y: int) -> int:
    buff = ptr32(buf)
    if (y == 0):
        buff[0] = int(shash(x,32,48)) + int(shash(x,16,24)) + int(shash(x,4,16))
    return int(y > buff[0])



## Game Engine ##

##
# Prepare everything for a level of gameplay including
# the starting tape, and the feed patterns for each layer.
def start_level():
    # Fill the tape with the starting area
    for i in range(0, 72):
        scroll_tape(pattern_fence, 1, 1)
        scroll_tape_with_fill(pattern_room, pattern_fill, 3, 1)
    # Set the feed patterns for each layer.
    # (back, mid-back, mid-back-fill, foreground, foreground-fill)
    feed[:] = [pattern_wall, pattern_fence, pattern_room,
        pattern_cave, pattern_cave_fill]
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
    offset_vertically((c // 10) % 24)
    scroll_tape_with_fill(feed[3], feed[4], 3, 1)
    if (c % 2 == 0):
        scroll_tape_with_fill(feed[1], feed[2], 1, 1)
        if (c % 4 == 0):
            scroll_tape(feed[0], 0, 1)
    c += 1


