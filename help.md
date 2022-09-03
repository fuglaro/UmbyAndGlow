## Files and API Docs

### Games/Umby&Glow/Umby&Glow.py

Game loading screen and setup.

Main entry point to the program, this shows a loading screen while the game loads (thanks to Doogle!).

This is also a useful place to place testing code for fast testing and development. Place the following code into this file before the title screen is loaded to perform specific tests.

#### Pattern Testing

View patterns easily for quick iteration of level design.

```python
from utils import *
from array import array
_buf = array('l', [0, 0, 0, 0, 0, 0, 0, 0])
with open("/Games/Umby&Glow/world6.py") as fp:
    exec(fp.read())
from tape import Tape, display_update
tape = Tape()
tape.feed = [w.pattern_biomechanical_hall_wall,w.pattern_alien_totem_plants,pattern_fill,w.pattern_alien_totem_floor,pattern_fill]
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
from monsters import *
with open("/Games/Umby&Glow/script.txt") as fp:
    for ln, line in enumerate(fp):
        if line and line[0] != "#" and line[0] != "\n":
            dist, _, ev_str = line.partition(",")
            try:
                int(dist), eval(ev_str.strip())
            except (SyntaxError, ValueError):
                print(ln+1, line)
                raise
```

### Games/Umby&Glow/game.py

Game Play including main loop

```
def load_save(sav, load):
    ''' Load the progress from the file "sav" if "load" is True '''

def run_menu():
    ''' Loads a starting menu and returns the selections.
    @returns: a tuple of the following values:
        * Umby (0), Glow (1)
        * 1P (0), 2P (1)
        * Player start location
    '''
```

### Games/Umby&Glow/tape.py

Tape Management, Stage, and display

