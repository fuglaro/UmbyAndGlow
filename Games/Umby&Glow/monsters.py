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
from audio import *

### Bones is a monster that flyes about then charges the player.
# Bones looks a bit like a skull.
# It will fly in a random direction, in a jaggard manner,
# until it hits a wall in which case
# it will change direction again. There is a small chance that
# Bones will fly over walls and ground and Bones will continue until
# surfacing. If Bones goes offscreen to the left + 72 pixels, it will die;
# offscreen to the top or bottom, it will change direction.
# It will also change direction on occasion.
# When the player is within a short range, Bones will charge the player
# and will not stop.
###
### Molaar is a pillar-head style land crawler but only goes
# counter-clockwise (around land), and also jumps high on flat surfaces.
# Jump direction is randomly forwards or backwards.
# Also turns downwards if roof crawling and goes offscreen to the right.
# Made of head, feet and tail. Middle of feet is the center of the monster.
# Head shifts relative to feet based on direction, and the head shifts
# When charging to shoot left. Also has tail that moves up when standing or
# Jumping, and down when climbing or clinging.
###
# All monsters will diw if they go offscreen to the left + 72 pixels but
# some monsters have avoidance tactics.
_Bones = const(1) # Random flying about
_BonesBoss = const(2) # Main monster of the Boss Bones swarm
_DragonBones = const(3) # Head monster of the Dragon Bones chain
_ChargingBones = const(4) # Charging player
_ChargingBonesFriend = const(5) # Charging other player
_Skittle = const(6) # Bug that just flies straight to the left at player
_Fireball = const(7) # Projectile that just flies straight to the left
# Gap for Monster projectiles here
_Stomper = const(20) # Swings up and down vertically
_Molaar = const(21) # Crawls around edges of land, shooting fireballs
_MolaarHanging = const(22) # Mode: hanging from roof
_MolaarClimbing = const(23) # Mode: climbing upwards
_MolaarCharging = const(24) # Mode: charing fireball
_MolaarHangingCharging = const(25) # Mode: charing fireball and roof hanging
_MolaarClimbingCharging = const(26) # Mode: charing fireball and climbing up
_Pillar = const(27) # Crawls with a catepillar-chain around edges of land
_PillarTail = const(28)
_Hoot = const(29) # Owl-like monster that blinks and swoops.
Bones = _Bones
BonesBoss = _BonesBoss
DragonBones = _DragonBones
ChargingBones = _ChargingBones
Skittle = _Skittle
Fireball = _Fireball
Stomper = _Stomper
Molaar = _Molaar
Pillar = _Pillar
Hoot = _Hoot

# Additional hidden bahaviour data
_data = array('I', 0 for i in range(48*5))

