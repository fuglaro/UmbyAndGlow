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

## Players and input ##

from machine import Pin
from math import sqrt, floor
from patterns import *
from audio import *

_FPS = const(60)

# Button functions. Note they return the inverse pressed state
bU = Pin(4, Pin.IN, Pin.PULL_UP).value
bD = Pin(6, Pin.IN, Pin.PULL_UP).value
bL = Pin(3, Pin.IN, Pin.PULL_UP).value
bR = Pin(5, Pin.IN, Pin.PULL_UP).value
bB = Pin(24, Pin.IN, Pin.PULL_UP).value
bA = Pin(27, Pin.IN, Pin.PULL_UP).value

## Umby and Glow artwork ##
# BITMAP: width: 3, height: 8, frames: 6
_u_art = bytearray([1,6,0,0,7,0,0,6,1,0,7,0,3,7,4,4,7,3])
# Umby's shadow
_u_sdw = bytearray([51,127,0,0,255,0,0,127,51,0,255,0,35,127,28,28,127,35])
_u_sdw_air = bytearray([3,15,0,0,15,0,0,15,3,0,15,0,3,15,12,12,15,3]) # When falling
# BITMAP: width: 3, height: 8, frames: 6
_g_art = bytearray([16,76,0,0,92,0,0,76,16,0,92,0,24,92,4,4,92,24])
# Umby's shadow
_g_sdw = bytearray([89,159,64,64,159,64,64,159,89,64,159,64,89,159,70,70,159,89])
# BITMAP: width: 9, height: 8
_ug_back_mask = bytearray([120,254,254,255,255,255,254,254,120])
# BITMAP: width: 3, height: 8
_aim = bytearray([64,224,64])
 # BITMAP: width: 3, height: 8
_aim_fore_mask = bytearray([224,224,224])
# BITMAP: width: 5, height: 8
_aim_back_mask = bytearray([112,248,248,248,112])


# Fast sine and cos lookup table.
# If angle is in radians*65536, then use as follows:
#     sin = (_sinco[(a//1024+200)%400]-128)/128
#     cos = (_sinco[(a//1024-100)%400]-128)/128
_sinco = bytearray([127, 125, 123, 121, 119, 117, 115, 113, 111, 109, 107, 105,
    103, 101, 99, 97, 95, 93, 91, 89, 87, 85, 83, 82, 80, 78, 76, 74, 72, 71,
    69, 67, 65, 64, 62, 60, 58, 57, 55, 53, 52, 50, 49, 47, 46, 44, 43, 41, 40,
    38, 37, 35, 34, 33, 31, 30, 29, 27, 26, 25, 24, 23, 21, 20, 19, 18, 17, 16,
    15, 14, 13, 12, 12, 11, 10, 9, 8, 8, 7, 6, 6, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1,
    1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 3,
    4, 4, 5, 6, 6, 7, 8, 8, 9, 10, 11, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 24, 25, 26, 27, 28, 30, 31, 32, 34, 35, 37, 38, 39, 41, 42, 44, 45,
    47, 48, 50, 52, 53, 55, 57, 58, 60, 62, 63, 65, 67, 69, 70, 72, 74, 76, 78,
    80, 81, 83, 85, 87, 89, 91, 93, 95, 97, 99, 101, 102, 104, 106, 108, 110,
    112, 114, 116, 118, 120, 122, 124, 126, 128, 130, 132, 134, 136, 138, 140,
    142, 144, 146, 148, 150, 152, 154, 156, 158, 160, 162, 164, 166, 168, 170,
    171, 173, 175, 177, 179, 181, 182, 184, 186, 188, 190, 191, 193, 195, 196,
    198, 200, 201, 203, 205, 206, 208, 209, 211, 212, 214, 215, 217, 218, 220,
    221, 222, 224, 225, 226, 228, 229, 230, 231, 232, 233, 235, 236, 237, 238,
    239, 240, 241, 242, 242, 243, 244, 245, 246, 247, 247, 248, 249, 249, 250,
    250, 251, 251, 252, 252, 253, 253, 254, 254, 254, 254, 255, 255, 255, 255,
    255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 254, 254, 254, 253,
    253, 253, 252, 252, 251, 251, 250, 249, 249, 248, 247, 247, 246, 245, 244,
    244, 243, 242, 241, 240, 239, 238, 237, 236, 235, 234, 233, 231, 230, 229,
    228, 227, 225, 224, 223, 221, 220, 219, 217, 216, 214, 213, 211, 210, 208,
    207, 205, 203, 202, 200, 199, 197, 195, 193, 192, 190, 188, 187, 185, 183,
    181, 179, 177, 176, 174, 172, 170, 168, 166, 164, 162, 160, 159, 157, 155,
    153, 151, 149, 147, 145, 143, 141, 139, 137, 135, 133, 131, 129])


