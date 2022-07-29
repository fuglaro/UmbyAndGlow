# Copyright © 2022 John van Leeuwen <jvl@convex.cc>
# Copyright © 2022 Auri <@Auri#8401(Discord)>
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

## Tape Management, Stage, and display ##

from array import array
from machine import Pin, SPI
from time import sleep_ms, ticks_ms

# Font by Auri (@Auri#8401)
_font = (
    bytearray([0,0,0]) # Space needs to be at the start.
    + # Alphabet # BITMAP: width: 78, height: 8
    bytearray([240,72,248,240,168,88,240,136,152,248,136,112,240,168,136,248,40,8,112,136,200,248,64,248,136,248,136,64,136,248,248,96,152,120,136,128,248,56,248,248,8,240,240,136,248,240,72,56,112,200,248,240,72,184,176,168,200,8,248,8,120,128,248,248,192,56,248,224,248,216,96,216,152,160,120,200,168,152])

    + # Numbers # BITMAP: width: 30, height: 8
    bytearray([120,136,240,144,248,192,208,136,176,136,168,88,32,48,248,88,136,104,112,168,200,8,200,56,88,168,208,56,40,240])
    + # Symbols # BITMAP: width: 57, height: 8
    bytearray([184,0,184,16,136,48,216,216,0,152,216,0,0,24,0,24,0,24,128,96,24,136,80,32,32,80,136,240,136,0,0,136,120,112,136,0,0,136,112,192,192,0,128,192,0,32,112,32,80,32,80,32,32,32])
    )
_font_index = " ABCDEFGHIJKLMNOPQRSTUVWXYZ" +"0123456789" +"!?:;'\"/><[]().,+*-"

# Setup basic display access
_FPS = const(60)
from ssd1306 import SSD1306_SPI
display = SSD1306_SPI(72, 40,
    SPI(0, sck=Pin(18), mosi=Pin(19)), dc=Pin(17), res=Pin(20), cs=Pin(16))
EMULATED = "rate" not in dir(display)
_REFRESH = _FPS if EMULATED else _FPS*2 
if EMULATED: # Load the emulator display if using the IDE API
    from thumbyGraphics import display as emu_dpy
    emu_dpy.setFPS(_FPS)
    display_update = emu_dpy.update
    _display_buffer = emu_dpy.display.buffer
else: # Otherwise use the raw one if on the thumby device
    # Load the nice memory-light display drivers
    _display_buffer = display.buffer
    timer = ticks_ms()
    fwait = 1000//_REFRESH
    @micropython.native
    def display_update():
        global timer
        t = ticks_ms()
        nwait = timer - ticks_ms()
        sleep_ms(0 if nwait <= 0 else nwait if nwait < fwait else fwait)
        display.show()
        timer = ticks_ms() + fwait

@micropython.viper
def ihash(x: uint) -> int:
    ### 32 bit deterministic semi-random hash fuction
    # Credit: Thomas Wang
    ###
    x = (x ^ 61) ^ (x >> 16)
    x += (x << 3)
    x ^= (x >> 4)
    x *= 0x27d4eb2d
    return int(x ^ (x >> 15))

