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


class Monsters:
    # BITMAP: width: 7, height: 8, frames: 3
    _bones = bytearray([28,54,147,110,147,54,28,28,190,159,110,159,190,28,28,
        242,139,222,139,242,28])
    # BITMAP: width: 9, height: 8
    _bones_m = bytearray([28,62,247,243,239,243,247,62,28])

    @micropython.native
    def __init__(self, tape):
        ### Engine for all the different monsters ###
        self._tp = tape
        self.mons = []


    @micropython.native
    def add(self, mon_type, x, y):
        ### Add a monster of the given type ###
        if len(self.mons) < 10: # Limit to maximum 10 monsters at once
            self.mons.append(array('I', [mon_type, x, y, 0, 0, 0, 0]))

    @micropython.native
    def clear(self):
        self.mons = []

    @micropython.viper
    def tick(self, t: int):
        ### Update Monster dynamics one game tick for all monsters ###
        tape = self._tp
        tpx = int(tape.x[0])
        ch = tape.check_tape
        plyrs = tape.players
        p1 = int(len(plyrs)) > 0
        if p1:
            p1x = int(plyrs[0].x)
            p1y = int(plyrs[0].y)
        p2 = int(len(plyrs)) > 1
        if p2:
            p2x = int(plyrs[1].x)
            p2y = int(plyrs[1].y)

        # Loop through all the monsters, updating ticks
        for mon in self.mons:
            monp = ptr32(mon)
            typ, x, y = monp[0], monp[1], monp[2]

            # Check for standard death conditions
            if x < tpx - 72: # Too far left, destroy monster
                self.mons.remove(mon)

            # Bones
            if typ == _Bones:
                if t%3:
                    continue
                t = t//2
                dx, dy = monp[3], monp[4]
                # Find the next position
                nx = x + (monp[5] if t%20>dx else 0)
                ny = y + (monp[6] if t%20>dy else 0)
                # Change direction if needed
                if (dx | dy == 0 or ny < -4 or ny > 68 or t%129==0
                    or ((ch(nx, ny) and t%13
                        and not (ch(x, y) or y < 0 or y >= 64)))):
                    monp[3], monp[4] = t%20, 20-(t%20)
                    monp[5] = -1 if t%2 else 1
                    monp[6] = -1 if t%4>1 else 1
                else: # Otherwise continue moving
                    monp[1], monp[2] = nx, ny
                # Check for charging conditions
                if p1 and (p1x-x)*(p1x-x) + (p1y-y)*(p1y-y) < 300:
                    monp[0] = 2 # Charge player
                if p2 and (p2x-x)*(p2x-x) + (p2y-y)*(p2y-y) < 300:
                    monp[0] = 3 # Charge friend

            # Charging Bones
            elif _ChargingBones <= typ <= _ChargingBonesFriend:
                if t%4==0: # Charge rate
                    p = tape.players[typ-2]
                    monp[1] += 1 if x < p1x else -1 if x > p1x else 0
                    monp[2] += 1 if y < p1y else -1 if y > p1y else 0

    @micropython.viper
    def draw_and_check_death(self, t: int, p1, p2):
        ### Draw all the monsters checking for collisions ###
        tape = self._tp
        ch = tape.check
        draw = tape.draw
        mask = tape.mask
        tpx = int(tape.x[0])
        mons = self.mons
        # Extract the states and positions of the rockets
        r1, r2 = 0, 0
        if p1:
            r1 = int(p1.rocket_on)
            r1x, r1y = int(p1.rocket_x)-tpx, int(p1.rocket_y)
        if p2:
            r2 = int(p2.rocket_on)
            r2x, r2y = int(p2.rocket_x)-tpx, int(p2.rocket_y)

        # Draw and check for monster death
        for mon in mons:
            ### Draw Monster to the draw buffers ###
            monp = ptr32(mon)
            typeid, x, y = monp[0], monp[1]-tpx, monp[2]

            # Bones class types
            if _Bones <= typeid <= _ChargingBonesFriend:
                # Select animation frame
                f = 2 if typeid != _Bones else 0 if t*16//_FPS % 16 else 1
                # Draw Bones' layers and masks
                draw(1, x-3, y-4, self._bones, 7, f) # Bones
                mask(1, x-4, y-4, self._bones_m, 9, 0) # Mask Fore
                mask(0, x-4, y-4, self._bones_m, 9, 0) # Mask Backd

            # Check if a rocket hits this monster
            if r1 and ch(r1x, r1y, 224):
                mons.remove(mon)
                p1.kill(t, mon)
            # Check if ai helper's rocket hits the monster
            elif r2 and ch(r2x, r2y, 224):
                mons.remove(mon)
                p2.kill(t, mon)

