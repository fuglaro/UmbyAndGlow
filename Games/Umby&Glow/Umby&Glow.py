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

@micropython.viper
def abs(v: int) -> int:
    """ Fast bitwise abs"""
    m = v >> 31
    return (v + m) ^ m

@micropython.viper
def ihash(x: uint) -> int:
    """ 32 bit deterministic semi-random hash fuction
    Credit: Thomas Wang
    """
    x = (x ^ 61) ^ (x >> 16)
    x += (x << 3)
    x ^= (x >> 4)
    x *= 0x27d4eb2d
    return int(x ^ (x >> 15))

@micropython.viper
def shash(x: int, step: int, size: int) -> int:
    """ (smooth) deterministic semi-random hash.
    For x, this will get two random values, one for the nearest
    interval of 'step' before x, and one for the nearest interval
    of 'step' after x. The result will be the interpolation between
    the two random values for where x is positioned along the step.
    @param x: the position to retrieve the interpolated random value.
    @param step: the interval between random samples.
    @param size: the maximum magnitude of the random values.
    """
    a = int(ihash(x//step)) % size
    b = int(ihash(x//step + 1)) % size
    return a + (b-a) * (x%step) // step


## Tape Management ##

class Tape:
    """
    Scrolling tape with a fore, mid, and background layer.
    This represents the level of the ground but doesn't include actors.
    The foreground is the parts of the level that are interactive with
    actors such as the ground, roof, and platforms.
    Mid and background layers are purely decorative.
    Each layer can be scrolled intependently and then composited onto
    display buffer.
    Each layer is created by providing deterministic functions that
    draw the pixels from x and y coordinates. Its really just an elaborate
    graph plotter - a scientific calculator turned console!
    The tape size is 64 pixels high, with an infinite length, but only
    72 pixels wide buffered.
    This is intended for the 72x40 pixel view. The view can be moved
    up and down but when it moves forewards and backwards, the buffer
    is cycled backwards and forewards. This means that the tape
    can be modified (such as for explosion damage) for the 64 pixels high,
    and 72 pixels wide, but when the tape is rolled forewards, and backwards,
    the columns that go offscreen are reset.
    """
    # Scrolling tape with each render layer being a section one after the other.
    # Each section is a buffer that cycles (via the tapeScroll positions) as the
    # world scrolls horizontally. Each section can scroll independently so
    # background layers can move slower than foreground layers.
    # Layers each have 1 bit per pixel from top left, descending then wrapping
    # to the right.
    # The vertical height is 64 pixels and comprises of 2 ints each with 32 bits. 
    # Each layer is a layer in the composited render stack.
    # Layers from left to right:
    # - 0: far background
    # - 144: close background
    # - 288: close background fill (opaque off pixels)
    # - 432: landscape including ground, platforms, and roof
    # - 576: landscape fill (opaque off pixels)
    _tape = array('I', (0 for i in range(72*2*5)))
    # The scroll distance of each layer in the tape,
    # and then the frame number counter and vertical offset appended on the end.
    # The vertical offset (yPos), cannot be different per layer (horizontal
    # parallax only).
    # [backPos, midPos, frameCounter, forePos, yPos]
    _tapeScroll = array('i', [0, 0, 0, 0, 0, 0, 0])

    # The patterns to feed into each tape section
    feed = [None, None, None, None, None]
    
    @micropython.viper
    def comp(self):
        """ Composite all the render layers together and render directly to
        the display buffer, taking into account the scroll position of each
        render layer, and dimming the background layers.
        """
        tape = ptr32(self._tape)
        scroll = ptr32(self._tapeScroll)
        frame = ptr8(thumby.display.display.buffer)
        # Obtain and increase the frame counter
        scroll[2] += 1 # Counter
        yPos = scroll[4]
        # Loop through each column of pixels
        for x in range(72):
            # Create a modifier for dimming background layer pixels.
            # The magic number here is repeating on and off bits, which is
            # alternated horizontally and in time. Someone say "time crystal".
            dim = int(1431655765) << (scroll[2]+x)%2
            # Compose the first 32 bits vertically.
            p0 = (x+scroll[0])%72*2
            p1 = (x+scroll[1])%72*2
            p3 = (x+scroll[3])%72*2
            a = uint(((tape[p0] | tape[p1+144]) & tape[p1+288] & dim
                | tape[p3+432]) & tape[p3+576])
            # Compose the second 32 bits vertically.
            b = uint(((tape[p0+1] | tape[p1+145]) & tape[p1+289] & dim
                | tape[p3+433]) & tape[p3+577])
            # Apply the relevant pixels to next vertical column of the display
            # buffer, while also accounting for the vertical offset.
            frame[x] = a >> yPos
            frame[72+x] = (a >> 8 >> yPos) | (b << (32 - yPos) >> 8)
            frame[144+x] = (a >> 16 >> yPos) | (b << (32 - yPos) >> 16)
            frame[216+x] = (a >> 24 >> yPos) | (b << (32 - yPos) >> 24)
            frame[288+x] = (b >> yPos)
    
    @micropython.viper
    def scroll_tape(self, back_move: int, mid_move: int, fore_move: int):
        """ Scroll the tape one pixel forwards, or backwards for each layer.
        Updates the tape scroll position of that layer.
        Fills in the new column with pattern data from the relevant
        pattern functions. Since this is a rotating buffer, this writes
        over the column that has been scrolled offscreen.
        Each layer can be moved in the following directions:
            -1 -> rewind layer backwards,
            0 -> leave layer unmoved,
            1 -> roll layer forwards
        @param back_move: Movement of the background layer
        @param mid_move: Movement of the midground layer (with fill)
        @param fore_move: Movement of the foreground layer (with fill)
        """
        tape = ptr32(self._tape)
        scroll = ptr32(self._tapeScroll)
        for i in range(3):
            layer = 3 if i == 2 else i
            move = fore_move if i == 2 else mid_move if i == 1 else back_move
            if not move:
                continue
            # Advance the tapeScroll position for the layer
            tapePos = scroll[layer] + move
            scroll[layer] = tapePos
            # Find the tape position for the column that needs to be filled
            x = tapePos + 72 - (1 if move == 1 else 0)
            offX = layer*144 + x%72*2
            # Update 2 words of vertical pattern for the tape
            # (the top 32 bits, then the bottom 32 bits)
            pattern = self.feed[layer]
            tape[offX] = int(pattern(x, 0))
            tape[offX+1] = int(pattern(x, 32))
            if layer != 0:
                fill_pattern = self.feed[layer + 1]
                tape[offX+144] = int(fill_pattern(x, 0))
                tape[offX+145] = int(fill_pattern(x, 32))
        
    @micropython.viper
    def offset_vertically(self, offset: int):
        """ Shift the view on the tape to a new vertical position, by
        specifying the offset from the top position. This cannot
        exceed the total vertical size of the tape (minus the tape height).
        """
        ptr32(self._tapeScroll)[4] = (
            offset if offset >= 0 else 0) if offset <= 24 else 24


## Patterns ##

# Patterns are a collection of mathematical, and logical functions
# that deterministically draw columns of the tape as it rolls in
# either direction. This enables the procedural creation of levels,
# but is really just a good way to get richness cheaply on this
# beautiful little piece of hardware.

# Simple cache used across the writing of a single column of the tape.
# Since the tape patterns must be stateless across columns (for rewinding), this
# should not store data across columns.
buf = array('i', [0, 0, 0, 0, 0, 0, 0, 0])

@micropython.viper
def pattern_template(x: int, oY: int) -> int:
    """ PATTERN [template]: Template for patterns. Not intended for use. """
    v = 0
    for y in range(oY, oY+32):
        v |= (
            1 # pattern (1=lit pixel, for fill layer, 0=clear pixel)
        ) << (y-oY)
    return v
@micropython.viper
def pattern_none(x: int, oY: int) -> int:
    """ PATTERN [none]: empty"""
    return 0

@micropython.viper
def pattern_fill(x: int, oY: int) -> int:
    """ PATTERN [fill]: completely filled """
    return int(0xFFFFFFFF) # 1 for all bits

@micropython.viper
def pattern_fence(x: int, oY: int) -> int:
    """ PATTERN [fence]: - basic dotted fences at roof and high floor """
    v = 0
    for y in range(oY, oY+32):
        v |= (
            (1 if y<12 else 1 if y>32 else 0) & int(x%10 == 0) & int(y%2 == 0)
        ) << (y-oY)
    return v

@micropython.viper
def pattern_room(x: int, oY: int) -> int:
    """ PATTERN [room]:- basic flat roof and high floor """
    v = 0
    for y in range(oY, oY+32):
        v |= (
            1 if y < 3 else 1 if y > 37 else 0
        ) << (y-oY)
    return v

@micropython.viper
def pattern_test(x: int, oY: int) -> int:
    """ PATTERN [test]: long slope plus walls """
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(x%120 == y*3) | (int(x%12 == 0) & int(y%2 == 0))
        ) << (y-oY)
    return v

@micropython.viper
def pattern_wall(x: int, oY: int) -> int:
    """ PATTERN [wall]: dotted vertical lines repeating """
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(x%16 == 0) & int(y%3 == 0)
         ) << (y-oY)
    return v

@micropython.viper
def pattern_cave(x: int, oY: int) -> int:
    """ PATTERN [cave]:
    Cave system with ceiling and ground. Ceiling is never less
    than 5 deep. Both have a random terrain and can intersect.
    """
    # buff: [ground-height, ceiling-height, ground-fill-on]
    buff = ptr32(buf)
    if oY == 0:
        buff[0] = int(shash(x,32,48)) + int(shash(x,16,24)) + int(shash(x,4,16))
        buff[1] = int(abs(int(shash(x,8,32)) - (buff[0] >> 2)))
        buff[2] = int(x % (buff[0]//8) == 0)
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(y > buff[0]) | int(y < buff[1]) | int(y <= 5)
         ) << (y-oY)
    return v
@micropython.viper
def pattern_cave_fill(x: int, oY: int) -> int:
    """ PATTERN [cave_fill]:
    Fill pattern for the cave. The ceiling is semi-reflective
    at the plane at depth 5. The ground has vertical lines.
    """
    # buff: [ground-height, ceiling-height, ground-fill-on]
    buff = ptr32(buf)
    v = 0
    for y in range(oY, oY+32):
        v |= (
            ((int(y < buff[0]//2*3) | buff[2]) # ground fill
            # ceiling fill
            & (int(y > 10-buff[1]) | int(y > 5) | int(y == 5) | buff[1]%y))
        ) << (y-oY)
    return v

@micropython.viper
def pattern_stalagmites(x: int, oY: int) -> int:
    """ PATTERN [stalagmites]:
    Stalagmite columns coming from the ground and associated
    stalactite columns hanging from the ceiling.
    These undulate in height in clustered waves.
    """
    # buff: [ceiling-height, fill-shading-offset]
    buff = ptr32(buf)
    if oY == 0:
        t1 = (x%256)-128
        t2 = (x%18)-9
        t3 = (x%4)-2
        buff[0] = 50 - t1*t1//256 - t2*t2//4 - t3*t3*4
        buff[1] = 15*(x%4)
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(y < buff[0]) | int(y > 64 - buff[0])
        ) << (y-oY)
    return v
@micropython.viper
def pattern_stalagmites_fill(x: int, oY: int) -> int:
    """ PATTERN [stalagmites_fill]:
    Associated shading pattern for the stalagmite layer.
    Stalagmites are shaded in a symetric manner while
    stalactites have shadows to the left. This is just for
    visual richness.
    """
    # buff: [ceiling-height, fill-shading-offset]
    buff = ptr32(buf)
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(y+20 > buff[0]) & int(y-buff[1] < 64 - buff[0])
        ) << (y-oY)
    return v

@micropython.viper
def pattern_toplit_wall(x: int, oY: int) -> int:
    """ PATTERN [toplit_wall]: organic background with roof shine """
    v = 0
    for y in range(oY, oY+32):
        v |= (
            1 if (x*x)%y == 0 else 0
        ) << (y-oY)
    return v


## Interesting pattern library for future considerations ## 
##
# PATTERN [toothsaw]: TODO use and update for word
@micropython.viper
def pattern_toothsaw(x: int, y: int) -> int:
    return int(y > (113111^x+11) % 64 // 2 + 24)
##
# PATTERN [revtoothsaw]: TODO use and update for word
@micropython.viper
def pattern_revtoothsaw(x: int, y: int) -> int:
    return int(y > (11313321^x) % 64)
##
# PATTERN [diamondsaw]: TODO use and update for word
@micropython.viper
def pattern_diamondsaw(x: int, y: int) -> int:
    return int(y > (32423421^x) % 64)
##
# PATTERN [fallentree]: TODO use and update for word
@micropython.viper
def pattern_fallentree(x: int, y: int) -> int:
    return int(y > (32423421^(x+y)) % 64)
@micropython.viper
def pattern_panelsv(x: int, oY: int) -> int:
    """ PATTERN [panels]: TODO """
    v = 0
    for y in range(oY, oY+32):
        v |= (
            1 if (x*y)%100 == 0 else 0
        ) << (y-oY)
    return v




## Actors ##

class Umby:
    pass



## Game Engine ##

def set_level(tape):
    """ Prepare everything for a level of gameplay including
    the starting tape, and the feed patterns for each layer.
    """
    # Set the feed patterns for each layer.
    # (back, mid-back, mid-back-fill, foreground, foreground-fill)
    # Fill the tape with the starting area
    tape.feed[:] = [pattern_wall,
        pattern_fence, pattern_fill,
        pattern_room, pattern_fill]
    for i in range(72):
        tape.scroll_tape(1, 1, 1)
    # Ready tape for main area
    tape.feed[:] = [pattern_toplit_wall,
        pattern_stalagmites, pattern_stalagmites_fill,
        pattern_cave, pattern_cave_fill]

def run_game():
    """ Initialise the game and run the game loop"""
    tape = Tape()
    set_level(tape)

    # FPS (intended to be between 60 and 120 variable fps)
    thumby.display.setFPS(2400000) # TESTING: for speed profiling

    # Main gameplay loop
    c = 0;
    profiler = time.ticks_ms()
    while(1):
        # Speed profiling
        if (c % 60 == 0):
            print(time.ticks_ms() - profiler)
            profiler = time.ticks_ms()
    
        # Update the display buffer new frame data
        tape.comp()
        # Flush to the display, waiting on the next frame interval
        thumby.display.update()
    
    
        # TESTING: infinitely scroll the tape
        tape.offset_vertically((c // 10) % 24)
        tape.scroll_tape(1 if c % 4 == 0 else 0, c % 2, 1)
        c += 1
run_game()

