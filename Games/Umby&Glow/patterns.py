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

## Patterns ##

# Patterns are a collection of mathematical, and logical functions
# that deterministically draw columns of the tape as it rolls in
# either direction. This enables the procedural creation of levels,
# but is really just a good way to get richness cheaply on this
# beautiful little piece of hardware.

from array import array

# Simple cache used across the writing of a single column of the tape.
# Since the tape patterns must be stateless across columns (for rewinding), this
# should not store data across columns.
_buf = array('i', [0, 0, 0, 0, 0, 0, 0, 0])

## Utility functions ##

@micropython.viper
def abs(v: int) -> int:
    ### Fast bitwise abs ###
    m = v >> 31
    return (v + m) ^ m

@micropython.viper
def ihash(x: uint) -> int:
    ### 32 bit deterministic semi-random hash fuction
    # Credit: Thomas Wang
    ###
    x = (x ^ 61) ^ (x >> 16)
    x += (x << 3)
    x ^= (x >> 4)
    x *= 0x27d4eb2d
    return int(x ^ (x >> 15))

@micropython.viper
def shash(x: int, step: int, size: int) -> int:
    ### (smooth) deterministic semi-random hash.
    # For x, this will get two random values, one for the nearest
    # interval of 'step' before x, and one for the nearest interval
    # of 'step' after x. The result will be the interpolation between
    # the two random values for where x is positioned along the step.
    # @param x: the position to retrieve the interpolated random value.
    # @param step: the interval between random samples.
    # @param size: the maximum magnitude of the random values.
    ###
    a = int(ihash(x//step)) % size
    b = int(ihash(x//step + 1)) % size
    return a + (b-a) * (x%step) // step


## Pattern Library ##


@micropython.viper
def pattern_template(x: int, oY: int) -> int:
    ### PATTERN [template]: Template for patterns. Not intended for use. ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            1 # pattern (1=lit pixel, for fill layer, 0=clear pixel)
        ) << (y-oY)
    return v

################################################################
# Interesting pattern example library
@micropython.viper
def pattern_toothsaw(x: int, y: int) -> int:
    ### PATTERN [toothsaw]: TODO use and update for word ###
    return int(y > (113111^x+11) % 64 // 2 + 24)
@micropython.viper
def pattern_revtoothsaw(x: int, y: int) -> int:
    ### PATTERN [revtoothsaw]: TODO use and update for word ###
    return int(y > (11313321^x) % 64)
@micropython.viper
def pattern_diamondsaw(x: int, y: int) -> int:
    ### PATTERN [diamondsaw]: TODO use and update for word ###
    return int(y > (32423421^x) % 64)
@micropython.viper
def pattern_fallentree(x: int, y: int) -> int:
    ### PATTERN [fallentree]: TODO use and update for word ###
    return int(y > (32423421^(x+y)) % 64)
@micropython.viper
def pattern_panelsv(x: int, oY: int) -> int:
    ### PATTERN [panels]: TODO use ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            1 if (x*y)%100 == 0 else 0
        ) << (y-oY)
    return v
################################################################

@micropython.viper
def pattern_none(x: int, oY: int) -> int:
    ### PATTERN [none]: empty ###
    return 0

@micropython.viper
def pattern_fill(x: int, oY: int) -> int:
    ### PATTERN [fill]: completely filled ###
    return int(0xFFFFFFFF) # 1 for all bits

@micropython.viper
def pattern_fence(x: int, oY: int) -> int:
    ### PATTERN [fence]: - basic dotted fences at roof and high floor ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            (1 if y<12 else 1 if y>32 else 0) & int(x%10 == 0) & int(y%2 == 0)
        ) << (y-oY)
    return v

@micropython.viper
def pattern_room(x: int, oY: int) -> int:
    ### PATTERN [room]:- basic flat roof and high floor ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            1 if y < 3 else 1 if y > 38 else 0
        ) << (y-oY)
    return v

@micropython.viper
def pattern_test(x: int, oY: int) -> int:
    ### PATTERN [test]: long slope plus walls ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(x%120 == y*3) | (int(x%12 == 0) & int(y%2 == 0))
        ) << (y-oY)
    return v

@micropython.viper
def pattern_wall(x: int, oY: int) -> int:
    ### PATTERN [wall]: dotted vertical lines repeating ###
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(x%16 == 0) & int(y%3 == 0)
         ) << (y-oY)
    return v

