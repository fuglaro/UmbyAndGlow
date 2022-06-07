# Copyright © 2022 John van Leeuwen <jvl@convex.cc>
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

###
### # TODO turn story into script and delete.
###
#
#1 - player can switch characters (hold both buttons)
#2 - 2 players connect if devices have different characters
#
#Umby and Glow save their cave.
#
#1.1) Umby, Glow in cave, with monsters and traps being about.
#1.2) Umby and Glow find monsters have infiltrated their cave.
#1.3) They suspect it is Lung.
#1.4) They decide to find out where they have come from.
#1.5) They leave their cave.
#
#Suspect bad worm
#Follow monsters to alien spaceship
#Find Lung held hostage
#Lung gives info as sacrifice (he will be flooded out - no time to save)
#Flood spaceship mainframe
#Go back home
#Cave -> forest -> air -> rocket -> space -> spaceship ->
#    spaceship computer mainframe -> dolphin aquarium ->
#    flooded spaceship -> forrest -> cave
###

import gc # TODO
gc.collect()
print(gc.mem_alloc(), gc.mem_free()) # TODO


##
# Script - the story through the dialog of the characters.
script = [
]

_FPS = const(60) # FPS (intended to be 60 fps) - increase to speed profile

from array import array
from time import sleep_ms, ticks_ms
from machine import Pin
from math import sin, cos, sqrt
print(gc.mem_alloc(), gc.mem_free()) # TODO
# TODO from thumby import display
gc.collect()
print(gc.mem_alloc(), gc.mem_free()) # TODO

# Button functions. Note they return the inverse pressed state
bU = Pin(4, Pin.IN, Pin.PULL_UP).value
bD = Pin(6, Pin.IN, Pin.PULL_UP).value
bL = Pin(3, Pin.IN, Pin.PULL_UP).value
bR = Pin(5, Pin.IN, Pin.PULL_UP).value
bB = Pin(24, Pin.IN, Pin.PULL_UP).value
bA = Pin(27, Pin.IN, Pin.PULL_UP).value

# TODO: mem-opt with const?


from sys import path
path.append("/Games/Umby&Glow")
from tape import Tape, display_update, ihash





gc.collect()
print(gc.mem_alloc(), gc.mem_free()) # TODO

tape = Tape()


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

# Utility functions

@micropython.viper
def abs(v: int) -> int:
    ### Fast bitwise abs ###
    m = v >> 31
    return (v + m) ^ m

