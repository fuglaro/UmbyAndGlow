## Monster types including their AI ##

from array import array
from audio import play, rocket_kill, rocket_bang
from patterns import (pattern_fill, pattern_none,
    pattern_windows, pattern_room, pattern_door)

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
_BackBones = const(2) # Background bones (non interactive)
_BonesBoss = const(3) # Main monster of the Boss Bones swarm
_DragonBones = const(4) # Head monster of the Dragon Bones chain
_ChargingBones = const(5) # Charging player
_ChargingBonesFriend = const(6) # Charging other player
_Skittle = const(7) # Bug that just flies straight to the left at player
_Fireball = const(8) # Projectile that just flies straight to the left
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
_LeftDoor = const(30) # Door that manages countdown sequence for rocket.
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
LeftDoor = _LeftDoor
boss_types = [_BonesBoss, _DragonBones, _LeftDoor]

# Dialog from worms in reaction to monster events
reactions = []

# Additional hidden bahaviour state for all monsters,
# (do not use for draw behavior as it won't propagate to coop)
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
    _molaar_feet = bytearray([120,52,36,36,44,24])
    # BITMAP: width: 6, height: 8
    _molaar_feet_m = bytearray([60,126,255,255,126,60])
    # BITMAP: width: 4, height: 8, frames: 2 (up tail, down tail)
    _molaar_tail = bytearray([192,234,127,41,131,215,126,84])
    # BITMAP: width: 8, height: 8
    _block = bytearray([255,255,255,255,255,255,255,255]) # Mask (8x8 full)


    def __init__(self, tape):
        ### Engine for all the different monsters ###
        self._tp = tape
        # x pos for left edge of the active tape area of coop, otherwise own
        self._px = 0
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
        px = buf[0]<<24 | buf[1]<<16 | buf[2]<<8 | buf[3] # left of own tape
        # Loop through each monster
        tids = ptr8(self._tids)
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        for i in range(48):
            x = xs[i]
            # Add monster to buffer (disabling if out of range)
            buf[16+i*3] = tids[i] if 0 < x-px <= 256 else 0
            buf[17+i*3] = x-px if 0 < x-px <= 256 else 0
            buf[18+i*3] = ys[i]
        # Clear remainder of buffer
        for i in range(i+1, 48):
            buf[16+i*3] = 0 # Disable monster (not active)

    @micropython.viper
    def port_in(self, buf: ptr8):
        ### Unpack monster data from input buffer recieved from player 2 ###
        px = buf[0]<<24 | buf[1]<<16 | buf[2]<<8 | buf[3] # left of other tape
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
            d[ii+4] = 20 # Starting number of monsters in the swarm
        elif mon_type == _Bones:
            d[ii+4] = int(self._tp.x[0]) # Movement rate type
        elif mon_type == _BackBones:
            d[ii+4] = x//4 # Movement rate type
        elif mon_type == _Skittle:
            ys[i] = 64 + int(self._tp.player.y) # Target player 1
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
        elif mon_type == _LeftDoor:
            d[ii] = -1 # Countdown timer paused
            # Send self 500 pixels into distance
            ptr32(self.x)[i] += 500
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
        self._px = tpx-72 <<1|1 # left of own tape

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
            if _Bones <= typ <= _BackBones and t%2==0:
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
            ## LeftDoor (RocketShip manager)
            elif typ == _LeftDoor:
                self._tick_left_door(t, i)

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
            p2 = int(plyrs[1].coop) if int(len(plyrs)) > 1 else 0
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
        plyr = self._tp.player
        tids = ptr8(self._tids)
        xs, ys = ptr32(self.x), ptr8(self.y)
        ii = i*5
        s = t//16%2 # every other section moves, alternatively
        # Shoot Fireball projectiles
        if t%240==0:
            self.add(_Fireball, xs[i], ys[i]-64)
        # Move the head
        if int(plyr.x) > xs[i]: # Charge rapidly if worm sneaks past
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
        elif int(len(plyrs)) > 1 and plyrs[1].coop:
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
            d = data[ii] # direction of movement (down:0/left:1/up:2/right:3)
            r = data[ii+1] # rotation direction
            if ch(x, y): # Try to find an edge from within solid foreground
                xs[i] -= 1 if tid==_Pillar or t%30==0 else 0
                ys[i] += -1 if t%360<180 and y > 1 else 1 if y < 62 else 0
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
                elif d==3 and x > int(self._tp.x[0])+108:
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
                if (t+data[ii+2])%360<50:
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
        tpx = int(tape.x[0])
        if tr==0:
            # Set new swoop location
            data[ii], data[ii+1] = x, y
            data[ii+2] = t*x*y%100-50
            data[ii+3] = (t^(x*y))%50+5
            # Dont fly too far off to the right
            if data[ii+3] > tpx + 400:
                data[ii+3] = tpx + 400
        elif tr <= 50:
            # Exececute the swoop
            xs[i] = data[ii] + data[ii+2]*tr//50
            ys[i] = 64 + data[ii+1] + (data[ii+3]-data[ii+1])*tr//50
            # Add curve to swoop
            ys[i] += 20 - ((20-tr)*(20-tr)//20 if tr < 20
                else (tr-30)*(tr-30)//20 if tr >= 30 else 0)

    @micropython.viper
    def _tick_left_door(self, t: int, i: int):
        ### Hidden monster that manages the rocket launch sequence ###
        tape = self._tp
        rx = int(tape.x[0]) + 140
        mx = int(tape.midx[0]) + 140
        plyrs = tape.players
        tids = ptr8(self._tids)
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        data = ptr32(_data)
        ii = i*5
        x = xs[i]
        p1, p2 = plyrs[0], plyrs[1]
        p1x = int(p1.x)
        p2x = int(p2.x)
        timer = data[ii]
        alive = int(plyrs[0].mode) < 200

        # Start the countdown timer when both players close
        if timer < 0 and p1x > x-500 and p2x > x-500 and alive:
            data[ii] = 0
        # Update the countdown timer if player not respawning
        elif 100 <= timer < 1300 and (timer-100)%120 == 0 and alive:
            tape.clear_overlay()
            msg = "T-Minus " + str((1300-timer)//120)
            tape.message(0, msg + " \n \n \n \n \n " + msg, 3)
        else:
            self._left_door_events(timer, p1, p1x, p2, p2x, ii, x)

        # Increase the timer if active
        if timer >= 0:
            data[ii] += 1

        # Repair spaceship (until 12000)
        if timer < 9700:
            if timer < 1300:
                if rx > x-20:
                    ptrn = (pattern_door if rx<x else
                        pattern_room if rx<x+80 else pattern_fill)
                    tape.redraw_tape(2, rx, ptrn, pattern_fill)
                x1 = x-20-rx+mx
                if rx > x:
                    tape.redraw_tape(1, x1, pattern_fill, pattern_fill)
                if mx-20 > x1:
                    tape.redraw_tape(1, mx-20, pattern_fill, pattern_fill)
            else: # Spaceship repairs
                x1 = timer%20
                tape.redraw_tape(2, x-x1-1 if x1<10 else x+x1+70,
                    pattern_fill, None)
                if int(p1.mode) > 200:
                    tape.redraw_tape(2, x+timer%80, pattern_room, None)
            # Keep redrawing the rocket ship windows when in flight
            if timer >= 1600:
                tape.redraw_tape(1, timer, pattern_windows, pattern_fill)

        # Keep background monsters in range and falling
        if timer%(8-data[ii+1])==0:
            for xi in range(48):
                if tids[xi] != _BackBones:
                    continue
                if xs[xi] > x+88:
                    xs[xi] = x+88
                elif xs[xi] < x-8:
                    xs[xi] = x-8
                if ys[xi] > 104:
                    ys[xi] = 74
                ys[xi] += data[ii+2]
    
        # Flying sequence monster spawning
        if 2300 < timer < 10000 and timer%300==0:
            # Random position from edge of screen
            p = (timer^p1x)%448
            x1 = p if p<160 else 0 if p<224 else p-224 if p<384 else 159
            y1 = 0 if p<160 else p-160 if p<224 else 63 if p<384 else p-384
            if x1 <= 50: # No monsters from left of screen
                return
            mon = _Molaar if 50 < x1 < 140 else _ChargingBones
            self.add(mon, x+x1-40, y1+64)

        # Stop monsters hogging the respawn area or charging for too long
        xi = timer//2%48
        if tids[xi] == _ChargingBones:
            if xs[xi] == p1x or ys[xi] == int(p1.y):
                if int(p1.mode) > 200:
                    if xs[xi] == p1x:
                        xs[xi] += 30 if xi%2 else -30
                    else:
                        ys[xi] += 30 if xi//2%2 else -30
                tids[xi] = _Bones
                data[xi*5+4] = 2
        # Keep monsters in area
        if tids[xi] == _Bones:
            if xs[xi] > x+120:
                xs[xi] == x+120
            elif xs[xi] < x-20:
                xs[xi] == x-20

        # Ship breaking apart
        if 10600 < timer < 11300:
            if timer%5==0:
                play(rocket_bang, 40)
                tape.blast(timer//5,
                    (timer^p1x)%216+int(self.x[0])-72, (timer*p1x)%64)
            # Clearing out background monsters
            if tids[timer%48] != _LeftDoor:
                tids[timer%48] = 0
                self.num = int(self.num) - 1 <<1|1
        elif timer == 11300:
            tids[i] = 0
            self.num = int(self.num) - 1 <<1|1

    def _left_door_events(self, timer, p1, p1x, p2, p2x, ii, x):
        ### Key events during the rocket launch sequence ###
        tape = self._tp
        # Handle countdown finishing
        if timer == 1300:
            if p1x < x or (p2.coop and p2x < x):
                # One of the players failed failed to board
                name = p1.name if p1x < x else p2.name
                msg = name + " failed to board!"
                p1.die(msg, (x-600)*256)
                _data[ii] = -9
            else:
                # Players boarded!
                tape.feed = [pattern_none,pattern_fill,pattern_fill,
                    pattern_fill,pattern_fill]
                tape.spawner = (bytearray([]), bytearray([]))
                tape.clear_overlay()
                msg = "Ready to Launch!"
                tape.message(0, msg + " \n \n \n \n \n " + msg, 3)
                # Shut the rocket doors
                for xi in range(x-80, x):
                    tape.redraw_tape(2, xi, pattern_fill, pattern_fill)
                for xi in range(x+80, x+160):
                    tape.redraw_tape(2, xi, pattern_fill, pattern_fill)
                for xi in range(0, 216):
                    tape.redraw_tape(0, xi, pattern_none, None)
                # Set repawn point to be within rocket
                p1.respawn_loc = x + 40
        # Handle launch stage 1 (cam shaking)
        elif timer == 1400:
            tape.clear_overlay()
            tape.cam_shake = 3
        elif timer == 1450:
            reactions.extend(["^: WOAAAH!!", "@: HERE WE GOOOOOO!!",
                "@: Brace yourself, Glow!",
                "^: I'm stuck good to this beam.",
                "^: Brace yourself too, Umby!",
                "@: The G-Force is only increasing. I'm well planted!"])
            # Release background monsters
            for xi in range(20):
                self.add(_BackBones, x+xi*4, 10)
            _data[ii+2] = 1 # Start lifting off

        # Lift off acceleration sequence
        elif timer == 1800:
            _data[ii+2] = 1
        elif timer == 1900:
            _data[ii+1] = 1
        elif timer == 2000:
            _data[ii+1] = 2
        elif timer == 2100:
            _data[ii+1] = 3
        elif timer == 2200:
            _data[ii+1] = 4
        elif timer == 2300:
            _data[ii+1] = 5
            reactions.extend(["^: Monsters!", "@: They're getting in!",
                "^: Let's fight!"])
        elif timer == 2400:
            _data[ii+1] = 6
        elif timer == 2600:
            _data[ii+1] = 7
        elif timer == 2800:
            _data[ii+2] = 2
            tape.cam_shake = 2
        elif timer == 3000:
            _data[ii+2] = 3
            tape.cam_shake = 1
        elif timer == 3200:
            _data[ii+2] = 4
            tape.cam_shake = 0

        elif timer == 6000:
            reactions.extend(["@: This ship is taking a beating!",
                "^: It's not going to take much more!"])

        # Reach orbit
        elif timer == 8800:
            _data[ii+2] = 3
            reactions.extend(["@: Looks like we are easing into orbit",
                "^: Finally!"])
        elif timer == 9000:
            _data[ii+2] = 2
        elif timer == 9200:
            _data[ii+2] = 1
        elif timer == 9400:
            _data[ii+1] = 6
        elif timer == 9500:
            _data[ii+1] = 5
        elif timer == 9600:
            _data[ii+1] = 4
            p1.space = p2.space = 1
            reactions.extend(["^: Woah!", "@: Low Gravity!", "^: Cool!"])
        elif timer == 9700:
            _data[ii+1] = 3
        elif timer == 9800:
            _data[ii+1] = 2
        elif timer == 9900:
            _data[ii+1] = 1
        elif timer == 10000:
            _data[ii+2] = 0

        # Rocket explosions
        elif timer == 10200:
            tape.cam_shake = 1
            reactions.extend(["^: Umby?!", "@: Glow... WOW...",
                "^: I think this ship is coming apart!",
                "@: I think so too..."])
        elif timer == 10300:
            tape.cam_shake = 2
        elif timer == 10400:
            tape.cam_shake = 3
        elif timer == 10500:
            tape.cam_shake = 4
            reactions.extend(["^: What do we do?!", "@: I don't know!",
                "@: Hold on???", "^: I'm trying!"])
            tape.feed = [pattern_none,pattern_none,pattern_fill,
                pattern_none,pattern_fill]
        elif timer == 10600:
            tape.cam_shake = 5
        elif timer == 10700:
            tape.cam_shake = 7
            reactions.extend(["^: AAAAAGGGH!", "@: AAAAAGGGH!"])
        elif timer == 11300:
            tape.cam_shake = 0
            p1.respawn_loc = 0

    @micropython.viper
    def draw_and_check_death(self, t: int, p1, p2):
        ### Draw all the monsters checking for collisions ###
        tape = self._tp
        ch = tape.check
        tpx = int(tape.x[0])
        px = int(self._px) - tpx

        # Extract the states and positions of the rockets
        r1 = r2 = 0
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
            l = 1 if 36 <= x-px < 220 else 0    
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
        mx = px = -3
        my = py = -4
        mw = pw = 8

        # Bones class types
        if _Bones <= tid <= _ChargingBonesFriend:
            pf = 2 if not _Bones <= tid <= _BackBones else 0 if t//10 % 6 else 1
            img, msk = self._bones, self._bones_m
            pw = 7
            mx = -4
            mw = 9
            # Just draw main mask for BackBones
            if tid == _BackBones:
                tape.draw(0, x+px, y+py, img, pw, pf)
                return
            # Draw additional mask
            tape.mask(0, mx, my, msk, 9, 0) # Mask Back
        # Skittle type
        elif tid == _Skittle:
            img, msk = self._skittle, self._skittle_m
            px = 0
            mx = -1
            mw = 9
        # Fireball type
        elif tid == _Fireball:
            img, msk = self._fireball, self._fireball_m
            px = mx = 0
        # Stomper type
        elif tid == _Stomper:
            img, msk = self._stomper, self._stomper_m
            m = (y*16+t)%440
            my = py = (m if m < 50 else 50 if m < 170 else 220-m
                if m < 220 else 0)+3-y
            mw = pw = 7
        # Molaar type
        elif _Molaar <= tid <= _MolaarClimbingCharging:
            img, msk = self._molaar_feet, self._molaar_feet_m
            mw = pw = 6
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
            mw = pw = 7
        elif tid == _PillarTail:
            img, msk = self._pillar_tail, self._pillar_tail_m
            mw = pw = 7
        # Hoot type
        elif tid == _Hoot:
            img, msk = self._hoot, self._hoot_blink
            px = -4
            my = py = -5
            pw = 9
            mw = 7 if t%120<10 or 20<t%120<30 else 0
            # Draw open eyes
            tape.draw(0, x+mx, y+my, msk, 0 if mw else 7, 0)
        else:
            return

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
        elif tid == _LeftDoor:
            # LeftDoor can't die
            return

        # Wipe the monster, do the explosion, and leave a death message
        self._kill(t, mon, player, tag)

