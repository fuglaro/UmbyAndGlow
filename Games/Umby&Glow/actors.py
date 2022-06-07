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


## Actors (Players and Monsters), and input ##

_FPS = const(60)

from machine import Pin
from math import sin, cos, sqrt
from patterns import *

# Button functions. Note they return the inverse pressed state
bU = Pin(4, Pin.IN, Pin.PULL_UP).value
bD = Pin(6, Pin.IN, Pin.PULL_UP).value
bL = Pin(3, Pin.IN, Pin.PULL_UP).value
bR = Pin(5, Pin.IN, Pin.PULL_UP).value
bB = Pin(24, Pin.IN, Pin.PULL_UP).value
bA = Pin(27, Pin.IN, Pin.PULL_UP).value



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




class _Player:
    ### Umby and Glow generic functions and variables ###
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
        tape = self._tp
        self.mode = -1#Respawn
        self._respawn_x = tape.x[0] - rewind_distance
        tape.message(0, death_message)

    @micropython.native
    def kill(self, t, monster):
        ### Explode the rocket, killing the monster or nothing.
        # Also carves space out of the ground.
        ###
        tape = self._tp
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
        pattern = pattern_bang(rx, ry, 8, 0)
        fill = pattern_bang(rx, ry, 10, 1)
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
        tape = self._tp
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


class Umby(_Player):
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

    def __init__(self, tape, x, y):
        self._tp = tape
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
        tape = self._tp
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
        tape = self._tp
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
                trail = pattern_bang(rx-rd, ry, 2, 1)
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
        tape = self._tp
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


class Glow(_Player):
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

    def __init__(self, tape, x, y):
        self._tp = tape
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
        self._bAOnce = -1 # Had a press down of A button
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
        tape = self._tp
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
                self._hook_vel = -sqrt(xv*xv+yv*yv)*v1*4
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
        tape = self._tp
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
            if ry > 80 or ry < -1 or px < -30 or px > 102:
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
        tape = self._tp
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