@micropython.viper
def shash(x: int, step: int, size: int) -> int:
    ### (smooth) deterministic semi-random hash.
    # For x, this will get two random values, one for the nearest
    # interval of 'step' before x, and one for the nearest interval
    # of 'step' after x. The result will be the interpolation between
    # the two random values for where x is positioned along the step.
    # @param x: the position to retrieve the interpolated random value.
    # @param step: the interval between random samples.
    # @param size: the maximum magnitude of the random values.
    ###
    a = int(ihash(x//step)) % size
    b = int(ihash(x//step + 1)) % size
    return a + (b-a) * (x%step) // step

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
def pattern_none(x: int, oY: int) -> int:
    ### PATTERN [none]: empty ###
    return 0

@micropython.viper
def pattern_fill(x: int, oY: int) -> int:
    ### PATTERN [fill]: completely filled ###
    return int(0xFFFFFFFF) # 1 for all bits

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
def pattern_room(x: int, oY: int) -> int:
    ### PATTERN [room]:- basic flat roof and high floor ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            1 if y < 3 else 1 if y > 37 else 0
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
def pattern_cave(x: int, oY: int) -> int:
    ### PATTERN [cave]:
    # Cave system with ceiling and ground. Ceiling is never less
    # than 5 deep. Both have a random terrain and can intersect.
    ###
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
    ### PATTERN [cave_fill]:
    # Fill pattern for the cave. The ceiling is semi-reflective
    # at the plane at depth 5. The ground has vertical lines.
    ###
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
    ### PATTERN [stalagmites]:
    # Stalagmite columns coming from the ground and associated
    # stalactite columns hanging from the ceiling.
    # These undulate in height in clustered waves.
    ###
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
    ### PATTERN [stalagmites_fill]:
    # Associated shading pattern for the stalagmite layer.
    # Stalagmites are shaded in a symetric manner while
    # stalactites have shadows to the left. This is just for
    # visual richness.
    ###
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
    ### PATTERN [toplit_wall]: organic background with roof shine ###
    v = 0
    p = x-500
    for y in range(oY, oY+32):
        v |= (
            1 if (p*p)%y == 0 else 0
        ) << (y-oY)
    return v

def bang(blast_x, blast_y, blast_size, invert):
    ### PATTERN (DYNAMIC) [bang]: explosion blast with customisable
    # position and size. Intended to be used for scratch_tape.
    # Comes with it's own inbuilt fill patter for also blasting away
    # the fill layer.
    # @returns: a pattern (or fill) function.
    ###
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
def pattern_fallentree(x: int, y: int) -> int:
    ### PATTERN [fallentree]: TODO use and update for word ###
    return int(y > (32423421^(x+y)) % 64)
@micropython.viper
def pattern_panelsv(x: int, oY: int) -> int:
    ### PATTERN [panels]: TODO ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            1 if (x*y)%100 == 0 else 0
        ) << (y-oY)
    return v


## Actors ##

class Player:
    ### Umby or Glow ###
    # Player behavior mode such as Play, Testing, and Respawn
    # BITMAP: width: 9, height: 8
    _back_mask = bytearray([120,254,254,255,255,255,254,254,120])
    # BITMAP: width: 3, height: 8
    _aim = bytearray([64,224,64])
     # BITMAP: width: 3, height: 8
    _aim_fore_mask = bytearray([224,224,224])
    # BITMAP: width: 5, height: 8
    _aim_back_mask = bytearray([112,248,248,248,112])
    mode = 0#Play (normal)
    rocket_x = 0
    rocket_y = 0
    rocket_active = 0

    def die(self, rewind_distance, death_message):
        ### Put Player into a respawning state ###
        self.mode = -1#Respawn
        self._respawn_x = tape.x[0] - rewind_distance
        tape.message(0, death_message)

    @micropython.native
    def kill(self, t, monster):
        ### Explode the rocket, killing the monster or nothing.
        # Also carves space out of the ground.
        ###
        rx = self.rocket_x
        ry = self.rocket_y
        # Tag the wall with an explostion mark
        tag = t%4
        tape.tag("<BANG!>" if tag==0 else "<POW!>" if tag==1 else
            "<WHAM!>" if tag==3 else "<BOOM!>", rx, ry)
        # Tag the wall with a death message
        if monster:
            tape.tag("[RIP]", monster.x, monster.y)
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
        ### Updated Player for one game tick.
        # @param t: the current game tick count
        ###
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
        ### After the player dies, a respawn process begins,
        # showing a death message, while taking Umby back
        # to a respawn point on a new starting platform.
        # This handles a game tick when a respawn process is
        # active.
        ###
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
        ### Handle one game tick for when in test mode.
        # Test mode allows you to explore the level by flying,
        # free of interactions.
        ###
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
    ### One of the players you can play with.
    # Umby is an earth worm. They can jump, aim, and fire rockets.
    # Umby can also make platforms by releasing rocket trails.
    # Monsters, traps, and falling offscreen will kill them.
    # Hitting their head on a platform or a roof, while jumping, will
    # also kill them.
    ###
    # BITMAP: width: 3, height: 8, frames: 6
    _art = bytearray([16,96,0,0,112,0,0,96,16,0,112,0,48,112,64,64,112,48])
    # Umby's shadow
    _sdw = bytearray([48,240,0,0,240,0,0,240,48,0,240,0,48,240,192,192,240,48])
    # BITMAP: width: 3, height: 8, frames: 3
    _fore_mask = bytearray([112,240,112,112,240,240,240,240,112])
    name = "Umby"

    def __init__(self, x, y):
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
        self.aim_x = int(sin(self._aim_angle)*10)
        self.aim_y = int(cos(self._aim_angle)*10)

    @micropython.native
    def _tick_play(self, t):
        ### Handle one game tick for normal play controls ###
        x = self.x
        y = self.y
        _chd = tape.check_tape(x, y+1)
        _chu = tape.check_tape(x, y-4)
        _chl = tape.check_tape(x-1, y)
        _chlu = tape.check_tape(x-1, y-3)
        _chr = tape.check_tape(x+1, y)
        _chru = tape.check_tape(x+1, y-3)
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
        ### Handle one game tick for Umby's rocket.
        # Rockets start with aiming a target, then the launch
        # process begins and charges up. When the button is then
        # released the rocket launches. When the rocket hits the
        # ground it clears a blast radius, or kills Umby, if hit.
        # During flight, further presses of the rocket button
        # will leave a rocket trail that will act as a platform.
        ###
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
            self.aim_x = int(sin(angle)*power*10.0)
            self.aim_y = int(cos(angle)*power*10.0)
        # Actually launch the rocket when button is released
        if bB() and power > 1.0 and not self.rocket_active:
            self.rocket_active = 1
            self._rocket_x = self.x
            self._rocket_y = self._y - 1
            self._rocket_x_vel = sin(angle)*power/2.0
            self._rocket_y_vel = cos(angle)*power/2.0
            self._aim_pow = 1.0
            self.aim_x = int(sin(angle)*10.0)
            self.aim_y = int(cos(angle)*10.0)
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
            if tape.check_tape(rx, ry):
                # Explode rocket
                self.kill(t, None)
        # Wait until the rocket button is released before firing another
        if self.rocket_active == 2 and bB():
            self.rocket_active = 0

    @micropython.viper
    def draw(self, t: int):
        ### Draw Umby to the draw buffer ###
        p = int(tape.x[0])
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
        tape.draw(0, x_pos-1-p, y_pos-6, self._sdw, 3, f) # Shadow
        tape.draw(1, x_pos-1-p, y_pos-6, self._art, 3, f) # Umby
        tape.mask(0, x_pos-4-p, y_pos-6, self._back_mask, 9, 0)
        tape.mask(1, x_pos-1-p, y_pos-6, self._fore_mask, 3, fm)
        # Draw Umby's aim
        tape.draw(t*6//_FPS%2, x_pos-p+aim_x-1, y_pos-6+aim_y, self._aim, 3, 0)
        tape.mask(1, x_pos-p+aim_x-1, y_pos-6+aim_y, self._aim_fore_mask, 3, 0)
        tape.mask(0, x_pos-p+aim_x-2, y_pos-5+aim_y, self._aim_back_mask, 5, 0)
        # Draw Umby's rocket
        if int(self.rocket_active) == 1:
            tape.draw(1, rock_x-p-1, rock_y-7, self._aim, 3, 0)
            tape.draw(0, rock_x-p+(-3 if aim_x>0 else 1), rock_y-7,
                self._aim, 3, 0) # Rocket tail


class Glow(Player):
    ### One of the players you can play with.
    # Glow is a cave dwelling glow worm. They can crawl along the roof,
    # fall at will, swing with a grappling hook, and fire rockets.
    # Unlike Umby, Rockets are self propelled and accelerate into a horizontal
    # flight, They are launched backwards and downwards in the oppostite
    # direction of the grappling hook aim, but accelerate horizontally
    # into the opposite direction of the rocket aim at launch.
    # Unlike Umby, Glow has two aims pointing in opposite directions,
    # one for the grappling hook, and one for the rocket aim. Aim can only
    # be moved up or down, and will switch to the horizontal direction for
    # the last direction Glow pressed.
    # Monsters, traps, and falling offscreen will kill them.
    # Glow is not good with mud, and if hits the ground, including at a bad angle
    # when on the grappling hook, will get stuck. This will cause it to be
    # difficult to throw the grappling hook, and may leave Glow with the only
    # option of sinking throug the abyse into the mud.
    # This means glow can sometimes fall through thin platforms like Umby's
    # platforms and then crawl underneath.
    # Umby also has some specific modes:
    #     * 0: auto attach grapple hook to ceiling.
    #     * 1: grapple hook activated.
    #    * 2: normal movement
    ###
    # BITMAP: width: 3, height: 8, frames: 6
    _art = bytearray([8,6,0,0,14,0,0,6,8,0,14,0,12,14,2,2,14,12])
    # Umby's shadow
    _sdw = bytearray([12,15,0,0,15,0,0,15,12,0,15,0,12,15,3,3,15,12])
    # BITMAP: width: 3, height: 8, frames: 3
    _fore_mask = bytearray([14,15,14,14,15,15,15,15,14])

    name = "Glow"

    def __init__(self, x, y):
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
        self.aim_x = int(sin(self._aim_angle)*10.0)
        self.aim_y = int(cos(self._aim_angle)*10.0)
        # Grappling hook variables
        self._bAOnce = 0 # Had a press down of A button
        self._hook_x = 0 # Position where hook attaches ceiling
        self._hook_y = 0
        self._hook_ang = 0.0
        self._hook_vel = 0.0
        self._hook_len = 0.0

    @micropython.native
    def _bAO(self):
        ### Returns true if the A button was hit
        # since the last time thie was called
        ###
        if self._bAOnce == 1:
            self._bAOnce = -1
            return 1
        return 0

    @micropython.native
    def _tick_play(self, t):
        ### Handle one game tick for normal play controls ###
        x = self.x
        y = self.y
        _chd = tape.check_tape(x, y-1)
        _chrd = tape.check_tape(x+1, y-1)
        _chlld = tape.check_tape(x-2, y-1)
        _chrrd = tape.check_tape(x+2, y-1)
        _chld = tape.check_tape(x-1, y-1)
        _chl = tape.check_tape(x-1, y)
        _chr = tape.check_tape(x+1, y)
        _chll = tape.check_tape(x-2, y)
        _chrr = tape.check_tape(x+2, y)
        _chu = tape.check_tape(x, y+3)
        _chlu = tape.check_tape(x-1, y+3)
        _chru = tape.check_tape(x+1, y+3)
        free_falling = not (_chd or _chld or _chrd or _chl or _chr)
        head_hit = _chu or _chlu or _chru
        # CONTROLS: Activation of grappling hook
        if self.mode == 0:
            # Shoot hook straight up
            i = y-1
            while i > 0 and not tape.check_tape(x, i):
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
                x2 = self._hook_x + sin(ang2)*self._hook_len
                y2 = self._hook_y + cos(ang2)*self._hook_len
                self._x_vel = x2 - self._x
                self._y_vel = y2 - self._y
            # Update motion and position variables based on swing
            self._hook_ang += self._hook_vel/128.0
            self._x = self._hook_x + sin(self._hook_ang)*self._hook_len
            self._y = self._hook_y + cos(self._hook_ang)*self._hook_len
        elif self.mode == 2: # Normal movement (without grappling hook)
            # CONTROLS: Activate hook
            if free_falling and self._bAO():
                # Activate grappling hook in aim direction
                self._hook_ang = self._aim_angle * self.dir
                # Find hook landing position
                x2 = -sin(self._hook_ang)/2
                y2 = -cos(self._hook_ang)/2
                xh = x
                yh = y
                while (yh > 0 and (x-xh)*self.dir < 40
                and not tape.check_tape(int(xh), int(yh))):
                    xh += x2
                    yh += y2
                # Apply grapple hook parameters
                self._hook_x = int(xh)
                self._hook_y = int(yh)
                x1 = x - self._hook_x
                y1 = y - self._hook_y
                self._hook_len = sqrt(x1*x1+y1*y1)
                # Now get the velocity in the grapple angle
                v1 = (1-self._x_vel*y1+self._y_vel*x1)/(self._hook_len+1)
                xv = self._x_vel
                yv = self._y_vel
                self._hook_vel = -sqrt(xv*xv+yv+yv)*v1*4
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
        ### Handle one game tick for Glows's rocket.
        # Rockets start with aiming a target, then the launch
        # process begins and charges up. When the button is then
        # released the rocket launches. When the rocket hits the
        # ground it clears a blast radius, or kills Glow, if hit.
        # See the class doc strings for more details.
        ###
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
            self.aim_x = int(sin(angle)*power*10.0)*self.dir
            self.aim_y = int(cos(angle)*power*10.0)
        # Actually launch the rocket when button is released
        if bB() and power > 1.0:
            self.rocket_active = 1
            self._rocket_x = self.x
            self._rocket_y = self._y + 1
            self._rocket_x_vel = sin(angle)*power/2.0*self.dir
            self._rocket_y_vel = cos(angle)*power/2.0
            self._aim_pow = 1.0
            self.aim_x = int(sin(angle)*10.0)*self.dir
            self.aim_y = int(cos(angle)*10.0)
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
            if tape.check_tape(rx, ry):
                # Explode rocket
                self.kill(t, None)
        # Immediately reset rickets after an explosion
        if self.rocket_active == 2:
            self.rocket_active = 0

    @micropython.viper
    def draw(self, t: int):
        ### Draw Glow to the draw buffer ###
        p = int(tape.x[0])
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
        tape.draw(0, x_pos-1-p, y_pos-1, self._sdw, 3, f) # Shadow
        tape.draw(1, x_pos-1-p, y_pos-1, self._art, 3, f) # Glow
        tape.mask(0, x_pos-4-p, y_pos-1, self._back_mask, 9, 0)
        tape.mask(1, x_pos-1-p, y_pos-1, self._fore_mask, 3, fm)
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
                tape.draw(1, sx-1, sy-6, self._aim, 3, 0)
            hx = hook_x-p-1
            hy = hook_y-6
        else:
            hx = x_pos-p-aim_x//2-1
            hy = y_pos-6-aim_y//2
        tape.draw(l, hx, hy, self._aim, 3, 0)
        tape.mask(1, hx, hy, self._aim_fore_mask, 3, 0)
        tape.mask(0, hx-1, hy+1, self._aim_back_mask, 5, 0)
        # Rocket aim
        x = x_pos-p+aim_x-1
        y = y_pos-6+aim_y
        tape.draw(l, x, y, self._aim, 3, 0)
        tape.mask(1, x, y, self._aim_fore_mask, 3, 0)
        tape.mask(0, x-1, y+1, self._aim_back_mask, 5, 0)
        # Draw Glows's rocket
        if self.rocket_active:
            rock_x = int(self.rocket_x)
            rock_y = int(self.rocket_y)
            dire = int(self._r_dir)
            tape.draw(1, rock_x-p-1, rock_y-7, self._aim, 3, 0)
            tape.draw(0, rock_x-p+(-3 if dire>0 else 1), rock_y-7,
                self._aim, 3, 0) # Rocket tail


class BonesTheMonster:
    ### Bones is a monster that flyes about then charges the player.
    # Bones looks a bit like a skull.
    # It will fly in a random direction until it hits a wall in which case
    # it will change direction again. There is a very small chance that
    # Bones will fly over walls and ground and Bones will continue until
    # surfacing. If Bones goes offscreen to the left + 72 pixels, it will die;
    # offscreen to the top or bottom plus 10, it will change direction.
    # It will also change direction on occasion.
    # When the player is within a short range, Bones will charge the player
    # and will not stop.
    ###
    # BITMAP: width: 7, height: 8, frames: 3
    _art = bytearray([28,54,147,110,147,54,28,28,190,159,110,159,190,28,28,242,
        139,222,139,242,28])
    # BITMAP: width: 9, height: 8
    _mask = bytearray([28,62,247,243,239,243,247,62,28])

    def __init__(self, tape, x, y):
        self._tp = tape
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
        ### Update Bones for one game tick ###
        # Find the potential new coordinates
        tape = self._tp
        x = self.x
        y = self.y
        if self.mode == 0: # Flying
            nx = self._x + self._dx
            ny = self._y + self._dy
            # Change direction if needed
            if ((self._dx == 0 and self._dy == 0)
            or ny < -10 or ny > 74 or t%128==0
            or (tape.check_tape(int(nx), int(ny)) and t%12 and not (
                tape.check_tape(x, y) or y < 0 or y >= 64))):
                self._dx = sin(t+nx)/4.0
                self._dy = cos(t+nx)/4.0
            else:
                self._x = nx
                self._y = ny
                self.x = int(nx)
                self.y = int(ny)
            # Check for charging condition
            for plyr in tape.players:
                px = plyr.x - x
                py = plyr.y - y
                if px*px + py*py < 300:
                    self._target = plyr
                    self.mode = 1
            # Check for own death conditions
            if x < tape.x[0]:
                tape.mons.remove(self)
        elif t%4==0: # Charging
            t = self._target
            self.x += 1 if x < t.x else -1 if x > t.x else 0
            self.y += 1 if y < t.y else -1 if y > t.y else 0

    @micropython.viper
    def draw(self, t: int):
        ### Draw Bones to the draw buffer ###
        tape = self._tp
        p = int(tape.x[0])
        x_pos = int(self.x)
        y_pos = int(self.y)
        mode = int(self.mode)
        # Select animation frame
        f = 2 if mode == 1 else 0 if t*16//_FPS % 16 else 1
        # Draw Bones' layers and masks
        tape.draw(1, x_pos-3-p, y_pos-4, self._art, 7, f) # Bones
        tape.mask(1, x_pos-4-p, y_pos-4, self._mask, 9, 0) # Mask
        tape.mask(0, x_pos-4-p, y_pos-4, self._mask, 9, 0) # Mask


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





## Game Play ##

def set_level(start):
    ### Prepare everything for a level of gameplay including
    # the starting tape, and the feed patterns for each layer.
    # @param start: The starting x position of the tape.
    ###
    # Set the feed patterns for each layer.
    # (back, mid-back, mid-back-fill, foreground, foreground-fill)
    tape.feed[:] = [pattern_toplit_wall,
        pattern_stalagmites, pattern_stalagmites_fill,
        pattern_cave, pattern_cave_fill]
    # Reset monster spawner to the new level
    tape.types = [BonesTheMonster]
    tape.rates = bytearray([200])
    tape.reset(start)
    if start > -9999:
        # Fill the visible tape with the starting platform
        for i in range(start, start+72):
            tape.redraw_tape(2, i, pattern_room, pattern_fill)
        # Draw starting instructions
        tape.write(1, "THAT WAY!", start+19, 26)
        tape.write(1, "------>", start+37, 32)

def run_menu():
    ### Loads a starting menu and returns the selections.
    # @returns: a tuple of the following values:
    #     * Umby (0), Glow (1)
    #     * 1P (0), 2P (1)
    #     * New (0), Load (1)
    ###
    t = 0
    set_level(-9999)
    tape.add(BonesTheMonster, -9960, 25)
    m = tape.mons[0]
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
        # Make the camera follow the monster
        m.tick(t)
        m.draw(t)
        tape.auto_camera_parallax(m.x, m.y, t)
        # Composite everything together to the render buffer
        tape.comp()
        # Flush to the display, waiting on the next frame interval
        display_update()
        t += 1
    tape.clear_overlay()
    return ch[0], ch[1], ch[2]



run_menu()

"""
@micropython.native
def run_game():
    ### Initialise the game and run the game loop ###
    # Basic setup
    # Start menu
    glow, coop, load = run_menu()

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


    t = 0;
    set_level(start)
    if glow:
        p1 = Glow(start+10, 20)
    else:
        p1 = Umby(start+10, 20)
    tape.players.append(p1)
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
        for mon in tape.mons:
            mon.tick(t)

        # Make the camera follow the action
        tape.auto_camera_parallax(p1.x, p1.y, t)

        # Update the display buffer new frame data
        # Add all the monsters, and check for collisions along the way
        for mon in tape.mons:
            mon.draw(t)
            # Check if a rocket hits this monster
            if p1.rocket_active:
                if tape.check(p1.rocket_x-tape.x[0], p1.rocket_y, 128):
                    tape.mons.remove(mon)
                    p1.kill(t, mon)
        # If player is in play mode, check for monster collisions
        if p1.mode >= 0 and tape.check(p1.x-tape.x[0], p1.y, 224):
            p1.die(240, "Umby became monster food!")

        # Draw the players
        p1.draw(t)

        # Composite everything together to the render buffer
        tape.comp()
        # Flush to the display, waiting on the next frame interval
        display_update()

        t += 1
run_game()
"""