class Monsters:
    #=== Bones & BossBones: Janky flying, charging in range. (and boss swarm)
    # BITMAP: width: 7, height: 8, frames: 3
    _bones = bytearray([28,54,147,110,147,54,28,28,190,159,110,159,190,28,28,
        242,139,222,139,242,28])
    # BITMAP: width: 9, height: 8
    _bones_m = bytearray([28,62,247,243,239,243,247,62,28])
    #=== Skittle (flies straight across screen to the left)
    # BITMAP: width: 8, height: 8
    _skittle = bytearray([56,84,56,124,56,124,56,16])
    # BITMAP: width: 9, height: 8
    _skittle_m = bytearray([56,124,254,124,254,124,254,124,56])
    #=== Fireball (flies straight across screen to the left)
    # BITMAP: width: 8, height: 8
    _fireball = bytearray([56,124,124,124,56,56,16,16])
    # BITMAP: width: 8, height: 8
    _fireball_m = bytearray([124,198,186,186,186,186,186,186])
    #=== Stomper (swings up and down vertically)
    # BITMAP: width: 7, height: 8
    _stomper = bytearray([36,110,247,124,247,110,36])
    # BITMAP: width: 7, height: 8
    _stomper_m = bytearray([239,255,255,254,255,255,239])
    #=== Pillar (catepillar-chain crawls across the edge of the foreground)
    # BITMAP: width: 7, height: 8
    _pillar_head = bytearray([2,62,228,124,228,62,2])
    # BITMAP: width: 7, height: 8
    _pillar_head_m = bytearray([63,255,255,254,255,255,63])
    # BITMAP: width: 7, height: 8
    _pillar_tail = bytearray([66,189,66,90,66,189,66])
    # BITMAP: width: 7, height: 8
    _pillar_tail_m = bytearray([126,255,255,255,255,255,126])
    #=== Hoot (blinks and swoops like an owl)
    # BITMAP: width: 9, height: 8
    _hoot = bytearray([114,142,156,248,112,248,156,142,114])
    # BITMAP: width: 7, height: 8
    _hoot_blink = bytearray([112,96,0,0,0,96,112])
    #=== Molaar (crawls counter-clockwise around land, jumps high, and shoots)
    # BITMAP: width: 8, height: 8, frames: 2 (default head, charging head)
    _molaar_head = bytearray([44,70,100,78,107,73,38,30,
        102,195,230,134,203,137,230,126])
    # BITMAP: width: 6, height: 8
    _molaar_feet = bytearray([24,52,36,36,44,24])
    # BITMAP: width: 6, height: 8
    _molaar_feet_m = bytearray([60,126,255,255,126,60])
    # BITMAP: width: 4, height: 8, frames: 2 (up tail, down tail)
    _molaar_tail = bytearray([192,234,127,41,131,215,126,84])
    # BITMAP: width: 8, height: 8
    _block = bytearray([255,255,255,255,255,255,255,255]) # Mask (8x8 full)


    def __init__(self, tape):
        ### Engine for all the different monsters ###
        self._tp = tape
        self._px = 0 # x pos for left edge of the active tape area
        # Types of all the monsters
        self._tids = bytearray(0 for i in range(48))
        # x positions of all the monsters
        self.x = array('I', 0 for i in range(48))
        # y positions start at 64 pixels above top of screen
        self.y = bytearray(0 for i in range(48))
        # Number of monsters active
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

    @micropython.native
    def is_alive(self, mon):
        ### Check if a specific monster is alive ###
        return bool(self._tids[mon])

    @micropython.viper
    def add(self, mon_type: int, x: int, y: int) -> int:
        ### Add a monster of the given type.
        # @returns: the index of the spawned monster, or -1
        ###
        # Find an empty monster slot
        tids = ptr8(self._tids)
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        d = ptr32(_data)
        # Find the next monster slot
        for i in range(48):
            if tids[i] == 0:
                break
        else: # Monster buffer full
            return -1
        # Create the new monster
        self.num = (int(self.num)+1) <<1|1
        tids[i] = mon_type
        xs[i], ys[i] = x, y+64
        ii = i*5
        d[ii] = d[ii+1] = d[ii+2] = d[ii+3] = d[ii+4] = 0

        # Set any monster specifics
        if mon_type == _BonesBoss:
            d[ii+4] = 20 # Starting numbr of monsters in the swarm
        elif mon_type == _Bones:
            d[ii+4] = int(self._tp.x[0]) # Movement rate type
        elif mon_type == _Skittle:
            ys[i] = 64 + int(self._tp.players[0].y) # Target player 1
        elif mon_type == _Pillar or mon_type == _DragonBones:
            # Make all the sections in the chain
            k = i
            for j in range(16 if mon_type == _DragonBones else 5):
                kn = int(self.add(_PillarTail, x, y))
                if kn > k:
                    k = kn
            # Swap the tail for the head is protected by body.
            tids[i] = _PillarTail
            tids[k] = mon_type
            if mon_type == _Pillar:
                # Set the turn direction (1=clockwise)
                d[k*5+1] = x%2
            elif mon_type == _DragonBones:
                d[k*5+4] = 1 # Movement rate
            i = k
        elif mon_type == _Molaar:
            d[ii] = 2 # Start searching edge upwards
            d[ii+2] = x*3 # Charging start offset
        elif mon_type == _Hoot:
            d[ii] = x
            d[ii+1] = d[ii+3] = y
        return i

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
                self._hit_monster(t, i, None)

            ## Handle each monster type ##
            typ = tids[i]
            # Bones and BonesBoss
            if typ == _Bones and  t%2==0:
                self._tick_bones(t, i)
            elif typ == _BonesBoss:
                self._tick_bones_boss(t, i)
            ## DragonBones
            elif typ == _DragonBones:
                self._tick_dragon_bones(t, i)
            ## Charging Bones
            elif _ChargingBones <= typ <= _ChargingBonesFriend and t%4==1:
                self._tick_bones_charging(t, i)
            ## Skittle
            elif (_Skittle <= typ <= _Fireball) and t%2:
                xs[i] -= 1 # Just fly straight left
            ## Pillar and Molaar
            elif _Molaar <= typ <= _Pillar and t%3==0:
                self._tick_pillar(t, i)
            ## Hoot
            elif typ == _Hoot and t%2==1:
                self._tick_hoot(t, i)

    @micropython.viper
    def _tick_bones(self, t: int, i: int):
        ### Bones behavior
        # * janky movement mostly avoiding walls,
        # * some move faster than others, some with no movement (until in range)
        # * switching to charging behavior when player in range
        ###
        xs, ys = ptr32(self.x), ptr8(self.y)
        x, y = xs[i], ys[i]-64
        tids = ptr8(self._tids)
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
        if (th+i)%20==0 and tids[i] == _Bones:
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
    def _tick_dragon_bones(self, t: int, i: int):
        ### Dragon with a bones head, and a chain of Pillar tails,
        # Also shoots fireballs
        ###
        plyrs = self._tp.players
        tids = ptr8(self._tids)
        xs, ys = ptr32(self.x), ptr8(self.y)
        ii = i*5
        s = t//16%2 # every other section moves, alternatively
        # Shoot Fireball projectiles
        if t%240==0:
            self.add(_Fireball, xs[i], ys[i]-64)
        # Move the head
        if int(plyrs[0].x) > xs[i]: # Charge rapidly if worm sneaks past
            self._tick_bones_charging(t, i)
        elif t%3: # Standard random Bones movements
            self._tick_bones(t, i)
        elif t%10==0: # Drift over time towards player
            self._tick_bones_charging(t, i)
        oy = -4 # Neck bend
        # Move the tail
        ht = 0 # has tail?
        mon = i
        for j in range(i-1, -1, -1):
            if tids[j] == _Pillar or tids[j] == _DragonBones:
                break # Another head, we are done on this chain
            elif tids[j] == _PillarTail:
                s = (s+1)%2 # Alternating sections move
                if s: # Follow the head, in a chain
                    d = xs[i]-xs[j]
                    xs[j] += 1 if d > 0 else -1 if d < 0 else 0
                    d = ys[i]-ys[j] + oy
                    oy = 0
                    ys[j] += 1 if d > 0 else -1 if d < 0 else 0
                i = j # Each section follows the other
                ht = 1
        if ht==0: # Switch to charging bones if no tail
            tids[mon] = _ChargingBones

    @micropython.viper
    def _tick_bones_charging(self, t: int, i: int):
        ### Charging Bones behavior ###
        # Find the player position to charge
        plyrs = self._tp.players
        tids = ptr8(self._tids)
        typ = tids[i]
        if typ != _ChargingBonesFriend:
            px = int(plyrs[0].x)
            py = int(plyrs[0].y)
        elif int(len(plyrs)) > 1:
            px = int(plyrs[1].x)
            py = int(plyrs[1].y)
        else:
            return
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        x, y = xs[i], ys[i]-64
        # Slowlyish charge the player position
        xs[i] += 1 if x < px else -1 if x > px else 0
        ys[i] += 1 if y < py else -1 if y > py else 0

    @micropython.viper
    def _tick_pillar(self, t: int, i: int):
        ### Pillar behavior: catepillar crawling around edges of foreground ###
        ### Molaar behavior: crawls along edges shooting fireballs ###
        tids = ptr8(self._tids)
        tid = tids[i]
        xs, ys = ptr32(self.x), ptr8(self.y)
        x, y = xs[i], ys[i]-64
        ch = self._tp.check_tape
        data = ptr32(_data)
        ii = i*5
        s = t//30%2 # every other section moves, alternatively
        # Move the head
        if s or tid != _Pillar:
            px = int(self._px)
            d = data[ii] # direction of movement (down:0/left:1/up:2/right:3)
            r = data[ii+1] # rotation direction
            if ch(x, y): # Try to find an edge from within solid foreground
                xs[i] -= 1
                ys[i] += -1 if t%250<100 and y > 4 else 1 if y < 60 else 0
            else:
                # Prepare edge crawling detection and turn variables
                npx = 1 if d==3 else -1 if d==1 else 0
                npy = 1 if d==0 else -1 if d==2 else 0
                spx = -1 if 1<=d<=2 else 1
                spy = 1 if d<=1 else -1
                tpx, tpy = 0-npx, npy
                # Apply anti-clockwise/clockwise modifiers
                rd = 1 if r else -1
                if r:
                    tpx, tpy = 0-tpx, 0-tpy
                    spx, spy = spx if npx else 0-spx, spy if npy else 0-spy
                # Crawl around edges of platforms, or search for edges
                cp = ch(x+npx, y+npy)
                if not cp and (ch(x+spx, y+spy) or not ch(x+tpy, y+tpx)):
                    # Move in direction facing
                    xs[i] += npx
                    ys[i] += npy
                else:
                    # Turn round a corner
                    data[ii] = (d-rd)%4 if cp else (d+rd)%4
                    ys[i] += 0 if cp else npy
                    xs[i] += 0 if cp else npx
                # Dont fly offscreen,
                if d==0 and ys[i] > 127:
                    data[ii] = 2
                elif d==2 and ys[i] < 64:
                    data[ii] = 0
                if ys[i] > 127:
                    ys[i] = 127
                elif ys[i] < 64:
                    ys[i] = 64
                # or too far to the right
                elif d==3 and x > px+108:
                    if tid == _Pillar:
                        # Turn back the other way
                        data[ii] = 1
                        data[ii+1] = 0 if r else 1
                    else:
                        # Turn down
                        data[ii] = 0

        # Update mode (and bail) for Molaar
        if _Molaar <= tid <= _MolaarClimbingCharging:
            _old_tid = tids[i]
            if t%4==0:
                tids[i] = (_Molaar if d<=1 else _MolaarClimbing if d==2
                    else _MolaarHanging)
                # Update charging
                if (t+data[ii+2])%180<50:
                    tids[i] += 3
                elif _old_tid > _MolaarClimbing:
                    # Released charge - launch fireball
                    self.add(_Fireball, x-9, y +
                        (3 if _old_tid==_MolaarHangingCharging else -4))
            return

        # Move the tail (for Pillar)
        for j in range(i-1, -1, -1):
            if tids[j] == _Pillar or tids[j] == _DragonBones:
                break # Another head, we are done on this chain
            elif tids[j] == _PillarTail:
                s = (s+1)%2 # Alternating sections move
                if s: # Follow the head, in a chain
                    d = xs[i]-xs[j]
                    xs[j] += 1 if d > 0 else -1 if d < 0 else 0
                    d = ys[i]-ys[j]
                    ys[j] += 1 if d > 0 else -1 if d < 0 else 0
                i = j # Each section follows the other

    @micropython.viper
    def _tick_hoot(self, t: int, i: int):
        ### Hoot behavior: lurking then swooping every now and then ###
        data = ptr32(_data)
        ii = i*5
        t//=2
        xs, ys = ptr32(self.x), ptr8(self.y)
        x, y = xs[i], ys[i]-64
        tr = (t+i*97)%200
        if tr==0:
            # Set new swoop location
            data[ii], data[ii+1] = x, y
            data[ii+2] = t*x*y%100-50
            data[ii+3] = (t^(x*y))%50+5
            # Dont fly too far off to the right
            if data[ii+3] > int(self._px) + 400:
                data[ii+3] = int(self._px) + 400
        elif tr <= 50:
            # Exececute the swoop
            xs[i] = data[ii] + data[ii+2]*tr//50
            ys[i] = 64 + data[ii+1] + (data[ii+3]-data[ii+1])*tr//50
            # Add curve to swoop
            ys[i] += 20 - ((20-tr)*(20-tr)//20 if tr < 20
                else (tr-30)*(tr-30)//20 if tr >= 30 else 0)

    @micropython.viper
    def draw_and_check_death(self, t: int, p1, p2):
        ### Draw all the monsters checking for collisions ###
        tape = self._tp
        ch = tape.check
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
            x = xs[i]-tpx
            # Monsters in the distance get drawn to background layers
            l = 1 if -36 <= x-px < 108 else 0
            self._draw_monster(t, tids[i], x, ys[i]-64, l)

            # Check if a rocket hits this monster
            if r1 and ch(r1x, r1y, 224):
                self._hit_monster(t, i, p1)
                r1 = 0 # Done with this rocket
            # Check if ai helper's rocket hits the monster
            elif r2 and ch(r2x, r2y, 224):
                self._hit_monster(t, i, p2)
                r2 = 0 # Done with this rocket

    @micropython.viper
    def _draw_monster(self, t: int, tid: int, x: int, y: int, l: int):
        ### Draw a single monster ###
        tape = self._tp
        pf = 0 # Animation frame number

        # Bones class types
        if _Bones <= tid <= _ChargingBonesFriend:
            pf = 2 if tid != _Bones else 0 if t//10 % 6 else 1
            img, msk = self._bones, self._bones_m
            px, py, pw = -3, -4, 7
            mx, my, mw = -4, -4, 9
            # Draw additional mask
            tape.mask(0, mx, my, msk, 9, 0) # Mask Back
        # Skittle type
        elif tid == _Skittle:
            img, msk = self._skittle, self._skittle_m
            px, py, pw = 0, -4, 8
            mx, my, mw = -1, -4, 9
        # Fireball type
        elif tid == _Fireball:
            img, msk = self._fireball, self._fireball_m
            px, py, pw = 0, -4, 8
            mx, my, mw = 0, -4, 8
        # Stomper type
        elif tid == _Stomper:
            img, msk = self._stomper, self._stomper_m
            m = (y*16+t)%440
            px, py, pw = -3, (m if m < 50 else 50 if m < 170 else 220-m
                if m < 220 else 0)+3-y, 7
            mx, my, mw = -3, py, 7
        # Molaar type
        elif _Molaar <= tid <= _MolaarClimbingCharging:
            img, msk = self._molaar_feet, self._molaar_feet_m
            px, py, pw = -3, -4, 6
            mx, my, mw = -3, -4, 6
            # Handle Charging
            hf = 0 if tid < _MolaarCharging else 1
            hpx = 0 if tid < _MolaarCharging else 2
            # Switch to non-charging equvalent
            tid -= 0 if tid < _MolaarCharging else 3
            # Draw head
            hpx += -5 if tid==_Molaar else -2 if tid==_MolaarClimbing else -9
            hpy = 0 if tid==_MolaarHanging else -8
            hpx += t//40%2 # Gait
            tape.draw(l, x+hpx, y+hpy, self._molaar_head, 8, hf)
            tape.mask(l, x+hpx, y+hpy, self._block, 8, 0)
            # Draw tail
            hpy = -9 if tid==_Molaar else 0
            hpf = 0 if tid==_Molaar else 1
            hpy += 1 if t%20<6 else 0 # Gait
            tape.draw(l, x+3, y+hpy, self._molaar_tail, 4, hpf)
        # Pillar type
        elif tid == _Pillar:
            img, msk = self._pillar_head, self._pillar_head_m
            px, py, pw = -3, -4, 7
            mx, my, mw = -3, -4, 7
        elif tid == _PillarTail:
            img, msk = self._pillar_tail, self._pillar_tail_m
            px, py, pw = -3, -4, 7
            mx, my, mw = -3, -4, 7
        # Hoot type
        elif tid == _Hoot:
            img, msk = self._hoot, self._hoot_blink
            px, py, pw = -4, -5, 9
            mx, my, mw = -3, -5, 7 if t%120<10 or 20<t%120<30 else 0
            # Draw open eyes
            tape.draw(0, x+mx, y+my, msk, 0 if mw else 7, 0)

        # Draw the common layers
        tape.draw(l, x+px, y+py, img, pw, pf)
        tape.mask(l, x+mx, y+my, msk, mw, 0)


    @micropython.viper
    def _kill(self, t: int, mon: int, player, tag):
        ptr8(self._tids)[mon] = 0
        self.num = int(self.num) - 1 <<1|1
        if player:
            # Explode the rocket
            player.detonate(t)
            # Tag the wall with a death message,
            self._tp.tag(tag, ptr32(self.x)[mon], ptr8(self.y)[mon]-64)
            play(rocket_kill, 30)

    @micropython.viper
    def _hit_monster(self, t: int, mon: int, player):
        ### Trigger for a player shooting a monster ###
        tids = ptr8(self._tids)
        tid = tids[mon]
        tag = "_RIP_"

        # Monster specific damage behaviors
        if tid == _Pillar: # Direct hit!
            for j in range(mon-1, -1, -1):
                if tids[j] == _Pillar:
                    break # Another head, we are done on this chain
                elif tids[j] == _PillarTail: # Destroy entire chain
                    self._kill(t, j, player, "_RIP_")

        elif tid == _PillarTail or tid == _DragonBones:
            tag = "_OUCH!_"
            # Destroy last tail segment instead
            for j in range(mon-1, -1, -1):
                if tids[j] == _Pillar:
                    break # Another head, we are done on this chain
                elif tids[j] == _PillarTail:
                    mon = j

        # Wipe the monster, do the explosion, and leave a death message
        self._kill(t, mon, player, tag)
