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

## Umby and Glow artwork ##
# BITMAP: width: 3, height: 8, frames: 6
_u_art = bytearray([16,96,0,0,112,0,0,96,16,0,112,0,48,112,64,64,112,48])
# Umby's shadow
_u_sdw = bytearray([48,240,0,0,240,0,0,240,48,0,240,0,48,240,192,192,240,48])
# BITMAP: width: 3, height: 8, frames: 3.
_u_fore_mask = bytearray([112,240,112,112,240,240,240,240,112])
# BITMAP: width: 3, height: 8, frames: 6
_g_art = bytearray([8,6,0,0,14,0,0,6,8,0,14,0,12,14,2,2,14,12])
# Umby's shadow
_g_sdw = bytearray([12,15,0,0,15,0,0,15,12,0,15,0,12,15,3,3,15,12])
# BITMAP: width: 3, height: 8, frames: 3
_g_fore_mask = bytearray([14,15,14,14,15,15,15,15,14])
# BITMAP: width: 9, height: 8
_ug_back_mask = bytearray([120,254,254,255,255,255,254,254,120])
# BITMAP: width: 3, height: 8
_aim = bytearray([64,224,64])
 # BITMAP: width: 3, height: 8
_aim_fore_mask = bytearray([224,224,224])
# BITMAP: width: 5, height: 8
_aim_back_mask = bytearray([112,248,248,248,112])


