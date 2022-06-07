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

# TODO: Instead of replacing sections of the tape by scrolling, allow for replacing columns of the tape.
# TODO: extend tape cache to be 3 screens wide (288pixels) for mid and foreground
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
    # - 144: close background
    # - 288: close background fill (opaque: off pixels)
    # - 432: landscape including ground, platforms, and roof
    # - 576: landscape fill (opaque: off pixels)
    # - 720: overlay mask (opaque: off pixels)
    # - 864: overlay
    _tape = array('I', (0 for i in range(72*2*7)))
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
    # BITMAP: width: 105, height: 8
    abc = bytearray([248,40,248,248,168,112,248,136,216,248,136,112,248,168,136,
        248,40,8,112,136,232,248,32,248,136,248,136,192,136,248,248,32,216,248,
        128,128,248,48,248,248,8,240,248,136,248,248,40,56,120,200,184,248,40,
        216,184,168,232,8,248,8,248,128,248,120,128,120,248,64,248,216,112,216,
        184,160,248,200,168,152,0,0,0,0,184,0,128,96,0,192,192,0,0,80,0,32,32,
        32,32,80,136,136,80,32,8,168,56])
    # Index lookup for printable characters
    abc_i = dict((v, i) for i, v in enumerate(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ !,.:-<>?"))

    # The patterns to feed into each tape section
    feed = [None, None, None, None, None]

    def __init__(self):
        self.clear_overlay()

    @micropython.viper
    def check(self, x: int, y: int) -> bool:
        """ Returns true if the x, y position is solid foreground """
        tape = ptr32(self._tape)
        p = x%72*2+432
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
            p0 = (x+scroll[0])%72*2
            p1 = (x+scroll[1])%72*2
            p3 = (x+scroll[3])%72*2
            x2 = x*2
            a = uint(((
                        # Back/mid layer (with monster mask and fill)
                        ((tape[p0] | tape[p1+144]) & stage[x2+288]
                            & stage[x2+432] & tape[p1+288] & tape[p3+576])
                        # Background (non-interactive) monsters
                        | stage[x2])
                    # Dim all mid and background layers
                    & dim
                    # Foreground monsters (and players)
                    | stage[x2+144]
                    # Foreground (with monster mask and fill)
                    | (tape[p3+432] & stage[x2+432] & tape[p3+576]))
                # Now apply the overlay mask and draw layers.
                & (tape[x2+720] << y_pos)
                | (tape[x2+864] << y_pos))
            # Now compose the second 32 bits vertically.
            b = uint(((
                        # Back/mid layer (with monster mask and fill)
                        ((tape[p0+1] | tape[p1+145]) & stage[x2+289]
                        & stage[x2+433] & tape[p1+289] & tape[p3+577])
                        # Background (non-interactive) monsters
                        | stage[x2+1])
                    # Dim all mid and background layers
                    & dim
                    # Foreground monsters (and players)
                    | stage[x2+145]
                    # Foreground (with monster mask and fill)
                    | (tape[p3+433] & stage[x2+433] & tape[p3+577]))
                # Now apply the overlay mask and draw layers.
                & ((tape[x2+720] >> 32-y_pos) | (tape[x2+721] << y_pos-32))
                | (tape[x2+864] >> 32-y_pos) | (tape[x2+865] << y_pos-32))
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
            x = tapePos + 71 if move == 1 else tapePos
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
        ptr32(self._tape_scroll)[4] = (
            offset if offset >= 0 else 0) if offset <= 24 else 24

    @micropython.viper
    def auto_camera_parallax(self, x: int, y: int):
        """ Move the camera so that an x, y tape position is in the spotlight.
        This will scroll each tape layer to immitate a camera move and
        will scroll with standard parallax.
        """
        # Get the current camera position
        c = ptr32(self._tape_scroll)[3]
        # Scroll the tapes as needed
        if x < c + 10:
            self.scroll_tape(-1 if c % 4 == 0 else 0, 0-(c % 2), -1)
        elif x > c + 40:
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
        h = y - 11 # ignore top 3 bits of the byte height (5 height font)
        # Select the relevant layers
        mask = 288 if layer == 1 else 720
        draw = 144 if layer == 1 else 864
        # Clear space on background mask layer
        b = 0xFE
        for i in range(int(len(text))*4+1):
            p = (x-1+i)%72*2+mask
            tape[p] ^= tape[p] & (b >> 1-h if h+1 < 0 else b << h+1)
            tape[p+1] ^= tape[p+1] & (b >> 31-h if -31+h < 0 else b << -31+h)
        # Draw to the mid background layer
        for i in range(int(len(text))):
            for o in range(3):
                p = (x+o+i*4)%72*2
                b = abc_b[int(abc_i[text[i]])*3+o]
                img1 = b >> 0-h if h < 0 else b << h
                img2 = b >> 32-h if -32+h < 0 else b << -32+h
                # Draw to the mid background layer
                tape[p+draw] |= img1
                tape[p+draw+1] |= img2
                # Stencil text out of the clear background mask layer
                tape[p+mask] |= img1
                tape[p+mask+1] |= img2

    @micropython.viper
    def message(self, position: int, text):
        """ Write a message to the top (left), center (middle), or
        bottom (right) of the screen in the overlay layer.
        @param position: (int) 0 - center, 1 - top, 2 - bottom.
        """
        self.write(3, text, 0, 10)

    @micropython.viper
    def clear_overlay(self):
        """ Reset and clear the overlay layer and it's mask layer.
        """
        tape = ptr32(self._tape)
        # Reset the overlay mask layer
        mask = uint(0xFFFFFFFF)
        for i in range(720, 864):
            tape[i] = mask
        # Reset and clear the overlay layer
        mask = uint(0xFFFFFFFF)
        for i in range(864, 1008):
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
    def clear(self): # TODO
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

class Umby:
    """ One of the players you can play with.
    Umby is an earth worm. They can jump, aim, and fire rockets.
    Umby can also make platforms by releasing rocket trails.
    Monsters, traps, and falling offscreen will kill them.
    Hitting their head on a platform or a roof, while jumping, will
    also kill them.
    """
    # BITMAP: width: 3, height: 8, frames: 6
    _art = bytearray([16,96,0,0,112,0,0,96,16,0,112,0,48,112,64,64,112,48])
    _sdw = bytearray([48,240,0,0,240,0,0,240,48,0,240,0,48,240,192,192,240,48])
    # BITMAP: width: 3, height: 8, frames: 3
    _fore_mask = bytearray([112,240,112,112,240,240,240,240,112])
    # BITMAP: width: 9, height: 8
    _back_mask = bytearray([120,254,254,255,255,255,254,254,120])
    mode = 0#Play (normal)

    def __init__(self, x, y):
        # Main behavior modes such as Play, Testing, and Respawn
        # Motion variables
        self._x_pos = x
        self._y_pos = y
        self._x_vel = 0.0
        self._y_vel = 0.0
        # Viper friendly variables (ints)
        self.x_pos = int(x)
        self.y_pos = int(y)

    @micropython.native
    def tick(self, t, tape):
        """ Updated Umby for one game tick.
        @param t: the current game tick count
        """

        # Normal Play mode
        if self.mode == 0:
            # Apply gravity and grund check
            if not tape.check(self.x_pos, self.y_pos + 1): # check for ground
                # Apply gravity to vertical speed
                self._y_vel += 0.98 / _FPS
                # Update vertical position with vertical speed
                self._y_pos += 1 if self._y_vel > 1 else self._y_vel
            else:
                # Stop falling when hit ground
                self._y_vel = 0
    
            # Apply movement controls
            if not bU():
                self._y_pos -= 1
            elif not bD():
                self._y_pos += 1
            if not bL():
                self._x_pos -= 1
            elif not bR():
                self._x_pos += 1

            # Check for falling into the abyss
            if self._y_pos > 80:
                self.mode = 1#Respawn
                self._respawn_x = tape.x[0] - 240
                tape.message(0, "Umby fell into the abyss!")
    
        # Respawn mode
        elif self.mode == 1:
            # Move Umby towards the respawn location
            if self._x_pos > self._respawn_x:
                self._x_pos -= 1
                self._y_pos += 0 if int(self._y_pos) == 32 else \
                    1 if self._y_pos < 32 else -1
                if self._x_pos == self._respawn_x + 30:
                    # Generate the respawn platform (level section)
                    self._feed_cache = tape.feed
                    tape.feed = [pattern_wall,
                        pattern_fence, pattern_fill,
                        pattern_room, pattern_fill]
                    # Hide any death message
                if self._x_pos == self._respawn_x + 120:
                    tape.clear_overlay()
            else:
                # Return to normal play mode
                tape.feed = self._feed_cache
                self.mode = 0#Play
                tape.write(1, "DONT GIVE UP!", tape.midx[0]+5, 26)

        # Testing mode
        else:
            # Explore the level by flying, free of interaction
            if not bU():
                self._y_pos -= 1
            elif not bD():
                self._y_pos += 1
            if not bL():
                self._x_pos -= 1
            elif not bR():
                self._x_pos += 1



        # TODO: fall off tape: fix death message display
        # TODO: allow digging straight down
        # TODO: climb
        # TODO: jump
        # TODO: hit ceiling


        # Update the viper friendly variables.
        self.x_pos = int(self._x_pos)
        self.y_pos = int(self._y_pos)

    @micropython.viper
    def draw(self, t: int, x: int, stage):
        """ Draw umby to the draw buffer """
        x_pos = int(self.x_pos)
        y_pos = int(self.y_pos)
        # Get animation frame
        # Steps through 0,1,2,3 every half second for animation
        # of looking left and right, and changes to movement art of
        # 4 when moving left and 5 when moving right.
        f = 4 if not bL() else 5 if not bR() else t*2 // _FPS % 4
        # 0 when still, 1 when left moving, 2 when right
        fm = 1 if not bL() else 2 if not bR() else 0
        # Draw the layers and masks
        stage.draw(0, x_pos-1-x, y_pos-6, self._sdw, 3, f)
        stage.draw(1, x_pos-1-x, y_pos-6, self._art, 3, f)
        stage.mask(0, x_pos-4-x, y_pos-6, self._back_mask, 9, 0)
        stage.mask(1, x_pos-1-x, y_pos-6, self._fore_mask, 3, fm)


## Game Engine ##

def set_level(tape, start):
    """ Prepare everything for a level of gameplay including
    the starting tape, and the feed patterns for each layer.
    @param start: The starting x position of the tape.
    """
    # Set the feed patterns for each layer.
    # (back, mid-back, mid-back-fill, foreground, foreground-fill)
    # Fill the tape with the starting area
    tape.feed[:] = [pattern_wall,
        pattern_fence, pattern_fill,
        pattern_room, pattern_fill]
    tape.scroll_tape(start-72, start-72, start-72)
    for i in range(72):
        tape.scroll_tape(1, 1, 1)
    # Draw starting instructions
    tape.write(1, "THAT WAY!", start+19, 26)
    tape.write(1, "------>", start+37, 32)
    # Ready tape for main area
    tape.feed[:] = [pattern_toplit_wall,
        pattern_stalagmites, pattern_stalagmites_fill,
        pattern_cave, pattern_cave_fill]

@micropython.native
def run_game():
    """ Initialise the game and run the game loop """
    display.setFPS(_FPS)
    tape = Tape()
    stage = Stage()
    start = 3
    set_level(tape, start)
    umby = Umby(start+10, 20)
    #umby.mode = 99 # Testing mode

    # Main gameplay loop
    v = 0
    t = 0;
    profiler = ticks_ms()
    while(1):
        # Speed profiling
        if (t % 60 == 0):
            print(ticks_ms() - profiler)
            profiler = ticks_ms()

        # Update the game engine by a tick
        umby.tick(t, tape)

        # Make the camera follow the action
        tape.auto_camera_parallax(umby.x_pos, umby.y_pos)

        # Update the display buffer new frame data
        stage.clear()
        umby.draw(t, tape.x[0], stage)
        tape.comp(stage.stage)

        # Flush to the display, waiting on the next frame interval
        display.update()
        t += 1
run_game()