class Tape:
    ###
    # Scrolling tape with a fore, mid, and background layer.
    # This represents the level of the ground but doesn't include actors.
    # The foreground is the parts of the level that are interactive with
    # actors such as the ground, roof, and platforms.
    # Mid and background layers are purely decorative.
    # Each layer can be scrolled intependently and then composited onto the
    # display buffer.
    # Each layer is created by providing deterministic functions that
    # draw the pixels from x and y coordinates. Its really just an elaborate
    # graph plotter - a scientific calculator turned games console!
    # The tape size is 64 pixels high, with an infinite length, and 216 pixels
    # wide are buffered (72 pixels before tape position, 72 pixels of visible,
    # screen, and 72 pixels beyond the visible screen).
    # This is intended for the 72x40 pixel view. The view can be moved
    # up and down but when it moves forewards and backwards, the buffer
    # is cycled backwards and forewards. This means that the tape
    # can be modified (such as for explosion damage) for the 64 pixels high,
    # and 216 pixels wide, but when the tape is rolled forewards, and backwards,
    # the columns that go out of buffer are reset.
    # There is also an overlay layer and associated mask, which is not
    # subject to any tape scrolling or vertical offsets.
    # There are also actor stage layers for managing rendering
    # and collision detection of players and monsters.
    ###

    def __init__(self):
        # Scrolling tape with each render layer being a section,
        # one after the other.
        # Each section is a buffer that cycles (via the tape_scroll positions)
        # as the world scrolls horizontally. Each section can scroll
        # independently so background layers can move slower than
        # foreground layers.
        # Layers each have 1 bit per pixel from top left, descending then
        # wrapping to the right.
        # The vertical height is 64 pixels and comprises of 2 ints,
        # each with 32 bits. 
        # Each layer is a layer in the composited render stack.
        # Layers from left to right:
        # - 0: far background
        # - 432: close background
        # - 864: close background fill (opaque: off pixels)
        # - 1296: landscape including ground, platforms, and roof
        # - 1728: landscape fill (opaque: off pixels)
        # - 2160: overlay mask (opaque: off pixels)
        # - 2304: overlay
        self._tape = array('I', (0 for i in range(72*3*2*5+72*2*2)))
        # The scroll distance of each layer in the tape, and then
        # the frame number counter and vertical offset appended on the end.
        # The vertical offset (yPos), cannot be different per layer
        # (horizontal parallax only).
        # [backPos, midPos, frameCounter, forePos, yPos]
        self._tape_scroll = array('i', [0, 0, 0, 0, 0, 0, 0])
        # Public accessible x position of the tape foreground
        # relative to the level.
        # This acts as the camera position across the level.
        # Care must be taken to NOT modify this externally.
        self.x = memoryview(self._tape_scroll)[3:5]
        self.midx = memoryview(self._tape_scroll)[1:2]
        # Alphabet for writing text - 3x5 text size (4x6 with spacing)
        # Custom emojis: @ = Umby and ^ = Glow
        self.abc = _font + bytearray([128,240,48,0,248,192])
        self.abc_i = dict((v, i) for i, v in enumerate(_font_index+"@^"))
        # The patterns to feed into each tape section
        self.feed = [None, None, None, None, None]
    
        # Actor and player management variables
        ### Render and collision detection buffer
        # for all the maps and monsters, and also the players.
        # Monsters and players can be drawn to the buffer one
        # after the other. Collision detection capabilities are
        # very primitive and only allow checking for pixel collisions
        # between what is on the buffer and another provided sprite.
        # The Render buffer is two words (64 pixels) high, and
        # 72 pixels wide for the background and mask layers, and
        # 132 pixels wide (30 pixels extra to the right and left for collision
        # checks) for the primary interactive actor layer.
        # Sprites passed in must be a byte tall,
        # but any width.
        # There are 4 layers on the render buffer, 2 for rendering
        # background and foreground monsters, and 2 for clearing
        # background and foreground environment for monster
        # visibility.
        # Frames for the drawing and checking collisions of all actors.
        # This includes layers for turning on pixels and clearing lower layers.
        # Clear layers have 0 bits for clearing and 1 for passing through.
        # This includes the following layers:
        # - 0: Mid and background clear.
        # - 144: Foreground clear.
        # - 288: Non-interactive background monsters.
        # - 432: Foreground monsters.
        self._stage = array('I', (0 for i in range(72*2*3+132*2)))
        # Monster classes to spawn, with likelihood of each monster class
        # spawning (out of 255), for every 8 steps
        # Set mons_clear and mons_add to set the hooks to the monster manager.
        self.spawner = (bytearray([]), bytearray([]))
        def _pass(*arg):
            pass
        self.mons_clear = _pass
        self.mons_add = _pass
        # How far along the tape spawning has completed
        self._x = array('I', [0])
        self.players = [] # Player register for interactions
        self.clear_overlay()
        self.clear_stage()

    @micropython.viper
    def reset(self, p: int):
        ### Set a new spawn starting position and reset the tape.
        # Also empties out all monsters.
        ###
        self.mons_clear()
        # Scroll each layer
        scroll = ptr32(self._tape_scroll)
        scroll[0] = p//4
        scroll[1] = p//2
        scroll[3] = p
        # Reset the tape buffers for all layers to the
        # given position and fill with the current feed.
        scroll = ptr32(self._tape_scroll)
        for i in range(3):
            layer = 3 if i == 2 else i
            tapePos = scroll[layer]
            for x in range(tapePos-72, tapePos+144):
                self.redraw_tape(i, x, self.feed[layer], self.feed[layer+1])

    @micropython.viper
    def check(self, x: int, y: int, b: int) -> bool:
        ### Returns true if the byte going up from the x, y position is solid
        # foreground where it collides with a given byte.
        # @param b: Collision byte (as an int). All pixels in this vertical
        #     byte will be checked. To check just a single pixel, pass in the
        #     value 128. Additional active bits will be checked going upwards
        #     from themost significant bit/pixel to least significant.
        ###
        if x < -30 or x >= 102:
            return False # Out of buffer range is always False
        stage = ptr32(self._stage)
        p = (x+30)%132*2+432
        h = y - 8 # y position is from bottom of text
        img1 = b >> 0-h if h < 0 else b << h
        img2 = b >> 32-h if h-32 < 0 else b << h-32
        return bool((stage[p] & img1) | stage[p+1] & img2)

    @micropython.viper
    def draw(self, layer: int, x: int, y: int, img: ptr8, w: int, f: int):
        ### Draw a sprite to a render layer.
        # Sprites must be 8 pixels high but can be any width.
        # Sprites can have multiple frames stacked horizontally.
        # There are 2 layers that can be rendered to:
        #     0: Non-interactive background monster layer.
        #     1: Foreground monsters, traps and player.
        # @param layer: (int) the layer to render to.
        # @param x: screen x draw position.
        # @param y: screen y draw position (from top).
        # @param img: (ptr8) sprite to draw (single row VLSB).
        # @param w: width of the sprite to draw.
        # @param f: the frame of the sprite to draw.
        ###
        o = x-f*w
        p = (layer+2)*144 + (60 if layer == 1 else 0)
        r1 = -30 if layer == 1 else 0
        r2 = 101 if layer == 1 else 71
        draw = ptr32(self._stage)
        for i in range(x if x >= r1 else r1, x+w if x+w <= r2 else r2):
            b = uint(img[i-o])
            draw[p+i*2] |= (b << y) if y >= 0 else (b >> 0-y)
            draw[p+i*2+1] |= (b << y-32) if y >= 32 else (b >> 32-y)

    @micropython.viper
    def mask(self, layer: int, x: int, y: int, img: ptr8, w: int, f: int):
        ### Draw a sprite to a mask (clear) layer.
        # This is similar to the "draw" method but applies a mask
        # sprite to a mask later.
        # There are 2 layers that can be rendered to:
        #     0: Mid and background environment mask (1 bit to clear).
        #     1: Foreground environment mask (1 bit to clear).
        ###
        o = x-f*w
        p = layer*144
        draw = ptr32(self._stage)
        for i in range(x if x >= 0 else 0, x+w if x+w < 72 else 71):
            b = uint(img[i-o])
            draw[p+i*2] &= -1 ^ ((b<<y) if y >= 0 else (b>>0-y))
            draw[p+i*2+1] &= -1 ^ ((b<<y-32) if y >= 32 else (b>>32-y))

    @micropython.viper
    def comp(self):
        ### Composite all the render layers together and render directly to
        # the display buffer, taking into account the scroll position of each
        # render layer, and dimming the background layers.
        ###
        tape = ptr32(self._tape)
        scroll = ptr32(self._tape_scroll)
        stg = ptr32(self._stage)
        frame = ptr8(_display_buffer)
        # Obtain and increase the frame counter
        scroll[2] += 1 # Counter
        y_pos = scroll[4]
        # Loop through each column of pixels
        for x in range(72):
            # Compose the first 32 bits vertically.
            p0 = (x+scroll[0])%216*2
            p1 = (x+scroll[1])%216*2
            p3 = (x+scroll[3])%216*2
            # Create a modifier for dimming background layer pixels.
            # The magic number here is repeating on and off bits, which is
            # alternated horizontally and in time. Someone say "time crystal".
            dimshift = (scroll[2]+x+y_pos+p1)%2
            dim = int(1431655765) << dimshift
            # Create darker dimmer for the overlay layer mask
            xdimshift = (scroll[2]+x+y_pos+p1)%8
            xdim = (int(-2004318072) if xdimshift == 0 else
                int(1145324612) if xdimshift == 4 else
                int(572662306) if xdimshift == 2 else
                int(286331153) if xdimshift == 6 else 0)
            x2 = x*2
            overlay_mask = uint(tape[x2+2160] << y_pos)
            a = uint(((
                        # Back/mid layer (with monster mask and fill)
                        ((tape[p0] | tape[p1+432]) & stg[x2]
                            & stg[x2+144] & tape[p1+864] & tape[p3+1728])
                        # Background (non-interactive) monsters
                        | stg[x2+288])
                    # Dim all mid and background layers
                    & dim & overlay_mask
                    # Foreground monsters (and players)
                    | stg[x2+492]
                    # Foreground (with monster mask and fill)
                    | (tape[p3+1296] & stg[x2+144] & tape[p3+1728]))
                # Now apply the overlay mask and draw layers.
                & (overlay_mask | xdim)
                | (tape[x2+2304] << y_pos))
            # Now compose the second 32 bits vertically.
            overlay_mask = uint((uint(tape[x2+2160]) >> 32-y_pos)
                    | (tape[x2+2161] << y_pos))
            b = uint(((
                        # Back/mid layer (with monster mask and fill)
                        ((tape[p0+1] | tape[p1+433]) & stg[x2+1]
                        & stg[x2+145] & tape[p1+865] & tape[p3+1729])
                        # Background (non-interactive) monsters
                        | stg[x2+289])
                    # Dim all mid and background layers
                    & dim & overlay_mask
                    # Foreground monsters (and players)
                    | stg[x2+493]
                    # Foreground (with monster mask and fill)
                    | (tape[p3+1297] & stg[x2+145] & tape[p3+1729]))
                # Now apply the overlay mask and draw layers.
                & (overlay_mask | xdim)
                | (uint(tape[x2+2304]) >> 32-y_pos) | (tape[x2+2305] << y_pos))
            # Apply the relevant pixels to next vertical column of the display
            # buffer, while also accounting for the vertical offset.
            frame[x] = a >> y_pos
            frame[72+x] = (a >> 8 >> y_pos) | (b << (32 - y_pos) >> 8)
            frame[144+x] = (a >> 16 >> y_pos) | (b << (32 - y_pos) >> 16)
            frame[216+x] = (a >> 24 >> y_pos) | (b << (32 - y_pos) >> 24)
            frame[288+x] = b >> y_pos

    @micropython.viper
    def clear_stage(self):
        ### Clear the stage buffers ready for the next frame ###
        # Reset the render and mask laters to their default blank state
        stg = ptr32(self._stage)
        for i in range(288, 696):
            stg[i] = 0
        for i in range(288):
            stg[i] = -1

    @micropython.viper
    def check_tape(self, x: int, y: int) -> bool:
        ### Returns true if the x, y position is solid foreground ###
        tape = ptr32(self._tape)
        p = x%216*2+1296
        return bool(tape[p] & (1 << y) if y < 32 else tape[p+1] & (1 << y-32))
    
    @micropython.viper
    def scroll_tape(self, back_move: int, mid_move: int, fore_move: int):
        ### Scroll the tape one pixel forwards, or backwards for each layer.
        # Updates the tape scroll position of that layer.
        # Fills in the new column with pattern data from the relevant
        # pattern functions. Since this is a rotating buffer, this writes
        # over the column that has been scrolled offscreen.
        # Each layer can be moved in the following directions:
        #     -1 -> rewind layer backwards,
        #     0 -> leave layer unmoved,
        #     1 -> roll layer forwards
        # @param back_move: Movement of the background layer
        # @param mid_move: Movement of the midground layer (with fill)
        # @param fore_move: Movement of the foreground layer (with fill)
        ###
        tape = ptr32(self._tape)
        scroll = ptr32(self._tape_scroll)
        feed = self.feed
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
            pattern = feed[layer]
            tape[offX] = int(pattern(x, 0))
            tape[offX+1] = int(pattern(x, 32))
            if layer != 0:
                fill_pattern = feed[layer + 1]
                tape[offX+432] = int(fill_pattern(x, 0))
                tape[offX+433] = int(fill_pattern(x, 32))
        # Spawn new monsters as needed
        xp = ptr32(self._x)
        p = scroll[3]
        # Only spawn when scrolling into unseen land
        if xp[0] >= p:
            return
        spawner = self.spawner
        rates = ptr8(spawner[1])
        types = ptr8(spawner[0])
        r = int(uint(ihash(p))>>3)
        # Loop through each monster type randomly spawning
        # at the configured rate.
        for i in range(0, int(len(spawner[0]))):
            if r%2057 < rates[i]:
                self.mons_add(types[i], p+72+36, r%64)
            r = r >> 1 # Fast reuse of random number
        xp[0] = p 

    @micropython.viper
    def redraw_tape(self, layer: int, x: int, pattern, fill_pattern):
        ### Updates a tape layer for a given x position
        # (relative to the start of the tape) with a pattern function.
        # This can be used to draw to a layer without scrolling.
        # These layers can be rendered to:
        #     0: Far background layer
        #     1: Mid background layer
        #     2: Foreground layer
        ###
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
        ### Carves a hole out of a tape layer for a given x position
        # (relative to the start of the tape) with a pattern function.
        # Draw layer: 1-leave, 0-carve
        # Fill layer: 0-leave, 1-carve
        # These layers can be rendered to:
        #     0: Far background layer
        #     1: Mid background layer
        #     2: Foreground layer
        ###
        tape = ptr32(self._tape)
        l = 3 if layer == 2 else layer
        p = ptr32(self._tape_scroll)[l]
        if -72 <= x - p < 144:
            offX = l*432 + x%216*2
            tape[offX] &= int(pattern(x, 0))
            tape[offX+1] &= int(pattern(x, 32))
            if l != 0 and fill_pattern:
                tape[offX+432] |= int(fill_pattern(x, 0))
                tape[offX+433] |= int(fill_pattern(x, 32))

    @micropython.viper
    def draw_tape(self, layer: int, x: int, pattern, fill_pattern):
        ### Draws over the top of a tape layer for a given x position
        # (relative to the start of the tape) with a pattern function.
        # This combines the existing layer with the provided pattern.
        # Draw layer: 1-leave, 0-carve
        # Fill layer: 0-leave, 1-carve
        # These layers can be rendered to:
        #     0: Far background layer
        #     1: Mid background layer
        #     2: Foreground layer
        ###
        tape = ptr32(self._tape)
        l = 3 if layer == 2 else layer
        offX = l*432 + x%216*2
        tape[offX] |= int(pattern(x, 0))
        tape[offX+1] |= int(pattern(x, 32))
        if l != 0 and fill_pattern:
            tape[offX+432] &= int(fill_pattern(x, 0))
            tape[offX+433] &= int(fill_pattern(x, 32))
        
    @micropython.viper
    def offset_vertically(self, offset: int):
        ### Shift the view on the tape to a new vertical position, by
        # specifying the offset from the top position. This cannot
        # exceed the total vertical size of the tape (minus the tape height).
        ###
        ptr32(self._tape_scroll)[4] = (
            offset if offset >= 0 else 0) if offset <= 24 else 24

    @micropython.viper
    def auto_camera_parallax(self, x: int, y: int, d: int, t: int):
        ### Move the camera so that an x, y tape position is in the spotlight.
        # This will scroll each tape layer to immitate a camera move and
        # will scroll with standard parallax.
        # This will also respect a direction (d) to (slowly) extend the view
        # of the camera backwards if the player is looking backwards.
        # Time is measured by passing in a tick counter (t).
        ###
        # Get the current camera position
        c = ptr32(self._tape_scroll)[3]
        # Scroll the tapes as needed
        n = (-1 if x < c+10 or (d == -1 and x < c+25 and t%8==0) else
            1 if x > c+40 or (d == 1 and x > c+20 and t%4==0) else 0)
        if n != 0:
            self.scroll_tape(n if c % 4 == 0 else 0, n*(c % 2), n)
        # Reset the vertical offset as needed
        y -= 20
        ptr32(self._tape_scroll)[4] = (y if y >= 0 else 0) if y <= 24 else 24

    @micropython.viper
    def write(self, layer: int, text, x: int, y: int):
        ### Write text to the mid background layer at an x, y tape position.
        # This also clears a space around the text for readability using
        # the background clear mask layer.
        # Text is drawn with the given position being at the botton left
        # of the written text (excluding the mask border).
        # There are 2 layers that can be rendered to:
        #     1: Mid background layer.
        #     3: Overlay layer.
        # When writing to the overlay layer, the positional coordinates
        # should be given relative to the screen, rather than the tape.
        ###
        text = text.upper() # only uppercase is supported
        tape = ptr32(self._tape)
        abc_b = ptr8(self.abc)
        abc_i = self.abc_i
        h = y - 8 # y position is from bottom of text
        # Select the relevant layers
        mask = 864 if layer == 1 else 2160
        draw = 432 if layer == 1 else 2304
        # Clear space on the mask layer
        b = 0xFE
        for i in range(int(len(text))*4+1):
            p = (x-1+i)%216*2+mask
            tape[p] ^= tape[p] & (b >> -1-h if h+1 < 0 else b << h+1)
            tape[p+1] ^= tape[p+1] & (b >> 31-h if h-31 < 0 else b << h-31)
        # Draw to the draw layer
        for i in range(int(len(text))):
            for o in range(3):
                p = (x+o+i*4)%216*2
                b = abc_b[int(abc_i.get(text[i], 0))*3+o]
                img1 = b >> 0-h if h < 0 else b << h
                img2 = b >> 32-h if h-32 < 0 else b << h-32
                # Draw to the draw layer
                tape[p+draw] |= img1
                tape[p+draw+1] |= img2
                # Stencil text out of the clear background mask layer
                tape[p+mask] |= img1
                tape[p+mask+1] |= img2

    @micropython.viper
    def message(self, position: int, text, layer: int):
        ### Write a message to the top (left), center (middle), or
        # bottom (right) of the screen to a specified layer.
        # @position: (int) 0 - center, 1 - top, 2 - bottom.
        # @layer: (int) 1 - mid-background, 3 - overlay
        ###
        # Split the text into lines that fit on screen.
        lines = [""]
        for word in text.split(' '):
            lenn = int(len(lines[-1]))
            if (lenn + int(len(word)) + 1)*4 > 72 or word=="\n":
                if lenn and lenn*4 < 72 and position:
                    # Add space after line for legibility
                    lines[-1] += " "
                lines.append("")
            if word == "\n":
                continue
            lines[-1] += (" " if lines[-1] else "") + word
        lenn = int(len(lines[-1]))
        if lenn and lenn*4 < 72 and position:
            # Add space after line for legibility
            lines[-1] += " "
        # Draw centered (if applicable)
        leng = int(len(lines))
        if position == 0:
            x = 36
            y = 25-leng*3
            if layer == 1:
                x += ptr32(self._tape_scroll)[1] + 36
                y += 10
            for i in range(leng):
                line = lines[i]
                if line:
                    self.write(layer, line, x-(int(len(line))*2), y)
                y += 6
        else:
            # Draw top (if applicable)
            if position == 1:
                y = 5
            # Draw bottom (if applicable)
            if position == 2:
                y = 46 - 6*leng
            for i in range(leng):
                self.write(layer, lines[i], 0, y)
                y += 6

    @micropython.viper
    def tag(self, text, x: int, y: int):
        ### Write text to the mid background layer centered
        # on the given tape foreground scoll position.
        ###
        scroll = ptr32(self._tape_scroll)
        p = x-scroll[3]+scroll[1] # Translate position to mid background
        self.write(1, text, p-int(len(text))*2, y+3)

    @micropython.viper
    def clear_overlay(self):
        ### Reset and clear the overlay layer and it's mask layer. ###
        tape = ptr32(self._tape)
        # Reset the overlay mask layer
        for i in range(2160, 2304):
            tape[i] = -1
        # Reset and clear the overlay layer
        for i in range(2304, 2448):
            tape[i] = 0