class Player:
    ### Umby and Glow ###

    ### Umby: One of the players you can play with.
    # Activate by creating object with name == "Umby"
    # Umby is an earth worm. They can jump, aim, and fire rockets.
    # Umby can also make platforms by releasing rocket trails.
    # Monsters, traps, and falling offscreen will kill them.
    # Hitting their head on a platform or a roof, while jumping, will
    # also kill them.
    #
    # Umby's rockets start with aiming a target, then the launch
    # process begins and charges up. When the button is then
    # released the rocket launches. When the rocket hits the
    # ground it clears a blast radius, or kills Umby, if hit.
    # During flight, further presses of the rocket button
    # will leave a rocket trail that will act as a platform.
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
    #
    # Glow's rockets start with aiming a target, then the launch
    # process begins and charges up. When the button is then
    # released the rocket launches. When the rocket hits the
    # ground it clears a blast radius, or kills Glow, if hit.
    # See the class doc strings for more details.
    ###

    ### Clip: Secret test mode you can play with.
    # Invincible orb that can float anywhere and then
    # transform into Umby or Glow (name will stay as "Clip")
    # Activate by creating object with name == "Clip"

    def __init__(self, tape, name, x, y, ai=False, coop=False):
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
        self.mode = 0
        self.name = name # Umby, Glow, or Clip
        self.ai = ai
        self._coop = coop
        self.dir = 1
        self.x, self.y = x, y # Unit is 1 pixel
        self.rocket_on = 0
        self.rocket_x, self.rocket_y = 0, 0 # Unit is 1 pixel
        # Internal properties
        self._tp = tape
        self._x, self._y = x*256, y*256 # Unit is 256th of a pixel
        self._rdir = 0
        self._moving = 0
        self._x_vel, self._y_vel = 0, 0 # Unit is 65536 of a pixel
        self._hx, self._hy = 0, 0 # Position where hook attaches ceiling
        # Internal hook parameters (resolved to player x, y in tick)
        self._hook_ang = 0 # Unit is 65536th of a radian
        self._hook_vel = 0
        self._hook_len = 0 # Unit is 256th of a pixel
        self._c = 0 # Button bits: up(1)|down(2)|left(4)|right(8)|b(16)|a(32)
        self._hold = 0
        self._aim_ang = 163840 # Unit is 65536th of a radian
        self._aim_pow = 256
        if name == "Glow": # Glow's starting behaviors
            self._aim_ang = -32768
            # Shoot hook straight up
            self._launch_hook(0)
        elif name == "Clip": # Test mode starting behaviors
            self.mode = 199
        self._aim_x = (_sinco[(self._aim_ang//1024+200)%400]-128)*10//128
        self._aim_y = (_sinco[(self._aim_ang//1024-100)%400]-128)*10//128
        self._boom_x = self._boom_y = 0 # recent explosion
        self._trail = 0 # Currently making platform from rocket trail
        self._air = 0 # Currently in jump

    @micropython.viper
    def port_out(self, buf: ptr8):
        ### Dump player data to the output buffer for sending to player 2 ###
        px = int(self._tp.x[0]) - 72
        buf[0] = px>>24
        buf[1] = px>>16
        buf[2] = px>>8
        buf[3] = px
        buf[4] = int(self.mode)
        buf[5] = int(self.x) - px
        buf[6] = int(self.y)
        buf[7] = int(self.rocket_x) - px
        buf[8] = int(self.rocket_y)
        buf[9] = int(self._hx) - px
        buf[10] = int(self._hy)
        boom = 1 if self._boom_x or self._boom_y else 0
        buf[11] = (# dir, rocket_on, rdir, moving, boom (0,1,2,3,4))
            (1 if int(self.dir) > 0 else 0)
            | int(self.rocket_on)*2
            | (4 if int(self._rdir) > 0 else 0)
            | int(self._moving)*8
            | boom*16
            | int(self._trail)*32
            | int(self._air)*64)
        buf[12] = int(self._boom_x) - px
        buf[13] = int(self._boom_y)
        self._boom_x = self._boom_y = 0 <<1|1 # reset last explosion (consumed)

    @micropython.viper
    def port_in(self, buf: ptr8):
        ### Unpack player data from input buffer recieved from player 2 ###
        px = buf[0]<<24 | buf[1]<<16 | buf[2]<<8 | buf[3]
        m = buf[11]
        if m&16:
            self.rocket_x = buf[12] + px <<1|1
            self.rocket_y = buf[13] <<1|1
            self.kill(buf[12], None)
        self.mode = buf[4] <<1|1
        self.x = buf[5] + px <<1|1
        self.y = buf[6] <<1|1
        rx = buf[7] + px
        ry = buf[8]
        self.rocket_x = rx <<1|1
        self.rocket_y = ry <<1|1
        self._hx = buf[9] + px <<1|1
        self._hy = buf[10] <<1|1
        self.dir = (1 if m&1 else -1) <<1|1
        self.rocket_on = (m&2) <<1|1
        rdir = 1 if m&4 else -1
        self._rdir = rdir <<1|1
        self._moving = (m&8) <<1|1
        self._air = (m&64) <<1|1
        if m&32: # Leave rocket trail
            drwtp = self._tp.draw_tape
            trail = pattern_bang(rx-rdir, ry, 2, 1)
            for rxp in range(rx-rdir*2, rx, rdir):
                drwtp(2, rxp, trail, None)

    @property
    @micropython.viper
    def immune(self) -> int:
        ### Returns if Umby is in a mode that can't be killed,
        # or killed by this engine.
        ###
        return 1 if 199 <= int(self.mode) <= 202 or self.ai or self._coop else 0

    @micropython.native
    def die(self, death_message):
        if self.immune:
            return
        ### Put Player into a respawning state ###
        self._x_vel = 0 # Reset speed
        self._y_vel = 0 # Reset fall speed
        self.mode = 201 if 0 <= self.mode <= 9 else 202
        self._respawn_x = self._x - 90000
        self._tp.message(0, death_message, 3)
        self._air = 1
        play(death, 240, True)

    @micropython.native
    def kill(self, t, monster):
        ### Explode the rocket, killing the monster or nothing.
        # Also carves space out of the ground.
        ###
        tape = self._tp
        scratch = tape.scratch_tape
        rx, ry = self.rocket_x, self.rocket_y
        self._boom_x, self._boom_y = rx, ry
        play(rocket_bang, 40)
        # Tag the wall with an explostion mark
        tag = t%4
        if -40 < rx-tape.x[0] < 112:
            tape.tag("<BANG!>" if tag==0 else "<POW!>" if tag==1 else
                "<WHAM!>" if tag==3 else "<BOOM!>", rx, ry)
            # Tag the wall with a death message
            if monster:
                tape.tag("[RIP]", monster[0], monster[1])
                play(rocket_kill, 30)
        # Carve blast hole out of ground
        pattern = pattern_bang(rx, ry, 8, 0)
        fill = pattern_bang(rx, ry, 10, 1)
        for x in range(rx-10, rx+10):
            scratch(2, x, pattern, fill)
        # DEATH: Check for death by rocket blast
        dx, dy = rx-self.x, ry-self.y
        if dx*dx + dy*dy < 64:
            self.die(self.name + " kissed a rocket!")
        # Get ready to end rocket
        self.rocket_on = 0

    @micropython.viper
    def _ai(self, t: int) -> int:
        ### Consult with the digital oracle for button presses ###
        mode = int(self.mode)
        x, y = int(self.x), int(self.y)
        d = int(self.dir) * 10
        p = int(self._tp.x[0]) + 36 # Horizontal middle
        m = int(bool(self._tp.mons.num))
        # Horizontal super powers
        if x < p-50:
            self._x = (p-50)*256 <<1|1
        # Vertical super powers
        if y < 3:
            self._y = 2304 <<1|1
        elif y > 63:
            self._y = 16128 <<1|1
        if mode == 0: # Umby
            # Vertical jump super powers
            if y > 63:
                self._y_vel = -65536 <<1|1
            # Horizontal walking, rocket, and jump
            return ((4 if x > p+d else 0) | (8 if x < p+d else 0)
                | (16 if m and t%512<48 else 0) | (32 if y >= 50 else 0))
        elif mode == 12: # Glow (roof-walk)
            # Super hook
            if y > 55:
                self._launch_hook(0)
                # Apply super grapple hook parameters
                self._hx, self._hy = x <<1|1, 1 <<1|1
                self._hook_len = ((y-1)<<8) <<1|1
            # Horizongal roof walking, rocket, and fall/grapple.
            return ((4 if x > p+d else 0) | (8 if x < p+d else 0)
                | (16 if m and t%256<5 else 0)
                | (32 if (t%16 and int(self._air) or t%512<8) else 0))
        else: # Glow (grappling swing)
            self._aim_ang = -52428 <<1|1
            if y < 0:
                self.mode = 12 <<1|1
            # Climb rope including when off screen so super powers work,
            # swing left/right towards center,
            # Fire rockets if monsters about, and
            # grapple when at end of swing if going in intended direction.
            a = int(self._hook_ang)
            return ((1 if int(self._hook_len)>3840 or x < p-50 else 0)
                | (4 if x>p else 0) | (8 if x<p else 0)
                | (16 if m and t%256<4 else 0)
                 | (32 if d*65536 > a > 32768 or d*65536 < a < -32768 else 0))

    @micropython.viper
    def tick(self, t: int):
        ### Updated Player for one game tick.
        # @param t: the current game tick count
        ###
        mode = int(self.mode)
        y = int(self._y)
        # If repesentation of coop Thumby, skip tick
        if self._coop:
            return
        # Update button press states
        if self.ai:
            c = int(self._ai(t))
        else:
            c = 63^(int(bU()) | int(bD())<<1 | int(bL())<<2 | int(bR())<<3
                | int(bB())<<4 | int(bA())<<5)
        self._c = c <<1|1

        # Update directional states
        l, r = c&4, c&8
        m = 0
        if l or r:
            self.dir = (-1 if l else 1) <<1|1
            m = 1
        self._moving = m <<1|1

        # Normal Play modes
        if mode < 199:
            # Normal play modes
            if mode == 0: # Crawl mode (Umby)
                self._tick_play_ground(t)
            else: # Roof climbing modes (Glow)
                self._tick_play_roof(t)
            # Check for common death conditions:
            # DEATH: Check for falling into the abyss
            if y > 20480:
                self.die(self.name + " fell into the abyss!")
        # Respawn mode
        elif 201 <= mode <= 202:
            self._tick_respawn()
        # Testing mode
        elif mode == 199:
            self._tick_testing()
        # Update the viper friendly variables.
        self.x = (int(self._x)>>8) <<1|1
        self.y = (int(self._y)>>8) <<1|1

    @micropython.viper
    def _tick_play_ground(self, t: int):
        ### Handle one game tick for ground play controls ###
        xf, yf = int(self._x), int(self._y)
        x, y = xf>>8, yf>>8
        yv = int(self._y_vel)
        c = int(self._c)
        ch = self._tp.check_tape
        cl = int(ch(x-1, y))
        cr = int(ch(x+1, y))
        grounded = int(ch(x, y+1)) | cl | cr
        self._air = (0 if grounded else 1) <<1|1
        lwall = int(ch(x-1, y-3)) | cl
        rwall = int(ch(x+1, y-3)) | cr
        # Apply gravity and ground check
        if not grounded:
            self._y = (yf + (yv>>8)) <<1|1
        # Stop gravity when hit ground but keep some fall speed ready
        self._y_vel = (32768 if grounded else yv + 2730) <<1|1
        # CONTROLS: Apply movement
        if t%3: # Movement
            self._x = (xf + (-256 if c&4 and not lwall else
                256 if c&8 and not rwall else 0)) <<1|1
        if t%3==0 and not ch(x, y-3) and ((c&4 and lwall) or (c&8 and rwall)):
            self._y = (yf-256) <<1|1 # Climbing
        # CONTROLS: Apply jump - allow continual jump until falling begins
        if c&32 and (yv < 0 or grounded):
            if grounded: # detatch from ground grip
                self._y = (yf-256) <<1|1
                play(worm_jump, 15)
            self._y_vel = -52428 <<1|1
        # DEATH: Check for head smacking
        if ch(x, y-4) and yv < -26214:
            # Only actually die if the platform hit is largish
            if (ch(x, y-5) and
                (ch(x-1, y-4) and ch(x-2, y-4))
                    or(ch(x+1, y-4) and ch(x+2, y-4))):
                self.die(self.name + " face-planted the roof!")

        # Umby's rocket.
        ron = int(self.rocket_on)
        u, d, b = c&1, c&2, c&16
        # Apply rocket dynamics if it is active
        if ron:
            rdir = int(self._rdir)
            rxf, ryf = int(self._rocket_x), int(self._rocket_y)
            ryv = int(self._rocket_y_vel)
            # Apply rocket motion
            rxf += int(self._rocket_x_vel)
            ryf += ryv
            ryv += 11 # Apply gravity
            # Update stored properties
            rx, ry = rxf>>8, ryf>>8
            self.rocket_x, self.rocket_y = rx <<1|1, ry <<1|1
            self._rocket_x, self._rocket_y = rxf <<1|1, ryf <<1|1
            self._rocket_y_vel = ryv <<1|1
            if b: # Create trail platform when activated
                drwtp = self._tp.draw_tape
                trail = pattern_bang(rx-rdir, ry, 2, 1)
                for rxp in range(rx-rdir*2, rx, rdir):
                    drwtp(2, rxp, trail, None)
            self._trail = (1 if b else 0)<<1|1
            if ry >= 80: # Defuse if fallen through ground
                self.rocket_on = 0 <<1|1
            if ch(rx, ry): # Explode rocket if hit the ground
                self.kill(t, None)
        elif b==0:
            self._hold = 0 <<1|1

        # Aiming and launching
        a_pow = int(self._aim_pow)
        if (u | d | b) or a_pow > 256:
            _snco = ptr8(_sinco)
            # CONTROLS: Aim rocket
            a_ang = int(self._aim_ang)
            if u | d:
                a_ang += 1310 if u else -1310
                self._aim_ang = a_ang <<1|1
            if b and ron==0 and (not self._hold or a_pow > 256):
                a_pow += 10
            # CONTROLS: Launch the rocket when button is released
            elif b==0 and ron==0 and a_pow > 256:
                play(rocket_flight, 180)
                self.rocket_on = 1 <<1|1
                self._rocket_x, self._rocket_y = xf <<1|1, yf-256 <<1|1
                self._rocket_x_vel = (
                    (_snco[((a_ang>>10)+200)%400]-128)*a_pow>>8) <<1|1
                self._rocket_y_vel = (
                    (_snco[((a_ang>>10)-100)%400]-128)*a_pow>>8) <<1|1
                a_pow = 256
                self._rdir = (1 if int(self._aim_x) > 0 else -1) <<1|1
                # Wait until the rocket button is released before firing another
                self._hold = 1 <<1|1
            # Resolve rocket aim to the x by y vector form
            self._aim_x = ((_snco[((a_ang>>10)+200)%400]-128)*a_pow//3360) <<1|1
            self._aim_y = ((_snco[((a_ang>>10)-100)%400]-128)*a_pow//3360) <<1|1
            self._aim_pow = a_pow <<1|1

    @micropython.viper
    def _launch_hook(self, angle: int):
        ### Activate grappling hook in given aim ###
        ch = self._tp.check_tape
        _snco = ptr8(_sinco)
        x, y = int(self.x), int(self.y)
        xl, yl = x<<8, y<<8
        self._hook_ang = angle <<1|1
        # Find hook landing position
        xs = 128-_snco[((angle>>10)+200)%400]
        ys = 128-_snco[((angle>>10)-100)%400]
        xh, yh = xl, yl
        d = int(self.dir)
        while (yh >= -1 and (xl-xh)*d < 10240 and not int(ch(xh>>8, yh>>8))):
            xh += xs
            yh += ys
        # Apply grapple hook parameters
        self._hx, self._hy = (xh>>8) <<1|1, (yh>>8) <<1|1
        x1, y1 = xl-xh, yl-yh
        self._hook_len = int(floor(sqrt(x1*x1+y1*y1))) <<1|1
        # Now get the velocity in the grapple angle
        xv, yv = int(self._x_vel)>>8, int(self._y_vel)>>8
        self._hook_vel = 0-(int(floor(sqrt(xv*xv+yv*yv)))*(1-xv*y1+yv*x1)
            >>5)//(int(self._hook_len) or 1) <<1|1
        # Start normal grappling hook mode
        self.mode = 11 <<1|1
        self._hold = 1 <<1|1
        play(grapple_launch, 15)

    @micropython.viper
    def _tick_play_roof(self, t: int):
        ### Handle one game tick for roof climbing play controls ###
        mode = int(self.mode)
        _snco = ptr8(_sinco)
        x, y = int(self.x), int(self.y)
        xf, yf = int(self._x), int(self._y)
        dr = int(self.dir)
        ch = self._tp.check_tape
        c = int(self._c)
        u, d, l = c&1, c&2, c&4
        r, b, a = c&8, c&16, c&32
        cd = int(ch(x, y-1))
        crd = int(ch(x+1, y-1))
        cld = int(ch(x-1, y-1))
        cl = int(ch(x-1, y))
        cr = int(ch(x+1, y))
        cu = int(ch(x, y+3))
        falling = 0 if (cd | cld | crd | cl | cr) else 1
        self._air = falling <<1|1
        if falling and not a:
            self._hold = 0 <<1|1
        hold = int(self._hold)
        # CONTROLS: Grappling hook swing
        if mode == 11:
            ang = int(self._hook_ang)
            vel = int(self._hook_vel)
            leng = int(self._hook_len)
            hx, hy = int(self._hx), int(self._hy)
            g = (ang>>8)*(ang>>8)>>9
            vel = (# Swing speed limit
                (3584 if vel > 3584 else -3584 if vel < -3584 else vel)
                # Air friction
                - (((vel*vel>>9)*vel)>>21)
                # Apply gravity
                + (g if ang < 0 else 0-g)
                # CONTROLS: swing
                + (40 if r else -40 if l else 0))
            # CONTROLS: climb/extend rope
            leng += -128 if u and leng > 0 else 128 if d and not cu else 0
            # Check land interaction conditions
            if cu or (not falling and vel*ang > 0):
                # Rebound off ceiling
                vel = 0-vel
                ang += vel*2
            elif not (falling or a): # Stick to ceiling if touched
                self.mode = 12 <<1|1
                self._x_vel = self._y_vel = 0 <<1|1
            # Release grappling hook with button or within a second
            # when not connected to solid roof.
            elif (hold==0 and a or (hy < 0 and t%_FPS==0)):
                self.mode = 12 <<1|1
                # Convert angular momentum to free falling momentum
                self._x_vel = (
                    (_snco[((ang>>10)-100)%400]-128)*leng>>15)*vel <<1|1
                self._y_vel = 0-(
                    (_snco[((ang>>10)+200)%400]-128)*leng>>15)*vel <<1|1
                self._hold = 1 <<1|1
            # Calculate the worm position
            self._x = (hx<<8) + ((_snco[((ang>>10)+200)%400]-128)*leng>>7) <<1|1
            self._y = (hy<<8) + ((_snco[((ang>>10)-100)%400]-128)*leng>>7) <<1|1
            # Update motion and position variables based on swing
            self._hook_ang = ang+vel <<1|1
            self._hook_vel = vel <<1|1
            self._hook_len = leng <<1|1
        elif mode == 12: # Clinging movement (without grappling hook)
            x_vel, y_vel = int(self._x_vel), int(self._y_vel)
            # CONTROLS: Activate hook
            if falling and a and hold==0 and y < 64:
                # Activate grappling hook in aim direction
                self._launch_hook(int(self._aim_ang)*dr)
            # CONTROLS: Fall (force when jumping)
            elif falling or a:
                if not falling:
                    x_vel = -32768 if l else 32768 if r else 0
                    self._hold = 1 <<1|1
                # Apply gravity to vertical speed
                y_vel += 1638
                # Update positions with momentum
                xf += x_vel>>8
                yf += y_vel>>8
            else:
                # Stop falling when attached to roof
                y_vel = 0
            self._x_vel, self._y_vel = x_vel <<1|1, y_vel <<1|1
            # CONTROLS: Apply movement
            if t%2 and y < 64:
                clu = int(ch(x-1, y+3))
                cru = int(ch(x+1, y+3))
                climb = (cd==0 and ((l and crd) or (r and cld)))
                descend = cu==0 and (((cl | clu) and l) or ((cr | cru) and r))
                lsafe = ((cld | cd | int(ch(x-2, y-1)) | int(ch(x-2, y)))
                    and l and (cl | clu)==0)
                rsafe = ((crd | cd | int(ch(x+2, y-1)) | int(ch(x+2, y)))
                    and r and (cr | cru)==0)
                xf += -256 if lsafe else 256 if rsafe else 0
                yf += -256 if climb else 256 if descend else 0
            self._x, self._y = xf <<1|1, yf <<1|1

        # Glow's rocket.
        # Apply rocket dynamics if it is active
        if self.rocket_on:
            rdir = int(self._rdir)
            rxf, ryf = int(self._rocket_x), int(self._rocket_y)
            rxv, ryv = int(self._rocket_x_vel), int(self._rocket_y_vel)
            # Apply rocket motion
            rxf += rxv
            ryf += ryv
            # Apply flight boosters
            rxv += 10*rdir
            if rxv*rdir > 0:
                ryv = ryv * 9 // 10
            # Update stored properties
            rx, ry = rxf>>8, ryf>>8
            self.rocket_x, self.rocket_y = rx <<1|1, ry <<1|1
            self._rocket_x, self._rocket_y = rxf <<1|1, ryf <<1|1
            self._rocket_x_vel, self._rocket_y_vel = rxv <<1|1, ryv <<1|1
            # Defuse if fallen through ground
            if not (80>=ry>=-1) or not (-30<=rx-int(self._tp.x[0])<=102):
                self.rocket_on = 0 <<1|1
            if ch(rx, ry): # Explode rocket if hit the ground
                self.kill(t, None)

        # Aiming and launching
        a_pow = int(self._aim_pow)
        if (u | d | b) or (not b and a_pow > 256):
            # CONTROLS: Aim rocket
            a_ang = int(self._aim_ang)
            # aiming (while not grappling)
            if (u | d) and int(self.mode) != 11 and not falling:
                a_ang += 1310 if u else -1310
                # Cap the aim angle
                a_ang = (-131072 if a_ang < -131072 else
                    0 if a_ang > 0 else a_ang)
                self._aim_ang = a_ang <<1|1
            if b: # Power rocket
                a_pow += 8
            # CONTROLS: Launch the rocket when button is released
            elif not b and a_pow > 256:
                play(rocket_flight, 180)
                self.rocket_on = 1 <<1|1
                self._rocket_x, self._rocket_y = xf <<1|1, yf+256 <<1|1
                self._rocket_x_vel = (
                    (_snco[((a_ang>>10)+200)%400]-128)*a_pow>>8)*dr <<1|1
                self._rocket_y_vel = (
                    (_snco[((a_ang>>10)-100)%400]-128)*a_pow>>8) <<1|1
                a_pow = 256
                self._rdir = dr <<1|1
            # Resolve roscket aim to the x by y vector form
            self._aim_x = (
                (_snco[((a_ang>>10)+200)%400]-128)*a_pow//3360)*dr <<1|1
            self._aim_y = ((_snco[((a_ang>>10)-100)%400]-128)*a_pow//3360) <<1|1
            self._aim_pow = a_pow <<1|1
        aim_x = int(self._aim_x)
        if (l | r) and aim_x*dr > 0:
            self._aim_x = 0-aim_x <<1|1

    @micropython.viper
    def _tick_respawn(self):
        ### After the player dies, a respawn process begins,
        # showing a death message, while taking Umby back
        # to a respawn point on a new starting platform.
        # This handles a game tick when a respawn process is
        # active.
        ###
        tape = self._tp
        xf = int(self._x)
        yf = int(self._y)
        rex = int(self._respawn_x)
        # Move player towards the respawn location
        if xf > rex:
            self._x = xf-256 <<1|1
            self._y = (yf + 0 if (yf>>8) == 20 else
                yf+256 if (yf>>8) < 20 else yf-256) <<1|1
            if xf < rex + 4680:
                # Draw the starting platform
                tape.redraw_tape(2, (xf>>8)-5, pattern_room, pattern_fill)
        else:
            # Cancel any rocket powering
            self._aim_pow = 256 <<1|1
            # Hide any death message
            tape.clear_overlay()
            # Return to normal play modes
            if int(self.mode) == 201:
                self.mode = 0 <<1|1
            else:
                # Shoot hook straight up
                self._x_vel = self._y_vel = 0 <<1|1
                self._launch_hook(0)
            tape.write(1, "DONT GIVE UP!", int(tape.midx[0])+8, 26)

    @micropython.native
    def _tick_testing(self):
        ### Handle one game tick for when in test mode.
        # Test mode allows you to explore the level by flying,
        # free of interactions.
        ###
        self._y += -256 if self._c&1 else 256 if self._c&2 else 0
        self._x += -256 if self._c&4 else 256 if self._c&8 else 0
        # Switch to characters if buttons are pressed
        if not self._c&8:
            self.mode = 0 if self._c&16 else 10 if self._c&32 else 199

    @micropython.viper
    def draw(self, t: int):
        mode = int(self.mode)
        tape = self._tp
        p = int(tape.x[0])
        py = int(tape.x[1])
        x_pos, y_pos = int(self.x) - p, int(self.y)
        m = int(self._moving)
        d = int(self.dir)
        air = int(self._air)
        # Get animation frame
        # Steps through 0,1,2,3 every half second for animation
        # of looking left and right, and changes to movement art of
        # 4 when moving left and 5 when moving right.
        f = t*2//_FPS%4 if not m else 4 if d < 0 else 5
        abl = t*6//_FPS%2 # aim blinker
        # Draw rocket, if active
        if self.rocket_on:
            hx, hy = int(self.rocket_x), int(self.rocket_y)
            rdir = int(self._rdir)
            tape.draw(1, hx-p-1, hy-7, _aim, 3, 0)#head
            tape.draw(0, hx-p+(-3 if rdir>0 else 1), hy-7, _aim, 3, 0)#tail
        # Test mode or offscreen
        if mode == 199 or not (-2 < x_pos < 73 and -1 < y_pos-py < 42):
            hx = 0 if x_pos < -1 else 69 if x_pos > 72 else x_pos-1
            hy = py-5 if y_pos < py else py+32 if y_pos > py + 41 else y_pos-6
            tape.draw(abl, hx, hy, _aim, 3, 0)
            tape.mask(1, hx, hy, _aim_fore_mask, 3, 0)
            return
        # Select the character specifics
        umby = mode == 0 or mode == 201
        sdw = (_u_sdw if not air else _u_sdw_air) if umby else _g_sdw
        art = _u_art if umby else _g_art
        hy = y_pos-2
        by = y_pos-6 if umby else y_pos-1
        # Draw Umby's or Glow's layers and masks
        tape.draw(0, x_pos-1, hy, sdw, 3, f) # Shadow
        tape.draw(1, x_pos-1, hy, art, 3, f) # Umby
        tape.mask(1, x_pos-1, hy, sdw, 3, f)
        tape.mask(0, x_pos-4, by, _ug_back_mask, 9, 0)
        # Aims and hooks
        if mode == 11: # Activated grappling hook rope
            hook_x, hook_y = int(self._hx), int(self._hy)
            # Draw Glow's grappling hook rope
            for i in range(0, 8):
                sx = x_pos + (hook_x-(x_pos+p))*i//8
                sy = y_pos + (hook_y-y_pos)*i//8
                tape.draw(1, sx-1, sy-6, _aim, 3, 0)
            hx, hy = hook_x-p-1, hook_y-6
        aim_x, aim_y = int(self._aim_x), int(self._aim_y)
        if not self.ai and not self._coop: # Only main player has aiming
            # Rocket aim
            hx = x_pos+aim_x-1
            hy = y_pos+aim_y-6
            tape.draw(abl, hx, hy, _aim, 3, 0)
            tape.mask(1, hx, hy, _aim_fore_mask, 3, 0)
            tape.mask(0, hx-1, hy+1, _aim_back_mask, 5, 0)