```
def _gen_bang(blast_x, blast_y, blast_size, invert):
    ''' PATTERN (DYNAMIC) [bang]: explosion blast pattern generator
    with customisable position and size.
    Intended to be used for scratch_tape.
    Comes with it's own inbuilt fill patter for also blasting away
    the fill layer.
    @returns: a pattern (or fill) function.
    '''

class Tape:
    '''
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
    There are also actor stage layers for managing rendering
    and collision detection of players and monsters.
    '''

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
    _tape

    # The scroll distance of each layer in the tape, and then
    # the frame number counter and vertical offset appended on the end.
    # The vertical offset (yPos), cannot be different per layer
    # (horizontal parallax only).
    # [backPos, midPos, frameCounter, forePos, yPos]
    _tape_scroll

    # Public accessible x position of the tape foreground
    # relative to the level.
    # This acts as the camera position across the level.
    # Care must be taken to NOT modify this externally.
    x
    midx
    bx

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
    _stage

    # Monster classes to spawn, with likelihood of each monster class
    # spawning (out of 255), for every 8 steps
    # Set mons_clear and mons_add to set the hooks to the monster manager.
    spawner

    def reset(self, p: int):
        ''' Set a new spawn starting position and reset the tape.
        Also empties out all monsters.
        '''

    def check(self, x: int, y: int, b: int) -> bool:
        ''' Returns true if the byte going up from the x, y position is solid
        foreground where it collides with a given byte.
        @param b: Collision byte (as an int). All pixels in this vertical
            byte will be checked. To check just a single pixel, pass in the
            value 128. Additional active bits will be checked going upwards
            from themost significant bit/pixel to least significant.
        '''

    def draw(self, layer: int, x: int, y: int, img: ptr8, w: int, f: int):
        ''' Draw a sprite to a render layer.
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
        '''

    def mask(self, layer: int, x: int, y: int, img: ptr8, w: int, f: int):
        ''' Draw a sprite to a mask (clear) layer.
        This is similar to the "draw" method but applies a mask
        sprite to a mask later.
        There are 2 layers that can be rendered to:
            0: Mid and background environment mask (1 bit to clear).
            1: Foreground environment mask (1 bit to clear).
        '''

    def comp(self):
        ''' Composite all the render layers together and render directly to
        the display buffer, taking into account the scroll position of each
        render layer, and dimming the background layers.
        '''

    def clear_stage(self):
        ''' Clear the stage buffers ready for the next frame ###
        Reset the render and mask laters to their default blank state
        '''

    def check_tape(self, x: int, y: int) -> bool:
        ''' Returns true if the x, y position is solid foreground '''

    def scroll_tape(self, back_move: int, mid_move: int, fore_move: int):
        ''' Scroll the tape one pixel forwards, or backwards for each layer.
        Updates the tape scroll position of that layer.
        Fills in the new column with pattern data from the relevant
        Each layer can be moved in the following directions:
            -1 -> rewind layer backwards,
            0 -> leave layer unmoved,
            1 -> roll layer forwards
        @param back_move: Movement of the background layer
        @param mid_move: Movement of the midground layer (with fill)
        @param fore_move: Movement of the foreground layer (with fill)
        '''

    def redraw_tape(self, layer: int, x: int, pattern, fill_pattern):
        ''' Updates a tape layer for a given x position
        (relative to the start of the tape) with a pattern function.
        This can be used to draw to a layer without scrolling.
        These layers can be rendered to:
            0: Far background layer
            1: Mid background layer
            2: Foreground layer
        '''

    def scratch_tape(self, layer: int, x: int, pattern, fill_pattern):
        ''' Carves a hole out of a tape layer for a given x position
        (relative to the start of the tape) with a pattern function.
        Draw layer: 1-leave, 0-carve
        Fill layer: 0-leave, 1-carve
        These layers can be rendered to:
            0: Far background layer
            1: Mid background layer
            2: Foreground layer
        '''

    def draw_tape(self, layer: int, x: int, pattern, fill_pattern):
        ''' Draws over the top of a tape layer for a given x position
        (relative to the start of the tape) with a pattern function.
        This combines the existing layer with the provided pattern.
        Draw layer: 1-leave, 0-carve
        Fill layer: 0-leave, 1-carve
        These layers can be rendered to:
            0: Far background layer
            1: Mid background layer
            2: Foreground layer
        '''

    def offset_vertically(self, offset: int):
        ''' Shift the view on the tape to a new vertical position, by
        specifying the offset from the top position. This cannot
        exceed the total vertical size of the tape (minus the tape height).
        '''

    def auto_camera(self, x: int, y: int, d: int, t: int):
        ''' Move the camera so that an x, y tape position is in the spotlight.
        This will scroll each tape layer to immitate a camera move and
        will scroll with standard parallax.
        This will also respect a direction (d) to (slowly) extend the view
        of the camera backwards if the player is looking backwards.
        Time is measured by passing in a tick counter (t).
        '''

    def write(self, layer: int, text, x: int, y: int):
        ''' Write text to the mid background layer at an x, y tape position.
        This also clears a space around the text for readability using
        the background clear mask layer.
        Text is drawn with the given position being at the botton left
        of the written text (excluding the mask border).
        There are 2 layers that can be rendered to:
            1: Mid background layer.
            3: Overlay layer.
        When writing to the overlay layer, the positional coordinates
        should be given relative to the screen, rather than the tape.
        '''

    def message(self, position: int, text, layer: int):
        ''' Write a message to the top (left), center (middle), or
        bottom (right) of the screen to a specified layer.
        @position: (int) 0 - center, 1 - top, 2 - bottom.
        @layer: (int) 1 - mid-background, 3 - overlay
        '''

    def tag(self, text, x: int, y: int):
        ''' Write text to the mid background layer centered
        on the given tape foreground scoll position.
        '''

    def blast(self, t: int, x: int, y: int):
        ''' Make explosion by scratching a circle from the foreground,
        and tagging a <KABLAM!> style message on the mid background.
        '''

    def clear_overlay(self):
        ''' Reset and clear the overlay layer and it's mask layer. '''
```

### Games/Umby&Glow/players.py

Platers, AI, and Input controls

