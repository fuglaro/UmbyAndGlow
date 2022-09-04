from array import array
from audio import play, rocket_kill, rocket_bang
from utils import (pattern_none, pattern_fill, pattern_room)

_Bones = const(1)
_BackBones = const(2)
_BonesBoss = const(3)
_DragonBones = const(4)
_Wyvern = const(5)
_ChargingBones = const(6)
_ChargingBonesFriend = const(7)
_Skittle = const(10)
_Fireball = const(11)
_Lazer = const(12)
_Stomper = const(20)
_Molaar = const(21)
_MolaarHanging = const(22)
_MolaarClimbing = const(23)
_MolaarCharging = const(24)
_MolaarHangingCharging = const(25)
_MolaarClimbingCharging = const(26)
_Pillar = const(27)
_PillarTail = const(28)
_Hoot = const(29)
_LeftDoor = const(30)
_EFalcon = const(31)
_Prober = const(32)
_Probing = const(33)
_FallingBones = const(34)
_BackPillar = const(50)
_BackBatty = const(51)
_CPU = const(80)
_Lung = const(81)
_TankFloor = const(82)
_MegaBones = const(83)
_CamShake2 = const(90)
_CamShake3 = const(91)
_SuperShake = const(92)
Bones = _Bones
BonesBoss = _BonesBoss
DragonBones = _DragonBones
Wyvern = _Wyvern
ChargingBones = _ChargingBones
Skittle = _Skittle
Fireball = _Fireball
Stomper = _Stomper
Molaar = _Molaar
Pillar = _Pillar
Hoot = _Hoot
LeftDoor = _LeftDoor
EFalcon = _EFalcon
Prober = _Prober
BackPillar = _BackPillar
BackBatty = _BackBatty
CPU = _CPU
Lung = _Lung
TankFloor = _TankFloor
MegaBones = _MegaBones
CamShake2 = _CamShake2
CamShake3 = _CamShake3
SuperShake = _SuperShake
FallingBones = _FallingBones
boss_types = [_BonesBoss, _DragonBones, _LeftDoor, _CPU, _Lung, _TankFloor,
    _MegaBones]

_data = array('l', 0 for i in range(48*5))

