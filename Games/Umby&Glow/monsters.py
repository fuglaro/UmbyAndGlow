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

## Monster types ##

from math import sin, cos

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