```python
def _draw_trail(draw_func, x, y, rdir):
    ''' Leave a rocket trail behind a position '''

class Player:
    ''' Umby and Glow

    Umby: One of the players you can play with.
    Activate by creating object with name == "Umby"
    Umby is an earth worm. They can jump, aim, and fire rockets.
    Umby can also make platforms by releasing rocket trails.
    Monsters, traps, and falling offscreen will kill them.
    Hitting their head on a platform or a roof, while jumping, will
    also kill them.
    Umby's rockets start with aiming a target, then the launch
    process begins and charges up. When the button is then
    released the rocket launches. When the rocket hits the
    ground it clears a blast radius, or kills Umby, if hit.
    During flight, further presses of the rocket button
    will leave a rocket trail that will act as a platform.

    Glow: One of the players you can play with.
    Activate by creating object with name == "Glow"
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
    Glow's rockets start with aiming a target, then the launch
    process begins and charges up. When the button is then
    released the rocket launches. When the rocket hits the
    ground it clears a blast radius, or kills Glow, if hit.
    See the class doc strings for more details.

    Clip: Secret test mode you can play with.
    Invincible orb that can float anywhere and then
    transform into Umby or Glow (name will stay as "Clip")
    Activate by creating object with name == "Cli
    '''
    # Modes:
    #     199: Testing (Clip)
    #     200: Frozen (immune)
    #     201: Respawning to Umby
    #     202: Respawning to Glow
    # ----0-9: Umby modes----
    #       0: Crawling (along ground)
    # --10-19: Glow modes----
    #      11: Swinging from grapple
    #      12: Clinging (from ceiling)
    mode

    def port_out(self, buf: ptr8):
        ''' Dump player data to the output buffer for sending to player 2 '''

    def port_in(self, buf: ptr8) -> int:
        ''' Unpack player data from input buffer recieved from player 2,
        returning the other player's tape position
        '''
    def immune(self) -> int:
        ''' Returns if Umby is in a mode that can't be killed,
        or killed by this engine.
        '''

    def die(self, death_message, respawn=None):
        ''' Start respawn sequence.
        Puts the player into a respawning state.
        @param death_message: message to display
        @param respawn: respawn point to move to, or default (1px=256)
        '''

    def detonate(self, t):
        ''' Explode the rocket, also carving space out of the ground. '''

    def tick(self, t: int):
        ''' Updated Player for one game tick.
        @param t: the current game tick count
        '''

    def _tick_play_ground(self, t: int):
        ''' Handle one game tick for ground play controls '''
```

### Games/Umby&Glow/script.py

Script Loading and Level Progression

```python
# Simple pattern cache used across the writing of a single column of the tape.
# Since the tape patterns must be stateless across columns (for rewinding), this
# should not store data across columns.
_buf

def _script():
    ''' Returns iterator that feeds out script events '''

def get_chapters():
    ''' Return the chapters and their starting positions '''

def story_jump(tape, mons, start, lobby):
    ''' Prepare everything for the level of gameplay
    at the given position including the story position,
    the feed patterns for each layer, and the monster spawner.
    Note this can only jump forwards in the script.
    @param tape: The tape to manipulate.
    @param start: The starting x position of the tape.
    @param lobby: Whether to draw the starting platform
    '''

def add_dialog(tape, dialog):
    ''' Say dialog or narration '''

def story_events(tape, mons, coop_px):
    ''' Update story events including dialog and level type changes.
    Update to the new px tape position.
    @param coop_px: furthest tape scroll of both players
    '''
```

### Games/Umby&Glow/monsters.py

Monster types including their AI

All monsters will die if they go offscreen to the left + 72 pixels but
some monsters have avoidance tactics.