class Player:
    ### Umby and Glow ###

    ### Umby: One of the players you can play with.
    # Activate by creating object with name == "Umby"
    # Umby is an earth worm. They can jump, aim, and fire rockets.
    # Umby can also make platforms by releasing rocket trails.
    # Monsters, traps, and falling offscreen will kill them.
    # Hitting their head on a platform or a roof, while jumping, will
    # also kill them.
    ###

    ### Glow: One of the players you can play with.
    # Activate by creating object with name == "Glow"
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
    #     * 2: normal movement
    ###

    ### Clip: Secret test mode you can play with.
    # Invincible orb that can float anywhere and then
    # transform into Umby or Glow (name will stay as "Clip")
    # Activate by creating object with name == "Clip"

    def __init__(self, tape, name, x, y, ai=False):
        # Modes:
        #     199: Testing (Clip)
        #     200: Frozen (immune)
        #     201: Respawning to Umby
        #     202: Respawning to Glow
        # ----0-9: Umby modes----
        #       0: Crawling (along ground)
        # --10-19: Glow modes----
        #      10: Auto latching grapple
        #      11: Swinging from grapple
        #      12: Clinging (from ceiling)
        self.mode = 0 # (int)
        self.dir = 1
        self.rocket_dir = self.moving = self.rocket_on = 0
        # Movement variables
        self._x_vel, self._y_vel = 0.0, 0.0
        # Rocket variables
        self.rocket_x, self.rocket_y = 0, 0 # (int).
        self._aim_ang = 2.5
        self._aim_pow = 1.0
        # Grappling hook variables
        self.hook_x, self.hook_y = 0, 0 # (int) Position where hook attaches ceiling
        # Internal calulation of hook parameters (resolved to player x, y in tick)
        self._hook_ang = self._hook_vel = self._hook_len = 0.0
        if name == "Glow": # Glow's starting behaviors
            self.mode = 10
            self._aim_ang = -0.5
        elif name == "Clip": # Test mode starting behaviors
            self.mode = 199
        self.name = name
        self.ai = ai
        self._tp = tape
        # Motion variables
        self._x, self._y = x, y
        # Viper friendly variants (ints)
        self.x, self.y = int(x), int(y)
        self.aim_x = int(sin(self._aim_ang)*10.0)
        self.aim_y = int(cos(self._aim_ang)*10.0)
        # Control registers
        self.u = self.d = self.l = self.r = self.b = self.a = False
        self._hold = False

    @property
    def immune(self):
        ### Returns if Umby is in a mode that can't be killed ###
        return 199 <= self.mode <= 202 or self.ai

    def die(self, rewind_distance, death_message):
        if self.immune:
            return
        ### Put Player into a respawning state ###
        self._x_vel = 0.0 # Reset speed
        self._y_vel = 0.0 # Reset fall speed
        self.mode = 201 if 0 <= self.mode <= 9 else 202
        self._respawn_x = self._tp.x[0] - rewind_distance
        self._tp.message(0, death_message)

    @micropython.native
    def kill(self, t, monster):
        ### Explode the rocket, killing the monster or nothing.
        # Also carves space out of the ground.
        ###
        tape = self._tp
        scratch = tape.scratch_tape
        rx, ry = self.rocket_x, self.rocket_y
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
            scratch(2, x, pattern, fill)
        # DEATH: Check for death by rocket blast
        dx, dy = rx-self.x, ry-self.y
        if dx*dx + dy*dy < 64:
            self.die(240, self.name + " kissed a rocket!")
        # Get ready to end rocket
        self.rocket_on = 0

    @micropython.native
    def _ai(self, t):
        ### Consult with the digital oracle for button presses ###
        x, y = self.x, self.y
        d = self.dir
        p = self._tp.x[0] + 36 # Horizontal middle
        m = bool(self._tp.mons)
        # Vertical super powers
        self._y = 9 if y < 3 else 63 if y > 63 else self._y
        # Horizontal super powers
        self._x = p-50 if x < p-50 else self._x
        if self.mode == 0: # Umby
            # Vertical jump super powers
            self._y_vel = -1 if y > 63 else self._y_vel
            # Horizontal walking, rocket, and jump
            return 0, 0, x > p+d*10, x < p+d*10, m&t//64%8==0, y >= 50

    @micropython.native
    def tick(self, t):
        ### Updated Player for one game tick.
        # @param t: the current game tick count
        ###
        # Update button press states
        self.u, self.d, self.l, self.r, self.b, self.a = (
            not bU(), not bD(), not bL(), not bR(), not bB(), not bA()
            ) if not self.ai else self._ai(t)
        # Update directional states
        self.dir = -1 if self.l else 1 if self.r else self.dir
        self.moving = 1 if self.l or self.r else 0
        # Normal Play modes
        if self.mode < 199:
            # Normal play modes
            if self.mode == 0: # Crawl mode (Umby)
                self._tick_play_ground(t)
            else: # Roof climbing modes (Glow)
                self._tick_play_roof(t)
            # Check for common death conditions:
            # DEATH: Check for falling into the abyss
            if self._y > 80:
                self.die(240, self.name + " fell into the abyss!")
        # Respawn mode
        elif 201 <= self.mode <= 202:
            self._tick_respawn()
        # Testing mode
        elif self.mode == 199:
            self._tick_testing()
        # Update the viper friendly variables.
        self.x = int(self._x)
        self.y = int(self._y)
        # Handle rocket engine tick
        if self.mode == 0: # Umby's rocket
            self._tick_rocket_grenade(t)
        elif self.mode < 199: # Glow's rocket
            self._tick_rocket_missile(t)

    @micropython.native
    def _tick_play_ground(self, t):
        ### Handle one game tick for ground play controls ###
        x, y = self.x, self.y
        ch = self._tp.check_tape
        cl = ch(x-1, y)
        cr = ch(x+1, y)
        grounded = ch(x, y+1) or cl or cr
        lwall = cl or ch(x-1, y-3)
        rwall = cr or ch(x+1, y-3)
        # Apply gravity and grund check
        self._y += self._y_vel if not grounded else 0
        # Stop gravity when hit ground but keep some fall speed ready
        self._y_vel = 0.5 if grounded else self._y_vel + 2.5 / _FPS
        # CONTROLS: Apply movement
        if t%3: # Movement
            self._x += (-1 if self.l and not lwall else
                1 if self.r and not rwall else 0)
        if t%3==0 and not ch(x, y-3): # Climbing
            self._y += (-1 if (self.l and lwall) or (self.r and rwall) else 0)
        # CONTROLS: Apply jump - allow continual jump until falling begins
        if self.a and (self._y_vel < 0 or grounded):
            if grounded: # detatch from ground grip
                self._y -= 1
            self._y_vel = -0.8
        # DEATH: Check for head smacking
        if ch(x, y-4) and self._y_vel < -0.4:
            self.die(240, self.name + " face-planted the roof!")

    @micropython.native
    def _launch_hook(self, angle):
        ### Activate grappling hook in given aim ###
        ch = self._tp.check_tape
        x, y = self.x, self.y
        self._hook_ang = angle
        # Find hook landing position
        xs, ys = -sin(angle)/2, -cos(angle)/2
        xh, yh = x, y
        d = self.dir
        while (yh >= -1 and (x-xh)*d < 40 and not ch(int(xh), int(yh))):
            xh += xs
            yh += ys
        # Apply grapple hook parameters
        self.hook_x, self.hook_y = int(xh), int(yh)
        x1 = self.x - self.hook_x
        y1 = self.y - self.hook_y
        self._hook_len = sqrt(x1*x1+y1*y1)
        # Now get the velocity in the grapple angle
        xv, yv = self._x_vel, self._y_vel
        self._hook_vel = -sqrt(xv*xv+yv*yv)*(1-xv*y1+yv*x1)*4/(self._hook_len+1)
        # Start normal grappling hook mode
        self.mode = 11
        self._hold = True

    @micropython.native
    def _tick_play_roof(self, t):
        ### Handle one game tick for roof climbing play controls ###
        x, y = self.x, self.y
        ch = self._tp.check_tape
        cd = ch(x, y-1)
        crd = ch(x+1, y-1)
        cld = ch(x-1, y-1)
        cl = ch(x-1, y)
        cr = ch(x+1, y)
        cu = ch(x, y+3)
        clu = ch(x-1, y+3)
        cru = ch(x+1, y+3)
        falling = not (cd or cld or crd or cl or cr)
        head_hit = cu or clu or cru
        self._hold = False if falling and not self.a else self._hold
        # CONTROLS: Activation of grappling hook
        if self.mode == 10:
            # Shoot hook straight up
            self._x_vel = self._y_vel = 0.0
            self._launch_hook(0)
        # CONTROLS: Grappling hook swing
        if self.mode == 11:
            ang = self._hook_ang
            # Apply gravity
            g = ang*ang/2.0
            self._hook_vel += -g if ang > 0 else g if ang < 0 else 0.0
            # Air friction
            vel = self._hook_vel
            self._hook_vel -= vel*vel*vel/64000
            # CONTROLS: swing
            self._hook_vel += -0.08 if self.l else 0.08 if self.r else 0
            # CONTROLS: climb/extend rope
            self._hook_len += -0.5 if self.u else 0.5 if self.d else 0
            # Check land interaction conditions
            if not falling and not self.a: # Stick to ceiling if touched
                self.mode = 12
            elif head_hit or (not falling and vel*ang > 0):
                # Rebound off ceiling
                self._hook_vel = -self._hook_vel
            # Release grappling hook with button or randomly within a second
            # when not connected to solid roof.
            elif (not self._hold and self.a or (self.hook_y < 0 and t%_FPS==0)):
                self.mode = 12
                # Convert angular momentum to free falling momentum
                ang2 = ang + vel/128.0
                self._x_vel = self.hook_x + sin(ang2)*self._hook_len - self._x
                self._y_vel = self.hook_y + cos(ang2)*self._hook_len - self._y
                self._hold = True
            # Update motion and position variables based on swing
            self._hook_ang += self._hook_vel/128.0
            self._x = self.hook_x + sin(self._hook_ang)*self._hook_len
            self._y = self.hook_y + cos(self._hook_ang)*self._hook_len
        elif self.mode == 12: # Clinging movement (without grappling hook)
            # CONTROLS: Activate hook
            if falling and self.a and not self._hold and self.y < 64:
                # Activate grappling hook in aim direction
                self._launch_hook(self._aim_ang*self.dir)
            # CONTROLS: Fall (force when jumping)
            elif falling or self.a:
                if not falling:
                    self._x_vel = -0.5 if self.l else 0.5 if self.r else 0.0
                # Apply gravity to vertical speed
                self._y_vel += 1.5 / _FPS
                # Update positions with momentum
                self._y += self._y_vel
                self._x += self._x_vel
            else:
                # Stop falling when attached to roof
                self._y_vel = 0
            # CONTROLS: Apply movement
            if t%2 and y < 64:
                climb = not cd and ((self.l and crd) or (self.r and cld))
                descend = not cu and (((cl or clu) and self.l)
                    or ((cr or cru) and self.r))
                lsafe = ((cld or cd or ch(x-2, y-1) or ch(x-2, y))
                    and self.l and not (cl or clu))
                rsafe = ((crd or cd or ch(x+2, y-1) or ch(x+2, y))
                    and self.r and not (cr or cru))
                self._x += -1 if lsafe else 1 if rsafe else 0
                self._y += -1 if climb else 1 if descend else 0

    @micropython.native
    def _tick_rocket_grenade(self, t):
        ### Handle one game tick for Umby's rocket.
        # Rockets start with aiming a target, then the launch
        # process begins and charges up. When the button is then
        # released the rocket launches. When the rocket hits the
        # ground it clears a blast radius, or kills Umby, if hit.
        # During flight, further presses of the rocket button
        # will leave a rocket trail that will act as a platform.
        ###
        tape = self._tp
        if self.u or self.d or self.b or self._aim_pow > 1.0:
            # CONTROLS: Aim rocket
            self._aim_ang += 0.02 if self.u else -0.02 if self.d else 0
            if self.b and not self.rocket_on and (
                    not self._hold or self._aim_pow > 1.0):
                self._aim_pow += 0.03
            # CONTROLS: Launch the rocket when button is released
            if not self.b and not self.rocket_on and self._aim_pow > 1.0:
                self.rocket_on = 1
                self._rocket_x, self._rocket_y = self.x, self._y - 1
                self._rocket_x_vel = sin(self._aim_ang)*self._aim_pow/2.0
                self._rocket_y_vel = cos(self._aim_ang)*self._aim_pow/2.0
                self._aim_pow = 1.0
                self.rocket_dir = 1 if self.aim_x > 0 else -1
                # Wait until the rocket button is released before firing another
                self._hold = True
            # Resolve rocket aim to the x by y vector form
            self.aim_x = int(sin(self._aim_ang)*self._aim_pow*10.0)
            self.aim_y = int(cos(self._aim_ang)*self._aim_pow*10.0)
        # Apply rocket dynamics if it is active
        if self.rocket_on:
            # Apply rocket motion
            self._rocket_x += self._rocket_x_vel
            self._rocket_y += self._rocket_y_vel
            rx = self.rocket_x = int(self._rocket_x)
            ry = self.rocket_y = int(self._rocket_y)
            # Apply gravity
            self._rocket_y_vel += 2.5 / _FPS
            # Create trail platform when activated
            if self.b:
                trail = pattern_bang(rx-self.rocket_dir, ry, 2, 1)
                for x in range(rx-self.rocket_dir*2, rx, self.rocket_dir):
                    tape.draw_tape(2, x, trail, None)
            # Diffuse if fallen through ground
            if ry > 80:
                self.rocket_on = 0
            # Check if the rocket hit the ground
            if tape.check_tape(rx, ry):
                self.kill(t, None) # Explode rocket
        else:
            self._hold = False if not self.b else self._hold

    @micropython.native
    def _tick_rocket_missile(self, t):
        ### Handle one game tick for Glows's rocket.
        # Rockets start with aiming a target, then the launch
        # process begins and charges up. When the button is then
        # released the rocket launches. When the rocket hits the
        # ground it clears a blast radius, or kills Glow, if hit.
        # See the class doc strings for more details.
        ###
        grappling = self.mode == 11
        tape = self._tp
        # CONTROLS: Apply rocket
        # Rocket aiming
        if self.u or self.d or self.b or self.l or self.r or (
                not self.b and self._aim_pow > 1.0):
            if not grappling:
                self._aim_ang += 0.02 if self.u else -0.02 if self.d else 0
                # Cap the aim angle between -2 and 2
                self._aim_ang = (-2.0 if self._aim_ang < -2.0 else
                    0 if self._aim_ang > 0 else self._aim_ang)
            if self.b: # Power rocket
                self._aim_pow += 0.03
            # Actually launch the rocket when button is released
            if not self.b and self._aim_pow > 1.0:
                self.rocket_on = 1
                self._rocket_x, self._rocket_y = self.x, self._y + 1
                self._rocket_x_vel = sin(self._aim_ang)*self._aim_pow/2*self.dir
                self._rocket_y_vel = cos(self._aim_ang)*self._aim_pow/2
                self._aim_pow = 1.0
                self.rocket_dir = self.dir
            # Resolve rocket aim to the x by y vector form
            self.aim_x = int(sin(self._aim_ang)*self._aim_pow*10.0)*self.dir
            self.aim_y = int(cos(self._aim_ang)*self._aim_pow*10.0)
        # Apply rocket dynamics if it is active
        if self.rocket_on:
            # Apply rocket motion
            self._rocket_x += self._rocket_x_vel
            self._rocket_y += self._rocket_y_vel
            rx = self.rocket_x = int(self._rocket_x)
            ry = self.rocket_y = int(self._rocket_y)
            # Apply flight boosters
            self._rocket_x_vel += 2.5 / _FPS * self.rocket_dir
            if ((self._rocket_x_vel > 0 and self.rocket_dir > 0)
            or (self._rocket_x_vel < 0 and self.rocket_dir < 0)):
                self._rocket_y_vel *= 0.9
            # Diffuse rocket if out of range
            if not (80>=ry>=-1) or not (-30<=rx-tape.x[0]<=102):
                self.rocket_on = 0
            # Explode rocket if the rocket hit the ground
            if tape.check_tape(rx, ry):
                self.kill(t, None)

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
            # Return to normal play modes
            self.mode = 0 if self.mode == 201 else 10
            tape.write(1, "DONT GIVE UP!", tape.midx[0]+8, 26)

    @micropython.native
    def _tick_testing(self):
        ### Handle one game tick for when in test mode.
        # Test mode allows you to explore the level by flying,
        # free of interactions.
        ###
        self._y += -1 if self.u else 1 if self.d else 0
        self._x += -1 if self.l else 1 if self.r else 0
        # Switch to characters if buttons are pressed
        if not self.r:
            self.mode = 0 if self.b else 10 if self.a else 199

    @micropython.viper
    def draw(self, t: int):
        mode = int(self.mode)
        tape = self._tp
        p = int(tape.x[0])
        py = int(tape.x[1])
        x_pos, y_pos = int(self.x) - p, int(self.y)
        m = int(self.moving)
        d = int(self.dir)
        # Get animation frame
        # Steps through 0,1,2,3 every half second for animation
        # of looking left and right, and changes to movement art of
        # 4 when moving left and 5 when moving right.
        f = t*2 // _FPS % 4 if not m else 4 if d < 0 else 5
        # 0 when still, 1 when left moving, 2 when right
        fm = 0 if not m else 1 if d < 0 else 2
        abl = t*6//_FPS%2 # aim blinker
        # Test mode or offscreen
        if mode == 199 or not (-2 < x_pos < 73 and -1 < y_pos-py < 42):
            hx = 0 if x_pos < -1 else 69 if x_pos > 72 else x_pos-1
            hy = py-5 if y_pos < py else py+32 if y_pos > py + 41 else y_pos-6
            tape.draw(abl, hx, hy, _aim, 3, 0)
            tape.mask(1, hx, hy, _aim_fore_mask, 3, 0)
            tape.mask(0, hx-1, hy+1, _aim_back_mask, 5, 0)
            return
        # Draw rocket, if active
        if self.rocket_on:
            hx, hy = int(self.rocket_x), int(self.rocket_y)
            rdir = int(self.rocket_dir)
            tape.draw(1, hx-p-1, hy-7, _aim, 3, 0)#head
            tape.draw(0, hx-p+(-3 if rdir>0 else 1), hy-7, _aim, 3, 0)#tail
        # Select the character specifics
        umby = mode == 0 or mode == 201
        sdw = _u_sdw if umby else _g_sdw
        art = _u_art if umby else _g_art
        msk = _u_fore_mask if umby else _g_fore_mask
        hy = y_pos-6 if umby else y_pos-1
        # Draw Umby's or Glow's layers and masks
        tape.draw(0, x_pos-1, hy, sdw, 3, f) # Shadow
        tape.draw(1, x_pos-1, hy, art, 3, f) # Umby
        tape.mask(1, x_pos-1, hy, msk, 3, fm)
        tape.mask(0, x_pos-4, hy, _ug_back_mask, 9, 0)
        # Aims and hooks
        if mode == 11: # Activated grappling hook rope
            hook_x, hook_y = int(self.hook_x), int(self.hook_y)
            # Draw Glow's grappling hook rope
            for i in range(0, 8):
                sx = x_pos + (hook_x-(x_pos+p))*i//8
                sy = y_pos + (hook_y-y_pos)*i//8
                tape.draw(1, sx-1, sy-6, _aim, 3, 0)
            hx, hy = hook_x-p-1, hook_y-6
        aim_x, aim_y = int(self.aim_x), int(self.aim_y)
        if self.ai: # Only main player has aiming
            return
        if not umby:
            # Draw Glows's grappling hook aim
            hx, hy = x_pos-aim_x//2-1, y_pos-aim_y//2-6
            tape.draw(abl, hx, hy, _aim, 3, 0)
            tape.mask(1, hx, hy, _aim_fore_mask, 3, 0)
            tape.mask(0, hx-1, hy+1, _aim_back_mask, 5, 0)
        # Rocket aim
        hx = x_pos+aim_x-1
        hy = y_pos+aim_y-6
        tape.draw(abl, hx, hy, _aim, 3, 0)
        tape.mask(1, hx, hy, _aim_fore_mask, 3, 0)
        tape.mask(0, hx-1, hy+1, _aim_back_mask, 5, 0)


