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

## Monster types including their AI ##

from array import array

_FPS = const(60)


# TODO: Some monster ideas

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
# TODO: catepillar monster that is a chain of monsters.



### Bones is a monster that flyes about then charges the player.
# Bones looks a bit like a skull.
# It will fly in a random direction, in a jaggard manner,
# until it hits a wall in which case
# it will change direction again. There is a small chance that
# Bones will fly over walls and ground and Bones will continue until
# surfacing. If Bones goes offscreen to the left + 72 pixels, it will die;
# offscreen to the top or bottom plus 10, it will change direction.
# It will also change direction on occasion.
# When the player is within a short range, Bones will charge the player
# and will not stop.
###
_Bones = const(1) # Random flying about
_ChargingBones = const(2) # Charging player
_ChargingBonesFriend = const(3) # Charging other player
Bones = _Bones
ChargingBones = _ChargingBones

# Additional hidden bahaviour data
_data = array('I', 0 for i in range(48*4))

class Monsters:
    # BITMAP: width: 7, height: 8, frames: 3
    _bones = bytearray([28,54,147,110,147,54,28,28,190,159,110,159,190,28,28,
        242,139,222,139,242,28])
    # BITMAP: width: 9, height: 8
    _bones_m = bytearray([28,62,247,243,239,243,247,62,28])

    def __init__(self, tape):
        ### Engine for all the different monsters ###
        self._tp = tape
        self._px = 0 # x pos for left edge of the active tape area
        self._tids = bytearray(0 for i in range(48))
        self.x = array('I', 0 for i in range(48))
        # y positions start at 64 pixels above top of screen
        self.y = bytearray(0 for i in range(48))
        self.num = 0 # Note this won't be updated if object driven by network

    @micropython.viper
    def port_out(self, buf: ptr8):
        ### Dump monster data to the output buffer for sending to player 2 ###
        px = buf[0]<<24 | buf[1]<<16 | buf[2]<<8 | buf[3]
        # Loop through each monster
        tids = ptr8(self._tids)
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        for i in range(48):
            x = xs[i]
            # Add monster to buffer (disabling if out of range)
            buf[16+i*3] = tids[i] if 0 < x-px <= 256 else 0
            buf[17+i*3] = x-px
            buf[18+i*3] = ys[i]
        # Clear remainder of buffer
        for i in range(i+1, 48):
            buf[16+i*3] = 0 # Disable monster (not active)

    @micropython.viper
    def port_in(self, buf: ptr8):
        ### Unpack monster data from input buffer recieved from player 2 ###
        px = buf[0]<<24 | buf[1]<<16 | buf[2]<<8 | buf[3]
        self._px = px <<1|1
        # Loop through each monster
        tids = ptr8(self._tids)
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        for i in range(48):
            tids[i] = tid = buf[16+i*3]
            if tid:
                xs[i] = buf[17+i*3]+px
                ys[i] = buf[18+i*3]

    @micropython.viper
    def add(self, mon_type: int, x: int, y: int):
        ### Add a monster of the given type ###
        # Find an empty monster slot
        tids = ptr8(self._tids)
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        d = ptr32(_data)
        for i in range(48):
            if tids[i] == 0 or i == 47:
                # Create the new monster
                tids[i] = mon_type
                xs[i] = x
                ys[i] = y+64
                d[i*4] = 0
                d[i*4+1] = 0
                d[i*4+2] = 0
                d[i*4+3] = 0
                # Increment the counter
                self.num = int(self.num) + 1 <<1|1
                break

    @micropython.viper
    def clear(self):
        ### Remove all monsters ###
        tids = ptr8(self._tids)
        for i in range(48):
            tids[i] = 0
        self.num = 0 <<1|1

    @micropython.viper
    def tick(self, t: int):
        ### Update Monster dynamics one game tick for all monsters ###
        tape = self._tp
        tpx = int(tape.x[0])
        self._px = tpx <<1|1
        ch = tape.check_tape
        plyrs = tape.players
        p1 = int(len(plyrs)) > 0
        p1x = int(plyrs[0].x) if p1 else 0
        p1y = int(plyrs[0].y) if p1 else 0
        p2 = int(len(plyrs)) > 1
        p2x = int(plyrs[1].x) if p2 else 0
        p2y = int(plyrs[1].y) if p2 else 0

        # Loop through all the monsters, updating ticks
        tids = ptr8(self._tids)
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        data = ptr32(_data)
        for i in range(48):
            if tids[i] == 0:
                continue
            i4 = i*4
            typ = tids[i]
            x = xs[i]
            y = ys[i]-64

            # Check for standard death conditions
            if x < tpx - 72: # Too far left, destroy monster
                tids[i] = 0
                self.num = int(self.num) - 1 <<1|1

            # Bones
            if typ == _Bones:
                if t%2:
                    continue
                t = t//2
                dx, dy = data[i4], data[i4+1]
                # Find the next position
                nx = x + (data[i4+2] if t%20>dx else 0)
                ny = y + (data[i4+3] if t%20>dy else 0)
                # Change direction if needed
                if (dx | dy == 0 or ny < -4 or ny > 68 or t%129==0
                    or ((ch(nx, ny) and t%13
                        and not (ch(x, y) or y < 0 or y >= 64)))):
                    data[i4], data[i4+1] = t%20, 20-(t%20)
                    data[i4+2] = -1 if t%2 else 1
                    data[i4+3] = -1 if t%4>1 else 1
                else: # Otherwise continue moving
                    xs[i], ys[i] = nx, ny+64
                # Check for charging conditions
                if p1 and (p1x-x)*(p1x-x) + (p1y-y)*(p1y-y) < 300:
                    tids[i] = 2 # Charge player
                if p2 and (p2x-x)*(p2x-x) + (p2y-y)*(p2y-y) < 300:
                    tids[i] = 3 # Charge friend

            # Charging Bones
            elif _ChargingBones <= typ <= _ChargingBonesFriend:
                if t%4==0: # Charge rate
                    px = p1x if typ == _ChargingBones else p2x
                    py = p1y if typ == _ChargingBones else p2y
                    xs[i] += 1 if x < px else -1 if x > px else 0
                    ys[i] += 1 if y < py else -1 if y > py else 0

    @micropython.viper
    def draw_and_check_death(self, t: int, p1, p2):
        ### Draw all the monsters checking for collisions ###
        tape = self._tp
        ch = tape.check
        draw = tape.draw
        mask = tape.mask
        tpx = int(tape.x[0])
        px = int(self._px) - tpx

        # Extract the states and positions of the rockets
        r1, r2 = 0, 0
        if p1:
            r1 = int(p1.rocket_on)
            r1x, r1y = int(p1.rocket_x)-tpx, int(p1.rocket_y)
        if p2:
            r2 = int(p2.rocket_on)
            r2x, r2y = int(p2.rocket_x)-tpx, int(p2.rocket_y)

        # Loop through all active monsters, to draw and check for monster death
        tids = ptr8(self._tids)
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        for i in range(48):
            if tids[i] == 0:
                continue
            typeid = tids[i]
            x = xs[i]-tpx
            y = ys[i]-64

            # Bones class types
            if _Bones <= typeid <= _ChargingBonesFriend:
                # Select animation frame
                f = 2 if typeid != _Bones else 0 if t*16//_FPS % 16 else 1
                # Monsters in the distance get drawn to background layers
                l = 1 if -36 <= x-px < 108 else 0
                # Draw Bones' layers and masks
                draw(l, x-3, y-4, self._bones, 7, f) # Bones
                mask(l, x-4, y-4, self._bones_m, 9, 0) # Mask Fore
                mask(0, x-4, y-4, self._bones_m, 9, 0) # Mask Backd

            # Check if a rocket hits this monster
            if r1 and ch(r1x, r1y, 224):
                tids[i] = 0
                self.num = int(self.num) - 1 <<1|1
                p1.kill(t, (xs[i], y))
                r1 = 0 # Done with this rocket
            # Check if ai helper's rocket hits the monster
            elif r2 and ch(r2x, r2y, 224):
                tids[i] = 0
                self.num = int(self.num) - 1 <<1|1
                p2.kill(t, (xs[i], y))
                r2 = 0 # Done with this rocket