```python
# Additional hidden bahaviour state for all monsters,
# (not to be used for draw behavior as it won't propagate to coop)
_data

class Monsters:
    ''' Engine for all the different monsters '''

    def port_out(self, buf: ptr8):
        ''' Dump monster data to the output buffer for sending to player 2 '''

    def port_in(self, buf: ptr8):
        ''' Unpack monster data from input buffer recieved from player 2 '''

    def is_alive(self, mon):
        ''' Check if a specific monster is alive '''


    def add(self, mon_type: int, x: int, y: int) -> int:
        ''' Add a monster of the given type.
        @returns: the index of the spawned monster, or -1
        '''

    def clear(self):
        ''' Remove all monsters '''

    def tick(self, t: int):
        ''' Update Monster dynamics one game tick for all monsters '''

    def draw_and_check_death(self, t: int, p1, p2):
        ''' Draw all the monsters checking for collisions '''

```

#### BackBones

Like bones, but just flies around safely in the background.

#### Bones

Bones is a monster that flyes about then charges the player.
Bones looks a bit like a skull.
It will fly in a random direction, in a janky jaggard manner,
until it hits a wall in which case
it will change direction again. There is a small chance that
Bones will fly over walls and ground and Bones will continue until
surfacing. If Bones goes offscreen to the left + 72 pixels, it will die;
offscreen to the top or bottom, it will change direction.
It will also change direction on occasion.
When the player is within a short range, Bones will charge the player
and will not stop.
* janky movement mostly avoiding walls,
* some move faster than others, some with no movement (until in range)
* switching to charging behavior when player in range

#### BonesBoss

Main monster of the Boss Bones swarm.

Generates a swarm of Bones' around it.
* Moves slowly towards 10px to the left of the last Bones
* Spawns 20 Bones quickly
* Spawns up to 10 Bones slowly
* Rallies all Bones in the 30 pixel range to the left

#### ChargingBones

Bones when it is actively charging the player.
ChargingBonesFriend is when it is charing the other player.

#### DragonBones

Head monster of the Dragon Bones chain.

Big dragon with lots of tail sections that follow the main
DragonBones monster.
Dragon with a bones head, and a chain of Pillar tails,
Also shoots fireballs

#### E-Falcon

Small space ship that flies in from the right, dodging and shooting
dual lazers.
E Falcon behavior: flying around on the right shooting dual lazers.

### Fireball

Projectile that is launched from DragonBones and Molaar.

#### Hoot

Owl that lurks in the forest, blinks, and swoops on occasion.

#### Lazer

Thin projectile lazer launched from E-Falcon.

#### LeftDoor

Left door of the rocket ship, and the hidden controller
that manages the rocket countdown and launch sequence.

#### Molaar

Crawls around edges of land, shooting fireballs

Molaar is a pillar-head style land crawler but only goes
counter-clockwise (around land), and also jumps high on flat surfaces.
Jump direction is randomly forwards or backwards.
Also turns downwards if roof crawling and goes offscreen to the right.
Made of head, feet and tail. Middle of feet is the center of the monster.
Head shifts relative to feet based on direction, and the head shifts
When charging to shoot left. Also has tail that moves up when standing or
Jumping, and down when climbing or clinging.

#### Pillar

Forest caterpillar. Crawls with a catepillar-chain around edges of
land/foreground.

#### Prober

Alien brain sucker (turns in to Monster *Probing* during brain drain).
Cephalopod - background flies then hovers and brain probes.
Flies in the background until hovering near worm,
above or below depending on worm position, and to the right slightly,
then in a short time snaps out a brain probe!

#### Skittle

Alien bug that flies straight in from the right towards the player.

#### Stomper

Alien trap that goes up then down vertically over set intervals.

### Games/Umby&Glow/script.txt

Story and script data file which manages all level progression.

Script - the story through the dialog of the characters.
Script data includes the (additive) tape scroll amount for when
each line of the script occurs and the dialog itself.
Each entry is usually one line of dialog, but can also include naration
or other messaging, or even level details. Each line of script
includes a prefix indicating the character that says the line:
* "@:" -> Umby says this (overlay at bottom of screen)
* "^:" -> Glow says this (overlay at top of screen)
* "" (no prefix) -> Narration (written to middle of background)

 The script can also include level changes which takes the form of a
 tuple with the following form:
```python
    (feed, spawner, mode)
```
E.g:
```python
    # Level: Cave filled with Bones
    ("4", # World number 4
     # (back, mid-back, mid-back-fill, foreground, foreground-fill)
     "[w.pattern_toplit_wall,
       w.pattern_stalagmites, w.pattern_stalagmites_fill,
       w.pattern_cave, w.pattern_cave_fill]",
     # Reset monster spawner to the new level
     (bytearray([Bones]), bytearray([200])),
     # Player environment dynamics behavior (0-normal, 1-sace))
     0
    )
```
Or as a number, which will load the relevant monster directly.

### Games/Umby&Glow/comms.py

2 player network communication

```
def comms():
    ''' Communicate with the other Thumby.
    Each call might not complete a full message and might instead
    only recieve some bytes. This will send the inbuf
    if it is this Thumby's turn to send, otherwise it will receive
    data into the outbuf. This will only recieve a message after
    trying to send a message. If the communication channel is not
    responsive, this will attempt to reattemp sending data once
    every 60 calls.
    @returns: True if a complete message was just recieved
    '''
```

### Games/Umby&Glow/audio.py

Audio engine and sound effects

Audio sound effects are made with mathematical functions that accept
a time value, and outputs a frequency.

```python
def audio_tick():
    ''' Update the audio frequency for the next tick '''

def play(sound, duration, no_interupt=False):
    ''' Play a sound for the given duration,
    calling audio_tick at the rate you want the sound to change.
    '''

## Sound effects ##

def rocket_flight(t: int):
    ''' Sound signal for rocket flight.
    Ideal duration is 180
    '''

def rocket_bang(t: int):
    ''' Sound signal for rocket explosion.
    Ideal duration is 40
    '''

def rocket_kill(t: int):
    ''' Sound signal for rocket explosion and killing a monster.
    Ideal duration is 30
    '''

def worm_jump(t: int):
    ''' Sound signal for Umby's jump.
    Ideal duration is 15
    '''

def grapple_launch(t: int):
    ''' Sound signal for Glow launching their grapple hook.
    Ideal duration is 15
    '''

def death(t: int):
    ''' Sound signal for either worm dying.
    Ideal duration is 240
    '''
```

### Games/Umby&Glow/utils.py

Maths utility functions and common use patterns

```python
def abs(v: int) -> int:
    ''' Fast bitwise abs '''

def ihash(x: uint) -> int:
    ''' 32 bit deterministic semi-random hash fuction
    Credit: Thomas Wang
    '''

def shash(x: int, step: int, size: int) -> int:
    ''' (smooth) deterministic semi-random hash.
    For x, this will get two random values, one for the nearest
    interval of 'step' before x, and one for the nearest interval
    of 'step' after x. The result will be the interpolation between
    the two random values for where x is positioned along the step.
    @param x: the position to retrieve the interpolated random value.
    @param step: the interval between random samples.
    @param size: the maximum magnitude of the random values.
    '''

def fsqrt(v: int) -> int:
    ''' fast approximate sqrt '''

# Fast sine and cos lookup table.
# If angle is in radians*65536, then use as follows:
#     sin = (sinco[(a//1024+200)%400]-128)//128
#     cos = (sinco[(a//1024-100)%400]-128)//128
sinco
```

## Patterns

The levels of Umby and Glow are all generated with mathematical functions similar to using a graphing calculator. These functions are all refered to as *patterns*.

Patterns are a collection of mathematical, and logical functions
that deterministically draw columns of the tape as it rolls in
either direction. This enables the procedural creation of levels,
but is really just a good way to get richness cheaply on this
beautiful little piece of hardware.