## Monster types ##




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
# TODO: Monster which is a swirling mass of sprites (multi-sprite monsters)




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
_Bones = const(1)
Bones = _Bones

class _MonsterPainter:
    ### Draws the different monsters ###
    # BITMAP: width: 7, height: 8, frames: 3
    _bones = bytearray([28,54,147,110,147,54,28,28,190,159,110,159,190,28,28,
        242,139,222,139,242,28])
    # BITMAP: width: 9, height: 8
    _bones_m = bytearray([28,62,247,243,239,243,247,62,28])

    @micropython.viper
    def draw(self, tape, tid: int, mode: int, x: int, y: int, t: int):
        ### Draw Monster to the draw buffers ###
        if tid == _Bones:
            # Select animation frame
            f = 2 if mode == 1 else 0 if t*16//_FPS % 16 else 1
            # Draw Bones' layers and masks
            tape.draw(1, x-3, y-4, self._bones, 7, f) # Bones
            tape.mask(1, x-4, y-4, self._bones_m, 9, 0) # Mask Fore
            tape.mask(0, x-4, y-4, self._bones_m, 9, 0) # Mask Backd
_painter = _MonsterPainter()


class Monster:

    @micropython.native
    def __init__(self, tape, tid, x, y):
        ### Engine for all the different monsters ###
        # Modes:
        #     0 - Random flying, prefering space, and ready to charge player
        #     1 - Charging player 1 (this device's player)
        #     2 - Charging player 2 (other device's player)
        self.mode = 0
        self._dx = self._dy = 0 # directional motion
        self.tid = tid
        self._tp = tape
        self.x, self.y = int(x), int(y) # Middle of Bones
        self._x, self._y = x, y # floating point precision

        # Set the bahavior for each monster type.
        if tid == _Bones:
            self.mode = 0

    @micropython.native
    def tick(self, t):
        ### Update Monster dynamics, based on mode, for one game tick ###
        tape = self._tp
        x, y = self.x, self.y
        mode = self.mode

        # Flying
        if mode == 0:
            nx, ny = self._x+self._dx, self._y+self._dy
            # Change direction if needed
            if ((self._dx == 0 and self._dy == 0)
            or ny < -10 or ny > 74 or t%128==0
            or (tape.check_tape(int(nx), int(ny)) and t%12 and not (
                tape.check_tape(x, y) or y < 0 or y >= 64))):
                self._dx, self._dy = sin(t+nx)/4.0, cos(t+nx)/4.0
            else: # Continue moving
                self._x, self._y = nx, ny
            # Check for charging condition
            for pi, plyr in enumerate(tape.players):
                px, py = plyr.x-x, plyr.y-y
                if px*px + py*py < 300:
                    self.mode = pi+1

        # Charging player 1 or 2
        elif 1 <= mode <=2:
            if t%4==0: # Charge rate
                t = tape.players[mode-1]
                self._x += 1 if x < t.x else -1 if x > t.x else 0
                self._y += 1 if y < t.y else -1 if y > t.y else 0

        # Update the viper friendly variables
        self.x, self.y = int(self._x), int(self._y)
        # Check for standard death conditions
        if self.x < tape.x[0] - 72: # Too far left, destroy monster
            tape.mons.remove(self)

    @micropython.viper
    def draw(self, t: int):
        _painter.draw(self._tp, self.tid, int(self.mode),
            self.x-self._tp.x[0], self.y, t)