class Monsters:
    # BITMAP: width: 7, height: 8, frames: 3
    _bones = bytearray([28,54,147,110,147,54,28,28,190,159,110,159,190,28,28,
        242,139,222,139,242,28])
    # BITMAP: width: 9, height: 8
    _bones_m = bytearray([28,62,247,243,239,243,247,62,28])
    # BITMAP: width: 8, height: 8
    _skittle = bytearray([56,84,56,124,56,124,56,16])
    # BITMAP: width: 9, height: 8
    _skittle_m = bytearray([56,124,254,124,254,124,254,124,56])
    # BITMAP: width: 8, height: 8
    _fireball = bytearray([56,124,124,124,56,56,16,16])
    # BITMAP: width: 8, height: 8
    _fireball_m = bytearray([124,198,186,186,186,186,186,186])
    # BITMAP: width: 8, height: 8
    _lazer = bytearray([16,16,16,16,16,16,16,16])
    # BITMAP: width: 8, height: 8
    _lazer_m = bytearray([56,124,124,124,124,56,56,56])
    # BITMAP: width: 3, height: 8
    _lazer_shd = bytearray([40,40,40])
    # BITMAP: width: 7, height: 8
    _stomper = bytearray([36,110,247,124,247,110,36])
    # BITMAP: width: 7, height: 8
    _stomper_m = bytearray([239,255,255,254,255,255,239])
    # BITMAP: width: 7, height: 8
    _pillar_head = bytearray([2,62,228,124,228,62,2])
    # BITMAP: width: 7, height: 8
    _pillar_head_m = bytearray([63,255,255,254,255,255,63])
    # BITMAP: width: 7, height: 8
    _pillar_tail = bytearray([66,189,66,90,66,189,66])
    # BITMAP: width: 7, height: 8
    _pillar_tail_m = bytearray([126,255,255,255,255,255,126])
    # BITMAP: width: 9, height: 8
    _hoot = bytearray([114,142,156,248,112,248,156,142,114])
    # BITMAP: width: 7, height: 8
    _hoot_blink = bytearray([112,96,0,0,0,96,112])
    # BITMAP: width: 8, height: 8, frames: 2
    _molaar_head = bytearray([44,70,100,78,107,73,38,30,
        102,195,230,134,203,137,230,126])
    # BITMAP: width: 6, height: 8
    _molaar_feet = bytearray([120,52,36,36,44,24])
    # BITMAP: width: 6, height: 8
    _molaar_feet_m = bytearray([60,126,255,255,126,60])
    # BITMAP: width: 4, height: 8, frames: 2
    _molaar_tail = bytearray([192,234,127,41,131,215,126,84])
    # BITMAP: width: 8, height: 8
    _block = bytearray([255,255,255,255,255,255,255,255]) # Mask (8x8 full)
    # BITMAP: width: 6, height: 8
    _e_falcon = bytearray([129,153,165,165,189,231])
    # BITMAP: width: 8, height: 8
    _e_falcon_m = bytearray([129,189,255,255,255,255,255,60])
    # BITMAP: width: 10, height: 8. frames: 2
    _e_falcon_shd = bytearray([24,24,0,24,0,24,52,36,40,16,24,24,0,24,0,24,44,
        36,20,8])
    # BITMAP: width: 7, height: 8, frames: 2
    _prober = bytearray([93,227,147,158,147,227,93,93,251,139,142,139,251,93])
    # BITMAP: width: 9, height: 8, frames: 2
    _tentacles = bytearray([110,75,225,189,133,31,211,70,124,232,47,161,253,
        197,23,223,130,254])
    # BITMAP: width: 9, height: 8, frames: 2
    _tentacles_up = bytearray([118, 210, 135, 189, 161, 248, 203, 98, 62, 23,
        244, 133, 191, 163, 232, 251, 65, 127])
    # BITMAP: width: 48, height: 8, frames: 3
    _cpu = bytearray([182,157,132,231,255,134,145,164,149,129,236,229,233,172,161,182,218,183,133,180,255,135,160,149,161,128,237,233,164,173,225,218,234,231,135,157,252,135,161,145,164,129,229,164,169,233,225,234])
    # BITMAP: width: 16, height: 8
    _cpu_shd = bytearray([254,133,181,133,253,135,187,181,181,155,237,173,173,173,161,254])
    # BITMAP: width: 16, height: 8
    _cpu_m = bytearray([254,255,255,255,255,255,255,255,255,255,255,255,255,255,255,254])

    def __init__(self, tape):
        self._tp = tape
        self.data = _data
        self.ticks = None # Extra loadable monster behavior
        # x pos for left edge of the active tape area of coop, otherwise own
        self._px = 0
        # Types of all the monsters
        self._tids = bytearray(0 for i in range(48))
        # x positions of all the monsters
        self.x = array('l', 0 for i in range(48))
        # y positions start at 64 pixels above top of screen
        self.y = bytearray(0 for i in range(48))
        # Number of monsters active (local monsters only)
        self.num = 0
        # Dialog from worms in reaction to monster events
        self.reactions = []

    @micropython.viper
    def port_out(self, buf: ptr8):
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
        return bool(self._tids[mon])

    @micropython.viper
    def add(self, mon_type: int, x: int, y: int) -> int:
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
        xs[i] = x; ys[i] = y+64
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
        elif mon_type == _Pillar or _DragonBones <= mon_type <= _Wyvern:
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
            elif _DragonBones <= mon_type <= _Wyvern:
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
        tids = ptr8(self._tids)
        for i in range(48):
            tids[i] = 0
        self.num = 0 <<1|1

    @micropython.viper
    def tick(self, t: int):
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
            # Handle each monster type #
            typ = tids[i]
            if _Bones <= typ <= _BackBones and t%2==0:
                self._tick_bones(t, i)
            elif typ == _BonesBoss:
                self._tick_bones_boss(t, i)
            elif _DragonBones <= typ <= _Wyvern:
                self._tick_dragon_bones(t, i)
            elif _ChargingBones <= typ <= _ChargingBonesFriend and t%4==1:
                self._tick_bones_charging(t, i)
            elif (_Skittle <= typ <= _Lazer) and t%2:
                xs[i] -= 1 # Just fly straight left
            elif _Molaar <= typ <= _Pillar and t%3==0:
                self._tick_crawler(t, i)
            elif typ == _Prober:
                self._tick_prober(t, i)
            ## Dynamically loaded behaviors
            elif self.ticks:
                tic = self.ticks.get(typ, None)
                if tic:
                    tic(self, t, i)

    @micropython.viper
    def _tick_bones(self, t: int, i: int):
        xs = ptr32(self.x); ys = ptr8(self.y)
        x = xs[i]; y = ys[i]-64
        tids = ptr8(self._tids)
        data = ptr32(_data)
        ii = i*5
        th = t//2
        thi = th-i%10
        dx = data[ii]; dy = data[ii+1]
        # Find the next position
        nx = x + (data[ii+2] if thi%20>dx else 0)
        ny = y + (data[ii+3] if thi%20>dy else 0)
        # Change direction if needed
        tape = self._tp
        ch = tape.check_tape
        if (dx | dy == 0 or ny < 0 or ny > 63 or thi%129==0
            or ((ch(nx, ny) and th%13 and not (ch(x, y))))):
            data[ii] = th%20; data[ii+1] = 20-(th%20)
            data[ii+2] = -1 if th%2 else 1
            data[ii+3] = -1 if th%4>1 else 1
        # Otherwise continue moving
        elif th%(data[ii+4]%5+1):
            xs[i] = nx; ys[i] = ny+64
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
        tids = ptr8(self._tids)
        xs = ptr32(self.x)
        ys = ptr8(self.y)
        typ = tids[i]
        x = xs[i]
        y = ys[i]-64
        data = ptr32(_data)
        ii = i*5
        xj = x; yj = y
        if t%2:
            ci = 0
            # Swarm minions around boss
            for j in range(48):
                if tids[j] != _Bones:
                    continue
                ci += 1
                dx = data[j*5+2]
                xj = xs[j]; yj = ys[j]-64
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
        plyr = self._tp.player
        tids = ptr8(self._tids)
        xs = ptr32(self.x); ys = ptr8(self.y)
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
            if tids[j] == _Pillar or _DragonBones <= tids[j] <= _Wyvern:
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
        x = xs[i]; y = ys[i]-64
        # Slowlyish charge the player position
        xs[i] += 1 if x < px else -1 if x > px else 0
        ys[i] += 1 if y < py else -1 if y > py else 0

    @micropython.viper
    def _tick_crawler(self, t: int, i: int):
        tids = ptr8(self._tids)
        tid = tids[i]
        xs = ptr32(self.x); ys = ptr8(self.y)
        x = xs[i]; y = ys[i]-64
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
                tpx = 0-npx; tpy = npy
                # Apply anti-clockwise/clockwise modifiers
                rd = 1 if r else -1
                if r:
                    tpx = 0-tpx; tpy = 0-tpy
                    spx = spx if npx else 0-spx
                    spy = spy if npy else 0-spy
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
            if tids[j] == _Pillar or _DragonBones <= tids[j] <= _Wyvern:
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
    def _tick_prober(self, t: int, i: int):
        tids = ptr8(self._tids)
        data = ptr32(_data)
        xs = ptr32(self.x); ys = ptr8(self.y)
        x = xs[i]; y = ys[i]-64
        plx = int(self._tp.player.x)
        ply = int(self._tp.player.y)
        ti = t//8+i*77
        # Move and wait for turn to attack
        dx = plx+20+ti%16
        dy = ply+ti%48-32
        # Move to attack if its our turn
        mi = i
        while mi >= 0 and (tids[mi] != _Prober or mi == i):
            if mi == 0:
                dx = plx+10
                dy = ply+(8 if ply<32 else -8)
            mi -= 1
        xs[i] += 0 if dx==x or t%(y-dy) else (-1 if dx<x else 1)
        ys[i] += 0 if dy==y or t%(x-dx) else (-1 if dy<y else 1)
        # Attack if its our turn
        if mi == -1:
            ii = i*5
            # Charge
            if dx == xs[i] and dy == ys[i]-64:
                data[ii] += 1
            else:
                data[ii] = 0
            # Fire
            if data[ii] == 90:
                tids[i] = _Probing

    @micropython.viper
    def draw_and_check_death(self, t: int, p1, p2):
        tape = self._tp
        ch = tape.check
        tpx = int(tape.x[0])
        px = int(self._px) - tpx
        # Extract the states and positions of the rockets
        r1 = r2 = 0
        if p1:
            r1 = int(p1.rocket_on)
            r1x = int(p1.rocket_x)-tpx
            r1y = int(p1.rocket_y)
        if p2:
            r2 = int(p2.rocket_on)
            r2x = int(p2.rocket_x)-tpx
            r2y = int(p2.rocket_y)
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
            if tids[i] < _Hoot:
                self._draw_monsters_a(t, i, tids[i], x, ys[i]-64, l)
            else:
                self._draw_monsters_b(t, i, tids[i], x, ys[i]-64, l)
            # Check if a rocket hits this monster
            if r1 and ch(r1x, r1y, 224):
                self._hit_monster(t, i, p1)
                r1 = 0 # Done with this rocket
            # Check if ai helper's rocket hits the monster
            elif r2 and ch(r2x, r2y, 224):
                self._hit_monster(t, i, p2)
                r2 = 0 # Done with this rocket

    @micropython.viper
    def _draw_monsters_a(self, t: int, i: int, tid: int, x: int, y: int, l: int):
        tape = self._tp
        pf = 0 # Animation frame number
        mx = px = -3
        my = py = -4
        mw = pw = 8
        if _Bones <= tid <= _ChargingBonesFriend:
            pf = 2 if not _Bones <= tid <= _BackBones else 0 if t//10 % 6 else 1
            img = self._bones; msk = self._bones_m
            pw = 7
            mx = -4
            mw = 9
            if tid == _BackBones:
                tape.draw(0, x+px, y+py, img, pw, pf)
                return
            elif tid == _Wyvern:
                img = self._prober
                pf = t//30%2
                tape.draw(0, x+px, y+py, img, 7, 1-pf)
            tape.mask(0, mx, my, msk, 9, 0) # Mask Back
        elif tid == _Skittle:
            img = self._skittle; msk = self._skittle_m
            px = 0
            mx = -1
            mw = 9
        elif tid == _Fireball:
            img = self._fireball; msk = self._fireball_m
            px = mx = 0
        elif tid == _Lazer:
            img = self._lazer; msk = self._lazer_m
            px = mx = 0
            tape.draw(0, x+1, y+py, self._lazer_shd, 3, 0)
        elif tid == _Stomper:
            img = self._stomper; msk = self._stomper_m
            m = (y*16+t)%440
            my = py = (m if m < 50 else 50 if m < 170 else 220-m
                if m < 220 else 0)+3-y
            mw = pw = 7
        elif _Molaar <= tid <= _MolaarClimbingCharging:
            img = self._molaar_feet; msk = self._molaar_feet_m
            mw = pw = 6
            hf = 0 if tid < _MolaarCharging else 1
            hpx = 0 if tid < _MolaarCharging else 2
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
        elif tid == _Pillar:
            img = self._pillar_head; msk = self._pillar_head_m
            mw = pw = 7
        elif tid == _PillarTail:
            img = self._pillar_tail; msk = self._pillar_tail_m
            mw = pw = 7
        else:
            return
        tape.draw(l, x+px, y+py, img, pw, pf)
        tape.mask(l, x+mx, y+my, msk, mw, 0)

    @micropython.viper
    def _draw_monsters_b(self, t: int, i: int, tid: int, x: int, y: int, l: int):
        tape = self._tp
        pf = 0 # Animation frame number
        mx = px = -3
        my = py = -4
        mw = pw = 8
        if tid == _Hoot:
            img = self._hoot; msk = self._hoot_blink
            px = -4
            my = py = -5
            pw = 9
            mw = 7 if t%120<10 or 20<t%120<30 else 0
            # Draw open eyes
            tape.draw(0, x+mx, y+my, msk, 0 if mw else 7, 0)
        elif tid == _EFalcon:
            img = self._e_falcon; msk = self._e_falcon_m
            mx = -4
            pw = 6
            tape.draw(0, x-1, y+py, self._e_falcon_shd, 10, t%16//8)
        elif _Prober <= tid <= _Probing:
            ti = t+i*77
            plx = int(self._tp.player.x)-int(tape.x[0])
            ply = int(self._tp.player.y)
            img = self._prober; msk = self._block
            x1 = x-plx; y1 = y-ply
            l = 0 if x1*x1+y1*y1 > 256 and tid == _Prober else l
            pf = 1 if l else ti%48//24
            pw = 7
            mx = -3
            mw = 9
            # Draw the tenticles
            up = 0 if ply > y else 8
            tape.draw(0 if tid == _Prober else 1,
                x-11+ti%90//45, y-up+ti%36//12-1,
                self._tentacles_up if up else self._tentacles, 9, ti%20//10)
            tape.mask(0, x-11, y-up, self._block, 8, 0)
        elif tid == _CPU:
            img = self._cpu; msk = self._cpu_m
            mw = pw = 16
            my = py = 40-y
            pf = t//40%3
            for xi in range(4):
                if xi==2: continue
                pxi = x+px+(-20 if xi==3 else -8)+16*xi
                for yi in range(8):
                    if xi!=3 and yi>2: continue
                    pyi = y+py+(16 if xi==3 else -3)-8*yi
                    tape.draw(l, pxi, pyi, img, pw, pf)
                    tape.mask(l, pxi, pyi, msk, mw, 0)
                    if xi!=3:
                        tape.draw(0, pxi, pyi, self._cpu_shd, pw, 0)
        else:
            return
        tape.draw(l, x+px, y+py, img, pw, pf)
        tape.mask(l, x+mx, y+my, msk, mw, 0)

    @micropython.viper
    def _kill(self, t: int, mon: int, player, tag):
        if mon != -1:
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
        ### Triggered when a player hits a monster ###
        tids = ptr8(self._tids)
        tid = tids[mon]
        tag = "_RIP_"
        alt = "_OUCH!_"
        # Monster specific damage behaviors
        if tid == _Pillar: # Direct hit!
            for j in range(mon-1, -1, -1):
                if tids[j] == _Pillar:
                    break # Another head, we are done on this chain
                elif tids[j] == _PillarTail: # Destroy entire chain
                    self._kill(t, j, player, "_RIP_")
        elif tid == _PillarTail or _DragonBones <= tid <= _Wyvern:
            tag = alt
            # Destroy last tail segment instead
            for j in range(mon-1, -1, -1):
                if tids[j] == _Pillar:
                    break # Another head, we are done on this chain
                elif tids[j] == _PillarTail:
                    mon = j
        elif tid == _LeftDoor:
            # LeftDoor can't die
            return
        elif tid == _CPU:
            data = ptr32(_data)
            ii = mon*5
            data[ii] += 1
            if data[ii] < 16:
                tag = alt
                mon = -1
        # Wipe the monster, do the explosion, and leave a death message
        self._kill(t, mon, player, tag)