All pattern functions are called twice for each column of pixels
on each tape layer (or mask layer). The first call returns the
black(0) or white(1) pixel values for the top 32 pixels (as a 32 bit int),
and the second call returns the bottom 32 pixels. Since each
tape layer has a mask layer, some functions (which take advantage
of a mask pattern) come with an associated fill pattern. Fill patterns for
the mask layers return black(0) or transparent(1) values. Transparency
will show the white pixels of the associated layer and also other
background layers.
The two calls to each layer, and the calls to the mask layer are guaranteed
to happen subsequently, and there is a \_buf global variable to store
persistent static variables across function calls for the same pattern and
fill. This allows for optimisation of expensive operations for all pixels
and transparency values of a column of pixels on the same tape layer.
Pattens functions take two arguments:
* x: tape position horizontally to calculate column of pixels
* oY (yOrigin): top vertical position of the requested 32 bits (0 or 32).

Most patterns are dynamically loaded from `world*.py` files as the game
progresses.

### Pattern Descriptions

#### alien_totem_floor

Floor and roofing matching the style of alien_totem_plants.

#### alien_totem_plants

Garden of alien plants good for mid background

#### alien_vents

Horizontal straight lines stacked on each other with a thicher
section on top and bottom. 4 height lines, with 6 height gaps.
Comes with an associated alient_vent_decay fill pattern to
give organic texture.

#### biomechanical_hall_wall

Alien background wall with repetative feel.

#### boimechanical_lab

Alien spaceship room with random platforms that comes with an
associated fill pattern that gives and organic texture.

#### cave

Cave system with ceiling and ground. Ceiling is never less
than 5 deep. Both have a random terrain and can intersect.
Comes with an associated fill pattern that makes the ceiling
seem semi-reflective and gives the ground vertical line shading.

#### chain_link_fence

A chain link fence on bottom half with bar across the top, and posts.

#### cloudy_plains

Puffy clouds with fairly-flat ground (foreground).

#### cloudy_snowy_mountains

Distant snowy mountains background with clouds.

#### door

Low height flat tunnel.

#### fence_top

A 4 pixel thick horizontal line that matches the top of chain_link_fence.

#### ferns

Midbackground jungle-fern ground cover.
Also comes with ferns_fill which just has thinker leaves.

#### forest

Forest foreground including trees, ferns, and vines.
Comes with an associated fill pattern.

#### forest_ferns

Midbackground jungle-fern ground cover. Comes with an associated fill layer
that just has thicker leaves.

#### hull

Alien ship exterior wall.

#### launch_area

Rocket ship launching area (surrounding area).
High flat ground with boxes and hanging platforms.
Comes with an associated full pattern which includes box decoration,
box shadows, and ground pattern

#### launch_back

Distant background boxes and rockets.

#### launch_pad

Similar to launch_area but no boxes and no crane platform variance.

#### mid_forest

Dense trees and high ground fern cover. Intended for mid background layer.
Includes trees, ferns, and rays of sunlight.
Comes with an associated fill pattern which cuts out trees and ferns,
and also gives trees shadows, and adds shadow fern patterns.

#### nebula

Lightly scattered and clustered stars.

#### orbitals

Randomised planets and moons. Comes with an associated orbitals_fill pattern.

#### stalagmites

Stalagmite columns coming from the ground and associated
stalactite columns hanging from the ceiling.
These undulate in height in clustered waves.
Comes with an associated fill pattern.
Stalagmites are shaded in a symetric manner while
stalactites have shadows to the left. This is just for visual richness.

#### toplit_wall

Organic background with roof shine.

#### tree_branches

Forest tree top branches (foreground closed ceiling). Comes with an associated
fill pattern.

#### tree_wall

Background of dense forest.

#### tunnel

Thin tunnel a little bit bigger than worm height, that rolls up and down.

#### windows

Background wall with square windows with rounded corners.

### Example Pattern Library

Here are some interesting patterns:

```
@micropython.viper
def pattern_template(x: int, oY: int) -> int:
    ### PATTERN [template]: Template for patterns. Not intended for use. ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            1 # pattern (1=lit pixel, for fill layer, 0=clear pixel)
        ) << (y-oY)
    return v

@micropython.viper
def pattern_fence(x: int, oY: int) -> int:
    ### PATTERN [fence]: - basic dotted fences at roof and high floor ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            (1 if y<12 else 1 if y>32 else 0) & int(x%10 == 0) & int(y%2 == 0)
        ) << (y-oY)
    return v

@micropython.viper
def pattern_test(x: int, oY: int) -> int:
    ### PATTERN [test]: long slope plus walls ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(x%120 == y*3) | (int(x%12 == 0) & int(y%2 == 0))
        ) << (y-oY)
    return v

@micropython.viper
def pattern_wall(x: int, oY: int) -> int:
    ### PATTERN [wall]: dotted vertical lines repeating ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(x%16 == 0) & int(y%3 == 0)
         ) << (y-oY)
    return v

@micropython.viper
def pattern_toothsaw(x: int, y: int) -> int:
    ### PATTERN [toothsaw]: TODO use and update for word ###
    return int(y > (113111^x+11) % 64 // 2 + 24)

@micropython.viper
def pattern_revtoothsaw(x: int, y: int) -> int:
    ### PATTERN [revtoothsaw]: TODO use and update for word ###
    return int(y > (11313321^x) % 64)

@micropython.viper
def pattern_diamondsaw(x: int, y: int) -> int:
    ### PATTERN [diamondsaw]: TODO use and update for word ###
    return int(y > (32423421^x) % 64)


@micropython.viper
def pattern_zebra_hills(x: int, oY: int) -> int:
    ### PATTERN [zebra_hills]: Hills with internal zebra pattern ###
    buff = ptr32(_buf)
    if oY == 0:
        buff[0] = int(shash(x,128,40)) + int(shash(x,16,16)) + int(shash(x,4,4))
    v = 0
    for y in range(oY, oY+32):
        v |= (
            (int(y > (32423421^(x*(y-buff[0])))%32) if y > buff[0] + 4
                else 1 if y > buff[0] else 0)
         ) << (y-oY)
    return v

@micropython.viper
def pattern_fallen_tree(x: int, oY: int) -> int:
    ### PATTERN [fallentree]: TODO use  ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(y > (32423421^(x+y)) % 64)
        ) << (y-oY)
    return v

@micropython.viper
def pattern_vine_hang(x: int, oY: int) -> int:
    ### PATTERN [panels]: TODO use ###
    u = int(shash(x,12,40)) + int(shash(x,5,8))
    v = 0
    for y in range(oY, oY+32):
        v |= (
            1 if   (y)%((u)%10+5) < u//8-y//16 else 0
        ) << (y-oY)
    return v

@micropython.viper
def pattern_panels(x: int, oY: int) -> int:
    ### PATTERN [panels]: TODO use ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            1 if (x*y)%100 == 0 else 0
        ) << (y-oY)
    return v

@micropython.viper
def pattern_quilted_diodes(x: int, oY: int) -> int:
    ### PATTERN [quilted_diodes]: mix between electronics and fabric.
    # Looks like it is ihe insides of a woven computer.
    ###
    snco = ptr32(sinco) # Note we (dangerously) use a bytearray as an int array

    sf = 100 # size factor
    xm = sf*12//10 # sector
    x = x%xm-xm//2

    v = 0
    for ya in range(oY, oY+32):

        y = ya*int(abs(x//100))

        p1 = -1 if snco[(x^y)%99+1]<128 else 0
        p2 = -1 if snco[(x*2^y*2)%99+1]<128 else 0
        p3 = -1 if snco[(x*4^y*4)%99+1]<128 else 0
        p4 = -1 if snco[(x*8^y*8)%99+1]<128 else 0
        v |= (
           0 if (p1^p2^p3^p4) else 1
        ) << (ya-oY)
    return v

@micropython.viper
def pattern_catheral(x: int, oY: int) -> int:
    ### PATTERN [cathedral]: Cathedral style repetative background wall ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(y > (32423421^(y-x*y)) % 64)
        ) << (y-oY)
    return v
```
