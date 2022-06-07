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

# TODO: Make load/save
# TODO: Make help 
# TODO: Make AI Umby
# TODO: Make AI Glow
# TODO: Make 2 player (remote monsters out of range go to background)
# TODO: Make script/story outline
# TODO: Write script / story
# TODO: Add 8 more levels, extended game dynamics, and more monsters!
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
Lung gives info as sacrifice (he will be flooded out - no time to save)
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

_FPS = const(60) # FPS (intended to be 60 fps) - increase to speed profile

from array import array
from time import ticks_ms
import math
from thumby import display
import thumby

# Button functions. Note they return the inverse pressed state
bU = thumby.buttonU.pin.value
bD = thumby.buttonD.pin.value
bL = thumby.buttonL.pin.value
bR = thumby.buttonR.pin.value
bB = thumby.buttonB.pin.value
bA = thumby.buttonA.pin.value

## Tape Management ##

class Tape:
    """
    Scrolling tape with a fore, mid, and background layer.
    This represents the level of the ground but doesn't include actors.
    The foreground is the parts of the level that are interactive with
    actors such as the ground, roof, and platforms.
    Mid and background layers are purely decorative.
    Each layer can be scrolled intependently and then composited onto the
    display buffer.
    Each layer is created by providing deterministic functions that
    draw the pixels from x and y coordinates. Its really just an elaborate
    graph plotter - a scientific calculator turned games console!
    The tape size is 64 pixels high, with an infinite length, and 216 pixels
    wide are buffered (72 pixels before tape position, 72 pixels of visible,
    screen, and 72 pixels beyond the visible screen).
    This is intended for the 72x40 pixel view. The view can be moved
    up and down but when it moves forewards and backwards, the buffer
    is cycled backwards and forewards. This means that the tape
    can be modified (such as for explosion damage) for the 64 pixels high,
    and 216 pixels wide, but when the tape is rolled forewards, and backwards,
    the columns that go out of buffer are reset.
    There is also an overlay layer and associated mask, which is not
    subject to any tape scrolling or vertical offsets.
    """
    # Scrolling tape with each render layer being a section one after the other.
    # Each section is a buffer that cycles (via the tape_scroll positions) as the
    # world scrolls horizontally. Each section can scroll independently so
    # background layers can move slower than foreground layers.
    # Layers each have 1 bit per pixel from top left, descending then wrapping
    # to the right.
    # The vertical height is 64 pixels and comprises of 2 ints each with 32 bits. 
    # Each layer is a layer in the composited render stack.
    # Layers from left to right:
    # - 0: far background
    # - 432: close background
    # - 864: close background fill (opaque: off pixels)
    # - 1296: landscape including ground, platforms, and roof
    # - 1728: landscape fill (opaque: off pixels)
    # - 2160: overlay mask (opaque: off pixels)
    # - 2304: overlay
    _tape = array('I', (0 for i in range(72*3*2*5+72*2*2)))
    # The scroll distance of each layer in the tape,
    # and then the frame number counter and vertical offset appended on the end.
    # The vertical offset (yPos), cannot be different per layer (horizontal
    # parallax only).
    # [backPos, midPos, frameCounter, forePos, yPos]
    _tape_scroll = array('i', [0, 0, 0, 0, 0, 0, 0])
    # Public accessible x position of the tape foreground relative to the level.
    # This acts as the camera position across the level.
    # Care must be taken to NOT modify this externally.
    x = memoryview(_tape_scroll)[3:4]
    midx = memoryview(_tape_scroll)[1:2]
    
    # Alphabet for writing text - 3x5 text size (4x6 with spacing)
    # BITMAP: width: 117, height: 8
    abc = bytearray([248,40,248,248,168,80,248,136,216,248,136,112,248,168,136,
        248,40,8,112,136,232,248,32,248,136,248,136,192,136,248,248,32,216,248,
        128,128,248,16,248,248,8,240,248,136,248,248,40,56,120,200,184,248,40,
        216,184,168,232,8,248,8,248,128,248,120,128,120,248,64,248,216,112,216,
        184,160,248,200,168,152,0,0,0,0,184,0,128,96,0,192,192,0,0,80,0,32,32,
        32,32,80,136,136,80,32,8,168,56,248,136,136,136,136,248,16,248,0,144,
        200,176])
    abc_i = dict((v, i) for i, v in enumerate(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ !,.:-<>?[]12"))

    # The patterns to feed into each tape section
    feed = [None, None, None, None, None]

    def __init__(self):
        self.clear_overlay()

    @micropython.viper
    def check(self, x: int, y: int) -> bool:
        """ Returns true if the x, y position is solid foreground """
        tape = ptr32(self._tape)
        p = x%216*2+1296
        return bool(tape[p] & (1 << y) if y < 32 else tape[p+1] & (1 << y-32))

    @micropython.viper
    def comp(self, stage: ptr32):
        """ Composite all the render layers together and render directly to
        the display buffer, taking into account the scroll position of each
        render layer, and dimming the background layers.
        @param stage: The draw layers for the monsters and players
                        to stack within the comp.
        """
        tape = ptr32(self._tape)
        scroll = ptr32(self._tape_scroll)
        frame = ptr8(display.display.buffer)
        # Obtain and increase the frame counter
        scroll[2] += 1 # Counter
        y_pos = scroll[4]
        # Loop through each column of pixels
        for x in range(72):
            # Create a modifier for dimming background layer pixels.
            # The magic number here is repeating on and off bits, which is
            # alternated horizontally and in time. Someone say "time crystal".
            dim = int(1431655765) << (scroll[2]+x)%2
            # Compose the first 32 bits vertically.
            p0 = (x+scroll[0])%216*2
            p1 = (x+scroll[1])%216*2
            p3 = (x+scroll[3])%216*2
            x2 = x*2
            a = uint(((
                        # Back/mid layer (with monster mask and fill)
                        ((tape[p0] | tape[p1+432]) & stage[x2+288]
                            & stage[x2+432] & tape[p1+864] & tape[p3+1728])
                        # Background (non-interactive) monsters
                        | stage[x2])
                    # Dim all mid and background layers
                    & dim
                    # Foreground monsters (and players)
                    | stage[x2+144]
                    # Foreground (with monster mask and fill)
                    | (tape[p3+1296] & stage[x2+432] & tape[p3+1728]))
                # Now apply the overlay mask and draw layers.
                & (tape[x2+2160] << y_pos)
                | (tape[x2+2304] << y_pos))
            # Now compose the second 32 bits vertically.
            b = uint(((
                        # Back/mid layer (with monster mask and fill)
                        ((tape[p0+1] | tape[p1+433]) & stage[x2+289]
                        & stage[x2+433] & tape[p1+865] & tape[p3+1729])
                        # Background (non-interactive) monsters
                        | stage[x2+1])
                    # Dim all mid and background layers
                    & dim
                    # Foreground monsters (and players)
                    | stage[x2+145]
                    # Foreground (with monster mask and fill)
                    | (tape[p3+1297] & stage[x2+433] & tape[p3+1729]))
                # Now apply the overlay mask and draw layers.
                & ((uint(tape[x2+2160]) >> 32-y_pos) | (tape[x2+2161] << y_pos))
                | (uint(tape[x2+2304]) >> 32-y_pos) | (tape[x2+2305] << y_pos))
            # Apply the relevant pixels to next vertical column of the display
            # buffer, while also accounting for the vertical offset.
            frame[x] = a >> y_pos
            frame[72+x] = (a >> 8 >> y_pos) | (b << (32 - y_pos) >> 8)
            frame[144+x] = (a >> 16 >> y_pos) | (b << (32 - y_pos) >> 16)
            frame[216+x] = (a >> 24 >> y_pos) | (b << (32 - y_pos) >> 24)
            frame[288+x] = b >> y_pos
    
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
        scroll = ptr32(self._tape_scroll)
        for i in range(3):
            layer = 3 if i == 2 else i
            move = fore_move if i == 2 else mid_move if i == 1 else back_move
            if not move:
                continue
            # Advance the tape_scroll position for the layer
            tapePos = scroll[layer] + move
            scroll[layer] = tapePos
            # Find the tape position for the column that needs to be filled
            x = tapePos + 143 if move == 1 else tapePos - 72
            offX = layer*432 + x%216*2
            # Update 2 words of vertical pattern for the tape
            # (the top 32 bits, then the bottom 32 bits)
            pattern = self.feed[layer]
            tape[offX] = int(pattern(x, 0))
            tape[offX+1] = int(pattern(x, 32))
            if layer != 0:
                fill_pattern = self.feed[layer + 1]
                tape[offX+432] = int(fill_pattern(x, 0))
                tape[offX+433] = int(fill_pattern(x, 32))

    @micropython.viper
    def redraw_tape(self, layer: int, x: int, pattern, fill_pattern):
        """ Updates a tape layer for a given x position
        (relative to the start of the tape) with a pattern function.
        This can be used to draw to a layer without scrolling.
        These layers can be rendered to:
            0: Far background layer
            1: Mid background layer
            2: Foreground layer
        """
        tape = ptr32(self._tape)
        l = 3 if layer == 2 else layer
        offX = l*432 + x%216*2
        tape[offX] = int(pattern(x, 0))
        tape[offX+1] = int(pattern(x, 32))
        if l != 0 and fill_pattern:
            tape[offX+432] = int(fill_pattern(x, 0))
            tape[offX+433] = int(fill_pattern(x, 32))

    @micropython.viper
    def scratch_tape(self, layer: int, x: int, pattern, fill_pattern):
        """ Carves a hole out of a tape layer for a given x position
        (relative to the start of the tape) with a pattern function.
        Draw layer: 1-leave, 0-carve
        Fill layer: 0-leave, 1-carve
        These layers can be rendered to:
            0: Far background layer
            1: Mid background layer
            2: Foreground layer
        """
        tape = ptr32(self._tape)
        l = 3 if layer == 2 else layer
        offX = l*432 + x%216*2
        tape[offX] &= int(pattern(x, 0))
        tape[offX+1] &= int(pattern(x, 32))
        if l != 0 and fill_pattern:
            tape[offX+432] |= int(fill_pattern(x, 0))
            tape[offX+433] |= int(fill_pattern(x, 32))

    @micropython.viper
    def draw_tape(self, layer: int, x: int, pattern, fill_pattern):
        """ Draws over the top of a tape layer for a given x position
        (relative to the start of the tape) with a pattern function.
        This combines the existing layer with the provided pattern.
        Draw layer: 1-leave, 0-carve
        Fill layer: 0-leave, 1-carve
        These layers can be rendered to:
            0: Far background layer
            1: Mid background layer
            2: Foreground layer
        """
        tape = ptr32(self._tape)
        l = 3 if layer == 2 else layer
        offX = l*432 + x%216*2
        tape[offX] |= int(pattern(x, 0))
        tape[offX+1] |= int(pattern(x, 32))
        if l != 0 and fill_pattern:
            tape[offX+432] &= int(fill_pattern(x, 0))
            tape[offX+433] &= int(fill_pattern(x, 32))

    @micropython.viper
    def reset_tape(self, p: int):
        """ Reset the tape buffers for all layers to the
        given position and fill with the current feed.
        """
        scroll = ptr32(self._tape_scroll)
        for i in range(3):
            layer = 3 if i == 2 else i
            tapePos = scroll[layer] = (p if layer == 3 else 0)
            for x in range(tapePos-72, tapePos+144):
                self.redraw_tape(i, x, self.feed[layer], self.feed[layer+1])
        
    @micropython.viper
    def offset_vertically(self, offset: int):
        """ Shift the view on the tape to a new vertical position, by
        specifying the offset from the top position. This cannot
        exceed the total vertical size of the tape (minus the tape height).
        """
        ptr32(self._tape_scroll)[4] = (
            offset if offset >= 0 else 0) if offset <= 24 else 24

    @micropython.viper
    def auto_camera_parallax(self, x: int, y: int, t: int):
        """ Move the camera so that an x, y tape position is in the spotlight.
        This will scroll each tape layer to immitate a camera move and
        will scroll with standard parallax.
        """
        # Get the current camera position
        c = ptr32(self._tape_scroll)[3]
        # Scroll the tapes as needed
        if x < c + 10:
            self.scroll_tape(-1 if c % 4 == 0 else 0, 0-(c % 2), -1)
        elif x > c + 40 or (x > c + 20 and t%4==0):
            self.scroll_tape(1 if c % 4 == 0 else 0, c % 2, 1)
        # Reset the vertical offset as needed
        y -= 20
        ptr32(self._tape_scroll)[4] = (y if y >= 0 else 0) if y <= 24 else 24

    @micropython.viper
    def write(self, layer: int, text, x: int, y: int):
        """ Write text to the mid background layer at an x, y tape position.
        This also clears a space around the text for readability using
        the background clear mask layer.
        Text is drawn with the given position being at the botton left
        of the written text (excluding the mask border).
        There are 2 layers that can be rendered to:
            1: Mid background layer.
            3: Overlay layer.
        When writing to the overlay layer, the positional coordinates
        should be given relative to the screen, rather than the tape.
        """
        text = text.upper() # only uppercase is supported
        tape = ptr32(self._tape)
        abc_b = ptr8(self.abc)
        abc_i = self.abc_i
        h = y - 8 # y position is from bottom of text
        # Select the relevant layers
        mask = 864 if layer == 1 else 2160
        draw = 432 if layer == 1 else 2304
        # Clear space on background mask layer
        b = 0xFE
        for i in range(int(len(text))*4+1):
            p = (x-1+i)%216*2+mask
            tape[p] ^= tape[p] & (b >> -1-h if h+1 < 0 else b << h+1)
            tape[p+1] ^= tape[p+1] & (b >> 31-h if h-31 < 0 else b << h-31)
        # Draw to the mid background layer
        for i in range(int(len(text))):
            for o in range(3):
                p = (x+o+i*4)%216*2
                b = abc_b[int(abc_i[text[i]])*3+o]
                img1 = b >> 0-h if h < 0 else b << h
                img2 = b >> 32-h if h-32 < 0 else b << h-32
                # Draw to the draw layer
                tape[p+draw] |= img1
                tape[p+draw+1] |= img2
                # Stencil text out of the clear background mask layer
                tape[p+mask] |= img1
                tape[p+mask+1] |= img2

    @micropython.native
    def message(self, position, text):
        """ Write a message to the top (left), center (middle), or
        bottom (right) of the screen in the overlay layer.
        @param position: (int) 0 - center, 1 - top, 2 - bottom.
        """
        # Split the text into lines that fit on screen.
        lines = [""]
        for word in text.split(' '):
            if (len(lines[-1]) + len(word) + 1)*4 > 72:
                lines.append("")
            lines[-1] += (" " if lines[-1] else "") + word
        # Draw centered (if applicable)
        if position == 0:
            x = 25-len(lines)*3
            while (lines):
                line = lines.pop(0)
                self.write(3, line, 36-(len(line)*2), x)
                x += 6
        else:
            # Draw top (if applicable)
            if position == 1:
                x = 5
            # Draw bottom (if applicable)
            if position == 2:
                x = 46 - 6*len(lines)
            while (lines):
                self.write(2, lines.pop(0), 0, x)
                x += 6

    @micropython.viper
    def tag(self, text, x: int, y: int):
        """ Write text to the mid background layer centered
        on the given tape foreground scoll position.
        """
        scroll = ptr32(self._tape_scroll)
        p = x-scroll[3]+scroll[1] # Translate position to mid background
        self.write(1, text, p-int(len(text))*2, y+3)

    @micropython.viper
    def clear_overlay(self):
        """ Reset and clear the overlay layer and it's mask layer.
        """
        tape = ptr32(self._tape)
        # Reset the overlay mask layer
        mask = uint(0xFFFFFFFF)
        for i in range(2160, 2304):
            tape[i] = mask
        # Reset and clear the overlay layer
        mask = uint(0xFFFFFFFF)
        for i in range(2304, 2448):
            tape[i] = 0


## Patterns ##

# Patterns are a collection of mathematical, and logical functions
# that deterministically draw columns of the tape as it rolls in
# either direction. This enables the procedural creation of levels,
# but is really just a good way to get richness cheaply on this
# beautiful little piece of hardware.

# Utility functions

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
    p = x-500
    for y in range(oY, oY+32):
        v |= (
            1 if (p*p)%y == 0 else 0
        ) << (y-oY)
    return v

def bang(blast_x, blast_y, blast_size, invert):
    """ PATTERN (DYNAMIC) [bang]: explosion blast with customisable
    position and size. Intended to be used for scratch_tape.
    Comes with it's own inbuilt fill patter for also blasting away
    the fill layer.
    @returns: a pattern (or fill) function.
    """
    @micropython.viper
    def pattern(x: int, oY: int) -> int:
        s = int(blast_size)
        f = int(invert)
        _by = int(blast_y)
        tx = x-int(blast_x)
        v = 0
        for y in range(oY, oY+32):
            ty = y-_by
            a = 0 if tx*tx+ty*ty < s*s else 1
            v |= (
                a if f == 0 else (0 if a else 1)
            ) << (y-oY)
        return v
    return pattern

# Pattern Library:
# Interesting pattern library for future considerations ## 
@micropython.viper
def pattern_toothsaw(x: int, y: int) -> int:
    """ PATTERN [toothsaw]: TODO use and update for word """
    return int(y > (113111^x+11) % 64 // 2 + 24)
@micropython.viper
def pattern_revtoothsaw(x: int, y: int) -> int:
    """ PATTERN [revtoothsaw]: TODO use and update for word """
    return int(y > (11313321^x) % 64)
@micropython.viper
def pattern_diamondsaw(x: int, y: int) -> int:
    """ PATTERN [diamondsaw]: TODO use and update for word """
    return int(y > (32423421^x) % 64)
@micropython.viper
def pattern_fallentree(x: int, y: int) -> int:
    """ PATTERN [fallentree]: TODO use and update for word """
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


## Actors and Stage ##

class Stage:
    """ Render and collision detection buffer
    for all the maps and monsters, and also the players.
    Monsters and players can be drawn to the buffer one
    after the other. Collision detection capabilities are
    very primitive and only allow checking for pixel collisions
    between what is on the buffer and another provided sprite.
    The Render buffer is two words (64 pixels) high, and
    72 pixels wide. Sprites passed in must be a byte tall,
    but any width.
    There are 4 layers on the render buffer, 2 for rendering
    background and foreground monsters, and 2 for clearing
    background and foreground environment for monster
    visibility.
    """
    # Frames for the drawing and checking collisions of all actors.
    # This includes layers for turning on pixels and clearing lower layers.
    # Clear layers have 0 bits for clearing and 1 for passing through.
    # This includes the following layers:
    # - 0: Non-interactive background monsters.
    # - 144: Foreground monsters.
    # - 288: Mid and background clear.
    # - 432: Foreground clear.
    stage = array('I', (0 for i in range(72*2*4)))

    @micropython.viper
    def check(self, x: int, y: int, b: int) -> bool:
        """ Returns true if the byte going up from the x, y position is solid
        foreground where it collides with a given byte.
        @param b: Collision byte (as an int). All pixels in this vertical
            byte will be checked. To check just a single pixel, pass in the
            value 128. Additional active bits will be checked going upwards
            from themost significant bit/pixel to least significant.
        """
        stage = ptr32(self.stage)
        p = x%72*2+144
        h = y - 8 # y position is from bottom of text
        img1 = b >> 0-h if h < 0 else b << h
        img2 = b >> 32-h if h-32 < 0 else b << h-32
        return bool((stage[p] & img1) | stage[p+1] & img2)

    @micropython.viper
    def clear(self):
        """ Reset the render and mask laters to their default blank state """
        draw = ptr32(self.stage)
        for i in range(288):
            draw[i] = 0
        mask = uint(0xFFFFFFFF)
        for i in range(288, 576):
            draw[i] = mask

    @micropython.viper
    def draw(self, layer: int, x: int, y: int, img: ptr8, w: int, f: int):
        """ Draw a sprite to a render layer.
        Sprites must be 8 pixels high but can be any width.
        Sprites can have multiple frames stacked horizontally.
        There are 2 layers that can be rendered to:
            0: Non-interactive background monster layer.
            1: Foreground monsters, traps and player.
        @param layer: (int) the layer to render to.
        @param x: screen x draw position.
        @param y: screen y draw position (from top).
        @param img: (ptr8) sprite to draw (single row VLSB).
        @param w: width of the sprite to draw.
        @param f: the frame of the sprite to draw.
        """
        o = x-f*w
        p = layer*144
        draw = ptr32(self.stage)
        for i in range(x if x >= 0 else 0, x+w if x+w < 72 else 71):
            b = uint(img[i-o])
            draw[p+i*2] |= (b << y) if y >= 0 else (b >> 0-y)
            draw[p+i*2+1] |= (b << y-32) if y >= 32 else (b >> 32-y)

    @micropython.viper
    def mask(self, layer: int, x: int, y: int, img: ptr8, w: int, f: int):
        """ Draw a sprite to a mask (clear) layer.
        This is similar to the "draw" method but applies a mask
        sprite to a mask later.
        There are 2 layers that can be rendered to:
            0: Mid and background environment mask (1 bit to clear).
            1: Foreground environment mask (1 bit to clear).
        """
        o = x-f*w
        p = (layer+2)*144
        draw = ptr32(self.stage)
        for i in range(x if x >= 0 else 0, x+w if x+w < 72 else 71):
            b = uint(img[i-o])
            draw[p+i*2] ^= (b << y) if y >= 0 else (b >> 0-y)
            draw[p+i*2+1] ^= (b << y-32) if y >= 32 else (b >> 32-y)


class Player:
    """ Standard functions that are the same for all players """
    # Player behavior mode such as Play, Testing, and Respawn
    mode = 0#Play (normal)
    rocket_x = 0
    rocket_y = 0
    rocket_active = 0

    @micropython.native
    def die(self, rewind_distance, death_message):
        """ Put Player into a respawning state """
        tape = self._tape
        self.mode = -1#Respawn
        self._respawn_x = tape.x[0] - rewind_distance
        tape.message(0, death_message)

    @micropython.native
    def kill(self, t, monster):
        """ Explode the rocket, killing the monster or nothing.
        Also carves space out of the ground.
        """
        rx = self.rocket_x
        ry = self.rocket_y
        tape = self._tape
        # Tag the wall with an explostion mark
        tag = t%4
        tape.tag("<BANG!>" if tag==0 else "<POW!>" if tag==1 else
            "<WHAM!>" if tag==3 else "<BOOM!>", rx, ry)
        # Tag the wall with a death message
        if monster:
            self._tape.tag("[RIP]", monster.x, monster.y)
        # Carve blast hole out of ground
        pattern = bang(rx, ry, 8, 0)
        fill = bang(rx, ry, 10, 1)
        for x in range(rx-10, rx+10):
            tape.scratch_tape(2, x, pattern, fill)
        # DEATH: Check for death by rocket blast
        dx = rx-self.x
        dy = ry-self.y
        if dx*dx + dy*dy < 64:
            self.die(240, self.name + " kissed a rocket!")
        # Get ready to end rocket
        self.rocket_active = 2

    @micropython.native
    def tick(self, t):
        """ Updated Player for one game tick.
        @param t: the current game tick count
        """
        # Normal Play modes
        if self.mode >= 0:
            self._tick_play(t)
            # Now handle rocket engine
            self._tick_rocket(t)
        # Respawn mode
        elif self.mode == -1:
            self._tick_respawn()
        # Testing mode
        elif self.mode == -99:
            self._tick_testing()

    @micropython.native
    def _tick_respawn(self):
        """ After the player dies, a respawn process begins,
        showing a death message, while taking Umby back
        to a respawn point on a new starting platform.
        This handles a game tick when a respawn process is
        active
        """
        tape = self._tape
        # Move Umby towards the respawn location
        if self._x > self._respawn_x:
            self._x -= 1
            self._y += 0 if int(self._y) == 20 else \
                1 if self._y < 20 else -1
            if int(self._x) == self._respawn_x + 120:
                # Hide any death message
                tape.clear_overlay()
            if self._x < self._respawn_x + 30:
                # Draw the starting platform
                tape.redraw_tape(2, int(self._x)-5, pattern_room, pattern_fill)
        else:
            # Return to normal play mode
            self.mode = 0#Play
            tape.write(1, "DONT GIVE UP!", tape.midx[0]+8, 26)
        # Update the viper friendly variables.
        self.x = int(self._x)
        self.y = int(self._y)

    @micropython.native
    def _tick_testing(self):
        """ Handle one game tick for when in test mode.
        Test mode allows you to explore the level by flying,
        free of interactions.
        """
        if not bU():
            self._y -= 1
        elif not bD():
            self._y += 1
        if not bL():
            self._x -= 1
        elif not bR():
            self._x += 1
        # Update the viper friendly variables.
        self.x = int(self._x)
        self.y = int(self._y)


class Umby(Player):
    """ One of the players you can play with.
    Umby is an earth worm. They can jump, aim, and fire rockets.
    Umby can also make platforms by releasing rocket trails.
    Monsters, traps, and falling offscreen will kill them.
    Hitting their head on a platform or a roof, while jumping, will
    also kill them.
    """
    # BITMAP: width: 3, height: 8, frames: 6
    _art = bytearray([16,96,0,0,112,0,0,96,16,0,112,0,48,112,64,64,112,48])
    # Umby's shadow
    _sdw = bytearray([48,240,0,0,240,0,0,240,48,0,240,0,48,240,192,192,240,48])
    # BITMAP: width: 3, height: 8, frames: 3
    _fore_mask = bytearray([112,240,112,112,240,240,240,240,112])
    # BITMAP: width: 9, height: 8
    _back_mask = bytearray([120,254,254,255,255,255,254,254,120])
    # BITMAP: width: 3, height: 8
    _aim = bytearray([64,224,64])
     # BITMAP: width: 3, height: 8
    _aim_fore_mask = bytearray([224,224,224])
    # BITMAP: width: 5, height: 8
    _aim_back_mask = bytearray([112,248,248,248,112])
    name = "Umby"

    def __init__(self, tape, stage, x, y):
        self._tape = tape
        self._stage = stage
        # Motion variables
        self._x = x # Middle of Umby
        self._y = y # Bottom of Umby
        self._y_vel = 0.0
        # Viper friendly variants (ints)
        self.x = int(x)
        self.y = int(y)
        # Rocket variables
        self._aim_angle = 2.5
        self._aim_pow = 1.0
        self.aim_x = int(math.sin(self._aim_angle)*10)
        self.aim_y = int(math.cos(self._aim_angle)*10)

    @micropython.native
    def _tick_play(self, t):
        """ Handle one game tick for normal play controls """
        tape = self._tape
        x = self.x
        y = self.y
        _chd = tape.check(x, y+1)
        _chu = tape.check(x, y-4)
        _chl = tape.check(x-1, y)
        _chlu = tape.check(x-1, y-3)
        _chr = tape.check(x+1, y)
        _chru = tape.check(x+1, y-3)
        # Apply gravity and grund check
        if not (_chd or _chl or _chr):
            # Apply gravity to vertical speed
            self._y_vel += 2.5 / _FPS
            # Update vertical position with vertical speed
            self._y += self._y_vel
        else:
            # Stop falling when hit ground but keep some fall speed ready
            self._y_vel = 0.5
        # CONTROLS: Apply movement
        if not bL():
            if not (_chl or _chlu) and t%3: # Movement
                self._x -= 1
            elif t%3==0 and not _chu: # Climbing
                self._y -= 1
        elif not bR():
            if not (_chr or _chru) and t%3: # Movement
                self._x += 1
            elif t%3==0 and not _chu: # Climbing
                self._y -= 1
        # CONTROLS: Apply jump - allow continual jump until falling begins
        if not bA() and (self._y_vel < 0 or _chd or _chl or _chr):
            if _chd or _chl or _chr: # detatch from ground grip
                self._y -= 1
            self._y_vel = -0.8
        # Update the viper friendly variables.
        self.x = int(self._x)
        self.y = int(self._y)
        # DEATH: Check for head smacking
        if _chu and self._y_vel < -0.4:
            self.die(240, "Umby face-planted the roof!")
        # DEATH: Check for falling into the abyss
        if self._y > 80:
            self.die(240, "Umby fell into the abyss!")

    @micropython.native
    def _tick_rocket(self, t):
        """ Handle one game tick for Umby's rocket.
        Rockets start with aiming a target, then the launch
        process begins and charges up. When the button is then
        released the rocket launches. When the rocket hits the
        ground it clears a blast radius, or kills Umby, if hit.
        During flight, further presses of the rocket button
        will leave a rocket trail that will act as a platform.
        """
        tape = self._tape
        angle = self._aim_angle
        power = self._aim_pow
        # CONTROLS: Apply rocket
        if not (bU() and bD() and bB()): # Rocket aiming
            # CONTROLS: Aiming
            self._aim_angle += 0.02 if not bU() else -0.02 if not bD() else 0
            if not (bB() or self.rocket_active): # Power rocket
                self._aim_pow += 0.03
            angle = self._aim_angle
            # Resolve rocket aim to the x by y vector form
            self.aim_x = int(math.sin(angle)*power*10.0)
            self.aim_y = int(math.cos(angle)*power*10.0)
        # Actually launch the rocket when button is released
        if bB() and power > 1.0 and not self.rocket_active:
            self.rocket_active = 1
            self._rocket_x = self.x
            self._rocket_y = self._y - 1
            self._rocket_x_vel = math.sin(angle)*power/2.0
            self._rocket_y_vel = math.cos(angle)*power/2.0
            self._aim_pow = 1.0
            self.aim_x = int(math.sin(angle)*10.0)
            self.aim_y = int(math.cos(angle)*10.0)
        # Apply rocket dynamics if it is active
        if self.rocket_active == 1:
            # Create trail platform when activated
            if not bB():
                rx = self.rocket_x
                ry = self.rocket_y
                rd = -1 if self.aim_x < 0 else 1
                trail = bang(rx-rd, ry, 2, 1)
                for x in range(rx-rd*2, rx, rd):
                    tape.draw_tape(2, x, trail, None)
            # Apply rocket motion
            self._rocket_x += self._rocket_x_vel
            self._rocket_y += self._rocket_y_vel
            self.rocket_x = int(self._rocket_x)
            self.rocket_y = int(self._rocket_y)
            # Apply gravity
            self._rocket_y_vel += 2.5 / _FPS
            rx = self.rocket_x
            ry = self.rocket_y
            # Check fallen through ground
            if ry > 80:
                # Diffuse rocket
                self.rocket_active = 0
            # Check if the rocket hit the ground
            if tape.check(rx, ry):
                # Explode rocket
                self.kill(t, None)
        # Wait until the rocket button is released before firing another
        if self.rocket_active == 2 and bB():
            self.rocket_active = 0

    @micropython.viper
    def draw(self, t: int):
        """ Draw Umby to the draw buffer """
        p = int(self._tape.x[0])
        stage = self._stage
        x_pos = int(self.x)
        y_pos = int(self.y)
        aim_x = int(self.aim_x)
        aim_y = int(self.aim_y)
        rock_x = int(self.rocket_x)
        rock_y = int(self.rocket_y)
        # Get animation frame
        # Steps through 0,1,2,3 every half second for animation
        # of looking left and right, and changes to movement art of
        # 4 when moving left and 5 when moving right.
        f = 4 if not bL() else 5 if not bR() else t*2 // _FPS % 4
        # 0 when still, 1 when left moving, 2 when right
        fm = 1 if not bL() else 2 if not bR() else 0
        # Draw Umby's layers and masks
        stage.draw(0, x_pos-1-p, y_pos-6, self._sdw, 3, f) # Shadow
        stage.draw(1, x_pos-1-p, y_pos-6, self._art, 3, f) # Umby
        stage.mask(0, x_pos-4-p, y_pos-6, self._back_mask, 9, 0)
        stage.mask(1, x_pos-1-p, y_pos-6, self._fore_mask, 3, fm)
        # Draw Umby's aim
        stage.draw(t*6//_FPS%2, x_pos-p+aim_x-1, y_pos-6+aim_y, self._aim, 3, 0)
        stage.mask(1, x_pos-p+aim_x-1, y_pos-6+aim_y, self._aim_fore_mask, 3, 0)
        stage.mask(0, x_pos-p+aim_x-2, y_pos-5+aim_y, self._aim_back_mask, 5, 0)
        # Draw Umby's rocket
        if int(self.rocket_active) == 1:
            stage.draw(1, rock_x-p-1, rock_y-7, self._aim, 3, 0)
            stage.draw(0, rock_x-p+(-3 if aim_x>0 else 1), rock_y-7,
                self._aim, 3, 0) # Rocket tail


class Glow(Player):
    """ One of the players you can play with.
    Glow is a cave dwelling glow worm. They can crawl along the roof,
    fall at will, swing with a grappling hook, and fire rockets.
    Unlike Umby, Rockets are self propelled and accelerate into a horizontal
    flight, They are launched backwards and downwards in the oppostite
    direction of the grappling hook aim, but accelerate horizontally
    into the opposite direction of the rocket aim at launch.
    Unlike Umby, Glow has two aims pointing in opposite directions,
    one for the grappling hook, and one for the rocket aim. Aim can only
    be moved up or down, and will switch to the horizontal direction for
    the last direction Glow pressed.
    Monsters, traps, and falling offscreen will kill them.
    Glow is not good with mud, and if hits the ground, including at a bad angle
    when on the grappling hook, will get stuck. This will cause it to be
    difficult to throw the grappling hook, and may leave Glow with the only
    option of sinking throug the abyse into the mud.
    This means glow can sometimes fall through thin platforms like Umby's
    platforms and then crawl underneath.
    Umby also has some specific modes:
        * 0: auto attach grapple hook to ceiling.
        * 1: grapple hook activated.
        * 2: normal movement
    """
    # BITMAP: width: 3, height: 8, frames: 6
    _art = bytearray([8,6,0,0,14,0,0,6,8,0,14,0,12,14,2,2,14,12])
    # Umby's shadow
    _sdw = bytearray([12,15,0,0,15,0,0,15,12,0,15,0,12,15,3,3,15,12])
    # BITMAP: width: 3, height: 8, frames: 3
    _fore_mask = bytearray([14,15,14,14,15,15,15,15,14])
    # BITMAP: width: 9, height: 8
    _back_mask = bytearray([120,254,254,255,255,255,254,254,120])
    # BITMAP: width: 3, height: 8
    _aim = bytearray([64,224,64])
     # BITMAP: width: 3, height: 8
    _aim_fore_mask = bytearray([224,224,224])
    # BITMAP: width: 5, height: 8
    _aim_back_mask = bytearray([112,248,248,248,112])
    name = "Glow"

    def __init__(self, tape, stage, x, y):
        self._tape = tape
        self._stage = stage
        # Motion variables
        self._x = x # Middle of Glow
        self._y = y # Bottom of Glow (but top because they upside-down!)
        self._x_vel = 0.0
        self._y_vel = 0.0
        # Viper friendly variants (ints)
        self.x = int(x)
        self.y = int(y)
        # Rocket variables
        self._aim_angle = -0.5
        self._aim_pow = 1.0
        self.dir = 1
        self._r_dir = 1
        self.aim_x = int(math.sin(self._aim_angle)*10.0)
        self.aim_y = int(math.cos(self._aim_angle)*10.0)
        # Grappling hook variables
        self._bAOnce = 0 # Had a press down of A button
        self._hook_x = 0 # Position where hook attaches ceiling
        self._hook_y = 0
        self._hook_ang = 0.0
        self._hook_vel = 0.0
        self._hook_len = 0.0

    @micropython.native
    def _bAO(self):
        if self._bAOnce == 1:
            self._bAOnce = -1
            return 1
        return 0

    @micropython.native
    def _tick_play(self, t):
        """ Handle one game tick for normal play controls """
        tape = self._tape
        x = self.x
        y = self.y
        _chd = tape.check(x, y-1)
        _chrd = tape.check(x+1, y-1)
        _chlld = tape.check(x-2, y-1)
        _chrrd = tape.check(x+2, y-1)
        _chld = tape.check(x-1, y-1)
        _chl = tape.check(x-1, y)
        _chr = tape.check(x+1, y)
        _chll = tape.check(x-2, y)
        _chrr = tape.check(x+2, y)
        _chu = tape.check(x, y+3)
        _chlu = tape.check(x-1, y+3)
        _chru = tape.check(x+1, y+3)
        free_falling = not (_chd or _chld or _chrd or _chl or _chr)
        head_hit = _chu or _chlu or _chru
        # CONTROLS: Activation of grappling hook
        if self.mode == 0:
            # Shoot hook straight up
            i = y-1
            while i > 0 and not tape.check(x, i):
                i -= 1
            self._hook_x = x
            self._hook_y = i
            self._hook_ang = 0.0
            self._hook_vel = 0.0
            self._hook_len = y - i
            # Start normal grappling hook mode
            self.mode = 1
        # CONTROLS: Grappling hook swing
        if self.mode == 1:
            ang = self._hook_ang
            # Apply gravity
            g = ang*ang/2.0
            self._hook_vel += -g if ang > 0 else g if ang < 0 else 0.0
            # Air friction
            vel = self._hook_vel
            self._hook_vel -= vel*vel*vel/64000
            # CONTROLS: swing
            self._hook_vel += -0.08 if not bL() else 0.08 if not bR() else 0
            # CONTROLS: climb/extend rope
            self._hook_len += -0.5 if not bU() else 0.5 if not bD() else 0
            # Check land interaction conditions
            if not free_falling and bA(): # Stick to ceiling if touched
                self.mode = 2
            elif head_hit or (not free_falling and vel*ang > 0):
                # Rebound off ceiling
                self._hook_vel = -self._hook_vel
            if free_falling and self._bAO(): # Release grappling hook
                self.mode = 2
                # Convert angular momentum to free falling momentum
                ang2 = ang + vel/128.0
                x2 = self._hook_x + math.sin(ang2)*self._hook_len
                y2 = self._hook_y + math.cos(ang2)*self._hook_len
                self._x_vel = x2 - self._x
                self._y_vel = y2 - self._y
            # Update motion and position variables based on swing
            self._hook_ang += self._hook_vel/128.0
            self._x = self._hook_x + math.sin(self._hook_ang)*self._hook_len
            self._y = self._hook_y + math.cos(self._hook_ang)*self._hook_len
        elif self.mode == 2: # Normal movement (without grappling hook)
            # CONTROLS: Activate hook
            if free_falling and self._bAO():
                # Activate grappling hook in aim direction
                self._hook_ang = self._aim_angle * self.dir
                # Find hook landing position
                x2 = -math.sin(self._hook_ang)/2
                y2 = -math.cos(self._hook_ang)/2
                xh = x
                yh = y
                while (yh > 0 and (x-xh)*self.dir < 40
                and not tape.check(int(xh), int(yh))):
                    xh += x2
                    yh += y2
                # Apply grapple hook parameters
                self._hook_x = int(xh)
                self._hook_y = int(yh)
                x1 = x - self._hook_x
                y1 = y - self._hook_y
                self._hook_len = math.sqrt(x1*x1+y1*y1)
                # Now get the velocity in the grapple angle
                v1 = (1-self._x_vel*y1+self._y_vel*x1)/(self._hook_len+1)
                xv = self._x_vel
                yv = self._y_vel
                self._hook_vel = -math.sqrt(xv*xv+yv+yv)*v1*4
                # Start normal grappling hook mode
                self.mode = 1
            # CONTROLS: Fall (force when jumping)
            elif free_falling or not bA():
                if not free_falling:
                    self._bAO() # Claim 'A' so we don't immediately grapple
                    self._x_vel = -0.5 if not bL() else 0.5 if not bR() else 0.0
                # Apply gravity to vertical speed
                self._y_vel += 1.5 / _FPS
                # Update positions with momentum
                self._y += self._y_vel
                self._x += self._x_vel
            else:
                # Stop falling when attached to roof
                self._y_vel = 0
            # CONTROLS: Apply movement
            if not bL() and t%2:
                # Check if moving left possible and safe
                if not (_chl or _chlu) and (_chld or _chd or _chlld or _chll):
                    self._x -= 1
                # Check if climbing is needed and safe
                elif not _chd and _chrd:
                    self._y -= 1
                # Check is we should decend
                elif (_chl or _chlu) and not _chu:
                    self._y += 1
            elif not bR() and t%2:
                # Check if moving right possible and safe
                if not (_chr or _chru) and (_chrd or _chd or _chrrd or _chrr):
                    self._x += 1
                # Check if climbing is needed and safe
                elif not _chd and _chld:
                    self._y -= 1
                # Check is we should decend
                elif (_chr or _chru) and not _chu:
                    self._y += 1
        # Update the state of the A button pressed detector
        if not bA():
            if self._bAOnce == 0:
                self._bAOnce = 1
        else:
            self._bAOnce = 0
        # Update the viper friendly variables.
        self.x = int(self._x)
        self.y = int(self._y)
        # DEATH: Check for falling into the abyss
        if self._y > 80:
            self.die(240, "Umby fell into the abyss!")

    @micropython.native
    def _tick_rocket(self, t):
        """ Handle one game tick for Glows's rocket.
        Rockets start with aiming a target, then the launch
        process begins and charges up. When the button is then
        released the rocket launches. When the rocket hits the
        ground it clears a blast radius, or kills Glow, if hit.
        See the class doc strings for more details.
        """
        tape = self._tape
        angle = self._aim_angle
        power = self._aim_pow
        grappling = self.mode == 1
        # CONTROLS: Apply rocket
        # Rocket aiming
        if not bU() or not bD() or not bB() or not bL() or not bR():
            angle = self._aim_angle
            if not bU() and not grappling: # Aim up
                angle += 0.02
            elif not bD() and not grappling: # Aim down
                angle -= 0.02
            if not bL(): # Aim left
                self.dir = -1
            elif not bR(): # Aim right
                self.dir = 1
            if not bB(): # Power rocket
                self._aim_pow += 0.03
            angle = -2.0 if angle < -2.0 else 0 if angle > 0 else angle
            self._aim_angle = angle
            # Resolve rocket aim to the x by y vector form
            self.aim_x = int(math.sin(angle)*power*10.0)*self.dir
            self.aim_y = int(math.cos(angle)*power*10.0)
        # Actually launch the rocket when button is released
        if bB() and power > 1.0:
            self.rocket_active = 1
            self._rocket_x = self.x
            self._rocket_y = self._y + 1
            self._rocket_x_vel = math.sin(angle)*power/2.0*self.dir
            self._rocket_y_vel = math.cos(angle)*power/2.0
            self._aim_pow = 1.0
            self.aim_x = int(math.sin(angle)*10.0)*self.dir
            self.aim_y = int(math.cos(angle)*10.0)
            self._r_dir = self.dir
        # Apply rocket dynamics if it is active
        if self.rocket_active == 1:
            # Apply rocket motion
            self._rocket_x += self._rocket_x_vel
            self._rocket_y += self._rocket_y_vel
            self.rocket_x = int(self._rocket_x)
            self.rocket_y = int(self._rocket_y)
            rx = self.rocket_x
            ry = self.rocket_y
            # Apply flight boosters
            self._rocket_x_vel += 2.5 / _FPS * self._r_dir
            if ((self._rocket_x_vel > 0 and self._r_dir > 0)
            or (self._rocket_x_vel < 0 and self._r_dir < 0)):
                self._rocket_y_vel *= 0.9
            # Check fallen through ground or above ceiling,
            # or out of range
            px = self.rocket_x - tape.x[0]
            if ry > 80 or ry < -1 or px < -72 or px > 144:
                # Diffuse rocket
                self.rocket_active = 0
            # Check if the rocket hit the ground
            if tape.check(rx, ry):
                # Explode rocket
                self.kill(t, None)
        # Immediately reset rickets after an explosion
        if self.rocket_active == 2:
            self.rocket_active = 0

    @micropython.viper
    def draw(self, t: int):
        """ Draw Glow to the draw buffer """
        p = int(self._tape.x[0])
        stage = self._stage
        x_pos = int(self.x)
        y_pos = int(self.y)
        aim_x = int(self.aim_x)
        aim_y = int(self.aim_y)
        # Get animation frame
        # Steps through 0,1,2,3 every half second for animation
        # of looking left and right, and changes to movement art of
        # 4 when moving left and 5 when moving right.
        f = 4 if not bL() else 5 if not bR() else t*2 // _FPS % 4
        # 0 when still, 1 when left moving, 2 when right
        fm = 1 if not bL() else 2 if not bR() else 0
        # Draw Glows's layers and masks
        stage.draw(0, x_pos-1-p, y_pos-1, self._sdw, 3, f) # Shadow
        stage.draw(1, x_pos-1-p, y_pos-1, self._art, 3, f) # Glow
        stage.mask(0, x_pos-4-p, y_pos-1, self._back_mask, 9, 0)
        stage.mask(1, x_pos-1-p, y_pos-1, self._fore_mask, 3, fm)
        # Draw Glows's aim
        l = t*6//_FPS%2
        # Rope aim
        if int(self.mode) == 1: # Activated hook
            hook_x = int(self._hook_x)
            hook_y = int(self._hook_y)
            # Draw Glow's grappling hook rope
            for i in range(0, 8):
                sx = x_pos-p + (hook_x-x_pos)*i//8
                sy = y_pos + (hook_y-y_pos)*i//8
                stage.draw(1, sx-1, sy-6, self._aim, 3, 0)
            hx = hook_x-p-1
            hy = hook_y-6
        else:
            hx = x_pos-p-aim_x//2-1
            hy = y_pos-6-aim_y//2
        stage.draw(l, hx, hy, self._aim, 3, 0)
        stage.mask(1, hx, hy, self._aim_fore_mask, 3, 0)
        stage.mask(0, hx-1, hy+1, self._aim_back_mask, 5, 0)
        # Rocket aim
        x = x_pos-p+aim_x-1
        y = y_pos-6+aim_y
        stage.draw(l, x, y, self._aim, 3, 0)
        stage.mask(1, x, y, self._aim_fore_mask, 3, 0)
        stage.mask(0, x-1, y+1, self._aim_back_mask, 5, 0)
        # Draw Glows's rocket
        if self.rocket_active:
            rock_x = int(self.rocket_x)
            rock_y = int(self.rocket_y)
            dire = int(self._r_dir)
            stage.draw(1, rock_x-p-1, rock_y-7, self._aim, 3, 0)
            stage.draw(0, rock_x-p+(-3 if dire>0 else 1), rock_y-7,
                self._aim, 3, 0) # Rocket tail


class BonesTheMonster:
    """ Bones is a monster that flyes about then charges the player.
    Bones looks a bit like a skull.
    It will fly in a random direction until it hits a wall in which case
    it will change direction again. There is a very small chance that
    Bones will fly over walls and ground and Bones will continue until
    surfacing. If Bones goes offscreen to the left + 72 pixels, it will die;
    offscreen to the top or bottom plus 10, it will change direction.
    It will also change direction on occasion.
    When the player is within a short range, Bones will charge the player
    and will not stop.
    """
    # BITMAP: width: 7, height: 8, frames: 3
    _art = bytearray([28,54,147,110,147,54,28,28,190,159,110,159,190,28,28,242,
        139,222,139,242,28])
    # BITMAP: width: 9, height: 8
    _mask = bytearray([28,62,247,243,239,243,247,62,28])

    def __init__(self, tape, stage, spawn, x, y):
        self._tape = tape
        self._stage = stage
        self._spawn = spawn
        self.x = int(x) # Middle of Bones
        self.y = int(y) # Middle of Bones
        # Mode: 0 - flying, 1 - charging
        self.mode = 0
        self._x = x # floating point precision
        self._y = y # floating point precision
        self._dx = 0
        self._dy = 0

    @micropython.native
    def tick(self, t):
        """ Update Bones for one game tick """
        tape = self._tape
        # Find the potential new coordinates
        x = self.x
        y = self.y
        if self.mode == 0: # Flying
            nx = self._x + self._dx
            ny = self._y + self._dy
            # Change direction if needed
            if ((self._dx == 0 and self._dy == 0)
            or ny < -10 or ny > 74 or t%128==0
            or (tape.check(int(nx), int(ny)) and t%12 and not (
                tape.check(x, y) or y < 0 or y >= 64))):
                self._dx = math.sin(t+nx)/4.0
                self._dy = math.cos(t+nx)/4.0
            else:
                self._x = nx
                self._y = ny
                self.x = int(nx)
                self.y = int(ny)
            # Check for charging condition
            for plyr in self._spawn.players:
                px = plyr.x - x
                py = plyr.y - y
                if px*px + py*py < 300:
                    self._target = plyr
                    self.mode = 1
            # Check for own death conditions
            if x < tape.x[0]:
                self._spawn.mons.remove(self)
        elif t%4==0: # Charging
            t = self._target
            self.x += 1 if x < t.x else -1 if x > t.x else 0
            self.y += 1 if y < t.y else -1 if y > t.y else 0

    @micropython.viper
    def draw(self, t: int):
        """ Draw Bones to the draw buffer """
        p = int(self._tape.x[0])
        stage = self._stage
        x_pos = int(self.x)
        y_pos = int(self.y)
        mode = int(self.mode)
        # Select animation frame
        f = 2 if mode == 1 else 0 if t*16//_FPS % 16 else 1
        # Draw Bones' layers and masks
        stage.draw(1, x_pos-3-p, y_pos-4, self._art, 7, f) # Bones
        stage.mask(1, x_pos-4-p, y_pos-4, self._mask, 9, 0) # Mask
        stage.mask(0, x_pos-4-p, y_pos-4, self._mask, 9, 0) # Mask



# TODO: Some monster things

# Skittle (bug horizontal move (no vert on ground, waving in air)
bitmap3 = bytearray([0,56,84,56,124,56,124,56,16])
# BITMAP: width: 9, height: 8
bitmap4 = bytearray([56,124,254,124,254,124,254,124,56])

# Scout (slow wanderer on the ground, slow mover)
bitmap6 = bytearray([2,62,228,124,228,62,2])
# BITMAP: width: 7, height: 8
bitmap7 = bytearray([63,255,255,254,255,255,63])

# Stomper (swings up and down vertically)
# BITMAP: width: 7, height: 8
bitmap8 = bytearray([36,110,247,124,247,110,36])
# BITMAP: width: 7, height: 8
bitmap9 = bytearray([239,255,255,254,255,255,239])

# TODO: One the crawls along the ground and digs in to then pounce
# TODO: make a monster that spawns other monsters! (HARD)
# TODO: Do a monster that flys into the background


class MonsterSpawner:
    """ Spawns monsters as the tape scrolls
    Spawn rates are customisable.
    """
    _types = [BonesTheMonster] # Monster classes to spawn
    # Likelihood of each monster class spawning (out of 255) for every 5 steps
    rates = bytearray([0])
    # How far along the tape spawning has completed
    _x = array('I', [0])
    mons = [] # Active monsters
    players = [] # Player register for monsters to interact with

    def __init__(self, tape, stage):
        self._tape = tape
        self._stage = stage

    def reset(self, start):
        """ Remove all monsters and set a new spawn starting position """
        mons = []
        self._x[0] = start

    @micropython.viper
    def spawn(self):
        """ Spawn new monsters as needed """
        x = ptr32(self._x)
        p = int(self._tape.x[0])
        # Only spawn when scrolling into unseen land
        if x[0] >= p:
            return
        rates = ptr8(self.rates)
        r = int(uint(ihash(p)))
        # Loop through each monster type randomly spawning
        # at the configured rate.
        for i in range(0, int(len(self._types))):
            if rates[i] and r%(256-rates[i]) == 0:
                self.add(self._types[i], p+72+36, r%64)
            r = r >> 1 # Fast reuse of random number
        x[0] = p 

    @micropython.native
    def add(self, mon_type, x, y):
        """ Add a monster of the given type """
        if len(self.mons) < 10: # Limit to maximum 10 monsters at once
            self.mons.append(mon_type(self._tape, self._stage, self, x, y))


## Game Play ##

def set_level(tape, spawn, start):
    """ Prepare everything for a level of gameplay including
    the starting tape, and the feed patterns for each layer.
    @param start: The starting x position of the tape.
    """
    # Set the feed patterns for each layer.
    # (back, mid-back, mid-back-fill, foreground, foreground-fill)
    tape.feed[:] = [pattern_toplit_wall,
        pattern_stalagmites, pattern_stalagmites_fill,
        pattern_cave, pattern_cave_fill]
    # Fill the tape in the starting level
    tape.reset_tape(start)
    # Reset monster spawner to the new level
    spawn.rates[:] = bytearray([200])
    spawn.reset(start)
    if start > -9999:
        # Fill the visible tape with the starting platform
        for i in range(start, start+72):
            tape.redraw_tape(2, i, pattern_room, pattern_fill)
        # Draw starting instructions
        tape.write(1, "THAT WAY!", start+19, 26)
        tape.write(1, "------>", start+37, 32)

@micropython.native
def run_menu(tape, stage, spawn):
    """ Loads a starting menu and returns the selections.
    @returns: a tuple of the following values:
        * Umby (0), Glow (1)
        * 1P (0), 2P (1)
        * New (0), Load (1)
    """
    t = 0
    set_level(tape, spawn, -9999)
    spawn.add(BonesTheMonster, -9960, 25)
    m = spawn.mons[0]
    ch = [0, 0, 1] # Umby/Glow, 1P/2P, New/Load
    h = s = 0
    while(bA()):
        # Update the menu text
        if h == 0 and (t == 0 or not (bU() and bD() and bL() and bR())):
            s = (s + (1 if not bD() else -1 if not bU() else 0)) % 3
            ch[s] = (ch[s] + (1 if not bR() else -1 if not bL() else 0)) % 2
            @micropython.native
            def sel(i):
                return (("  " if ch[i] else "<<")
                    + ("----" if i == s else "    ")
                    + (">>" if ch[i] else "  "))
            tape.clear_overlay()
            msg = "UMBY "+sel(0)+" GLOW "
            msg += "1P   "+sel(1)+"   2P "
            msg += "NEW  "+sel(2)+" LOAD"
            tape.message(0, msg)
            h = 1
        elif bU() and bD() and bL() and bR():
            h = 0
        # Update the display buffer new frame data
        stage.clear()
        # Make the camera follow the monster
        m.tick(t)
        m.draw(t)
        tape.auto_camera_parallax(m.x, m.y, t)
        # Composite everything together to the render buffer
        tape.comp(stage.stage)
        # Flush to the display, waiting on the next frame interval
        display.update()
        t += 1
    tape.clear_overlay()
    return ch[0], ch[1], ch[2]

@micropython.native
def run_game():
    """ Initialise the game and run the game loop """
    # Basic setup
    display.setFPS(_FPS)
    tape = Tape()
    stage = Stage()
    spawn = MonsterSpawner(tape, stage)
    # Start menu
    glow, coop, load = run_menu(tape, stage, spawn)

    # Ready the level for playing
    sav = __file__[:-3] + "-" + ("glow" if glow else "umby") + ".sav"
    print(sav)
    #f = open(sav, "w")
    #f.write("500")
    #f.close()
    start = 3
    #if load:
    #    try:
    #        f = open(sav, "r")
    #        start = int(f.read())
    #        f.close()
    #    except:
    #        pass

    tape.message(0, start) # TODO debug

    t = 0;
    set_level(tape, spawn, start)
    if glow:
        p1 = Glow(tape, stage, start+10, 20)
    else:
        p1 = Umby(tape, stage, start+10, 20)
    spawn.players.append(p1)
    # (Secret) Testing mode
    if not (bR() or bA() or bB()):
        p1.mode = -99

    # Main gameplay loop
    profiler = ticks_ms()
    while(1):
        # Speed profiling
        if (t % 60 == 0):
            print(ticks_ms() - profiler)
            profiler = ticks_ms()
            # Save game

        # Update the game engine by a tick
        p1.tick(t)
        for mon in spawn.mons:
            mon.tick(t)

        # Make the camera follow the action
        tape.auto_camera_parallax(p1.x, p1.y, t)

        # Spawn new monsters as needed
        spawn.spawn()

        # Update the display buffer new frame data
        stage.clear()
        # Add all the monsters, and check for collisions along the way
        for mon in spawn.mons:
            mon.draw(t)
            # Check if a rocket hits this monster
            if p1.rocket_active:
                if stage.check(p1.rocket_x-tape.x[0], p1.rocket_y, 128):
                    spawn.mons.remove(mon)
                    p1.kill(t, mon)
        # If player is in play mode, check for monster collisions
        if p1.mode >= 0 and stage.check(p1.x-tape.x[0], p1.y, 224):
            p1.die(240, "Umby became monster food!")

        # Draw the players
        p1.draw(t)

        # Composite everything together to the render buffer
        tape.comp(stage.stage)
        # Flush to the display, waiting on the next frame interval
        display.update()

        t += 1
run_game()

