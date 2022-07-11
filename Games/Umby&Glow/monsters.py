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

################################################################
# Monster ideas and examples
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
# TODO: forest - owl eyes. Blink twice * 3, then swoop to new location ()
################################################################

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
_BonesBoss = const(2) # Main monster of the Boss Bones swarm
_ChargingBones = const(3) # Charging player
_ChargingBonesFriend = const(4) # Charging other player
Bones = _Bones
ChargingBones = _ChargingBones
BonesBoss = _BonesBoss

# Additional hidden bahaviour data
_data = array('I', 0 for i in range(48*5))

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
        ### Add a monster of the given type. ###
        # Find an empty monster slot
        tids = ptr8(self._tids)
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        d = ptr32(_data)
        # Find the next monster slot
        for i in range(48):
            if tids[i] == 0:
                break
        # Create the new monster
        tids[i] = mon_type
        xs[i] = x
        ys[i] = y+64
        ii = i*5
        d[ii] = 0
        d[ii+1] = 0
        d[ii+2] = 0
        d[ii+3] = 0
        d[ii+4] = 0
        # Set any monster specifics
        if mon_type == _BonesBoss:
            d[ii+4] = 20 # Starting numbr of monsters in the swarm
        if mon_type == _Bones:
            d[ii+4] = int(self._tp.x[0]) # Movement rate type
        # Increment the counter
        self.num = (int(self.num)+1) <<1|1

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

        # Loop through all the monsters, updating ticks
        tids = ptr8(self._tids)
        xs = ptr32(self.x)
        for i in range(48):
            if tids[i] == 0:
                continue
            # Check for standard death conditions
            if xs[i] < tpx - 72: # Too far left, destroy monster
                tids[i] = 0
                self.num = (int(self.num)-1) <<1|1

            ## Handle each monster type ##
            typ = tids[i]
            # Bones and BonesBoss
            if typ == _Bones:
                if t%2==0:
                    self._tick_bones(t, i)
            elif typ == _BonesBoss:
                self._tick_bones_boss(t, i)
            ## Charging Bones
            elif _ChargingBones <= typ <= _ChargingBonesFriend:
                if t%4==1:
                    self._tick_bones_charging(t, i)

    @micropython.viper
    def _tick_bones(self, t: int, i: int):
        ### Bones behavior
        # * janky movement mostly avoiding walls,
        # * some move faster than others, some with no movement (until in range)
        # * switching to charging behavior when player in range
        ###
        xs, ys = ptr32(self.x), ptr8(self.y)
        x, y = xs[i], ys[i]-64
        data = ptr32(_data)
        ii = i*5
        th = t//2
        thi = th-i%10
        dx, dy = data[ii], data[ii+1]
        # Find the next position
        nx = x + (data[ii+2] if thi%20>dx else 0)
        ny = y + (data[ii+3] if thi%20>dy else 0)
        # Change direction if needed
        tape = self._tp
        ch = tape.check_tape
        if (dx | dy == 0 or ny < 0 or ny > 63 or thi%129==0
            or ((ch(nx, ny) and th%13 and not (ch(x, y))))):
            data[ii], data[ii+1] = th%20, 20-(th%20)
            data[ii+2] = -1 if th%2 else 1
            data[ii+3] = -1 if th%4>1 else 1
        # Otherwise continue moving
        elif th%(data[ii+4]%5+1):
            xs[i], ys[i] = nx, ny+64
        # Check for charging conditions
        if (th+i)%20==0:
            tids = ptr8(self._tids)
            plyrs = tape.players
            p1 = int(len(plyrs)) > 0
            p1x = int(plyrs[0].x) if p1 else 0
            p1y = int(plyrs[0].y) if p1 else 0
            p2 = int(len(plyrs)) > 1
            p2x = int(plyrs[1].x) if p2 else 0
            p2y = int(plyrs[1].y) if p2 else 0
            if p1 and (p1x-x)*(p1x-x) + (p1y-y)*(p1y-y) < 300:
                tids[i] = _ChargingBones
            if p2 and (p2x-x)*(p2x-x) + (p2y-y)*(p2y-y) < 300:
                tids[i] = _ChargingBonesFriend

    @micropython.viper
    def _tick_bones_boss(self, t: int, i: int):
        ### BonesBoss behavior
        # * Moves slowly towards 10px to the left of the last Bones
        # * Spawns 20 Bones quickly
        # * Spawns up to 10 Bones slowly
        # * Rallies all Bones in the 30 pixel range to the left
        ###
        tids = ptr8(self._tids)
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        typ = tids[i]
        x = xs[i]
        y = ys[i]-64
        data = ptr32(_data)
        ii = i*5
        xj, yj = x, y
        if t%2:
            ci = 0
            # Swarm minions around boss
            for j in range(48):
                if tids[j] != _Bones:
                    continue
                ci += 1
                dx = data[j*5+2]
                xj, yj = xs[j], ys[j]-64
                if xj < x-30 and dx == -1:
                    data[j*5+2] = 1
                elif xj > x and dx == 1:
                    data[j*5+2] = -1

                # Movement of central boss brain itself.
                if t//20%20==ci:
                    # Make sure the minion moves a little
                    data[j*5+4] += 1
                    # Move towards position just behind minion
                    xs[i] += -1 if xj < x-10 else 1
                    ys[i] += -1 if yj < y else 1
            # Spawn starting minions and slowly spawn in fresh monsters
            if (ci < 10 and t%180==1) or (t%15==0 and data[ii+4] > 0):
                data[ii+4] -= 1
                self.add(_Bones, x, y)

    @micropython.viper
    def _tick_bones_charging(self, t: int, i: int):
        ### Charging Bones behavior ###
        # Find the player position to charge
        plyrs = self._tp.players
        tids = ptr8(self._tids)
        typ = tids[i]
        if typ == _ChargingBones:
            px = int(plyrs[0].x)
            py = int(plyrs[0].y)
        elif int(len(plyrs)) > 1:
            px = int(plyrs[1].x)
            py = int(plyrs[1].y)
        else:
            return
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        x = xs[i]
        y = ys[i]-64
        # Slowlyish charge the player position
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
                self.num = (int(self.num)-1) <<1|1
                p1.kill(t, (xs[i], y))
                r1 = 0 # Done with this rocket
            # Check if ai helper's rocket hits the monster
            elif r2 and ch(r2x, r2y, 224):
                tids[i] = 0
                self.num = (int(self.num)-1) <<1|1
                p2.kill(t, (xs[i], y))
                r2 = 0 # Done with this rocket