@micropython.viper
def pattern_cave(x: int, oY: int) -> int:
    ### PATTERN [cave]:
    # Cave system with ceiling and ground. Ceiling is never less
    # than 5 deep. Both have a random terrain and can intersect.
    ###
    # buff: [ground-height, ceiling-height, ground-fill-on]
    buff = ptr32(_buf)
    if oY == 0:
        buff[0] = int(shash(x,32,48)) + int(shash(x,16,24)) + int(shash(x,4,16))
        buff[1] = int(abs(int(shash(x,8,32)) - (buff[0] >> 2)))
        buff[2] = int(x % (buff[0]//8) == 0)
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(y > buff[0]) | int(y < buff[1]) | int(y <= 5)
         ) << (y-oY)
    return v
@micropython.viper
def pattern_cave_fill(x: int, oY: int) -> int:
    ### PATTERN [cave_fill]:
    # Fill pattern for the cave. The ceiling is semi-reflective
    # at the plane at depth 5. The ground has vertical lines.
    ###
    # buff: [ground-height, ceiling-height, ground-fill-on]
    buff = ptr32(_buf)
    v = 0
    for y in range(oY, oY+32):
        v |= (
            ((int(y < buff[0]//2*3) | buff[2]) # ground fill
            # ceiling fill
            & (int(y > 10-buff[1]) | int(y > 5) | int(y == 5) | buff[1]%y))
        ) << (y-oY)
    return v

@micropython.viper
def pattern_stalagmites(x: int, oY: int) -> int:
    ### PATTERN [stalagmites]:
    # Stalagmite columns coming from the ground and associated
    # stalactite columns hanging from the ceiling.
    # These undulate in height in clustered waves.
    ###
    # buff: [ceiling-height, fill-shading-offset]
    buff = ptr32(_buf)
    if oY == 0:
        t1 = (x%256)-128
        t2 = (x%18)-9
        t3 = (x%4)-2
        buff[0] = 50 - t1*t1//256 - t2*t2//4 - t3*t3*4
        buff[1] = 15*(x%4)
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(y < buff[0]) | int(y > 64 - buff[0])
        ) << (y-oY)
    return v
@micropython.viper
def pattern_stalagmites_fill(x: int, oY: int) -> int:
    ### PATTERN [stalagmites_fill]:
    # Associated shading pattern for the stalagmite layer.
    # Stalagmites are shaded in a symetric manner while
    # stalactites have shadows to the left. This is just for
    # visual richness.
    ###
    # buff: [ceiling-height, fill-shading-offset]
    buff = ptr32(_buf)
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(y+20 > buff[0]) & int(y-buff[1] < 64 - buff[0])
        ) << (y-oY)
    return v

@micropython.viper
def pattern_toplit_wall(x: int, oY: int) -> int:
    ### PATTERN [toplit_wall]: organic background with roof shine ###
    v = 0
    p = x-500
    for y in range(oY, oY+32):
        v |= (
            1 if (p*p)%y == 0 else 0
        ) << (y-oY)
    return v

@micropython.viper
def pattern_tunnel(x: int, oY: int) -> int:
    ### PATTERN [cave]:
    # Cave system with ceiling and ground. Ceiling is never less
    # than 5 deep. Both have a random terrain and can intersect.
    ###
    # buff: [ground-height]
    buff = ptr32(_buf)
    if oY == 0:
        buff[0] = 10 + int(shash(x,32,24)) + int(shash(x,16,8)) + int(shash(x,4,))
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(y > buff[0]) | int(y < buff[0]-10)
         ) << (y-oY)
    return v

def pattern_bang(blast_x, blast_y, blast_size, invert):
    ### PATTERN (DYNAMIC) [bang]: explosion blast with customisable
    # position and size. Intended to be used for scratch_tape.
    # Comes with it's own inbuilt fill patter for also blasting away
    # the fill layer.
    # @returns: a pattern (or fill) function.
    ###
    @micropython.viper
    def pattern(x: int, oY: int) -> int:
        s = int(blast_size)
        f = int(invert)
        _by = int(blast_y)
        tx = x-int(blast_x)
        v = 0
        for y in range(oY, oY+32):
            ty = y-_by
            a = 0 if tx*tx+ty*ty < s*s else 1
            v |= (
                a if f == 0 else (0 if a else 1)
            ) << (y-oY)
        return v
    return pattern

