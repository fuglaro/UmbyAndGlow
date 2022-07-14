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
#
# All pattern functions are called twice for each column of pixels
# on each tape layer (or mask layer). The first call returns the
# black(0) or white(1) pixel values for the top 32 pixels (as a 32 bit int),
# and the second call returns the bottom 32 pixels. Since each
# tape layer has a mask layer, some functions (which take advantage
# of a mask pattern) come with an associated fill pattern,
# for the mask layer with black(0) or transparent(1) values. Transparency
# will show the white pixels of the associated layer and other
# background layers.
# The two calls to each layer, and the calls to the mask layer are guaranteed
# to happen subsequently, and there is a _buf global variable to store
# persistent static variables across function calls for the same pattern and
# fill. This allows for optimisation of expensive operations for all pixels
# and transparency values of a column of pixels on the same tape layer.
# Pattens functions take two arguments:
# * x: tape position horizontally to calculate column of pixels
# * oY (yOrigin): top vertical position of the requested 32 bits (0 or 32).

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

################################################################
# Unused interesting patterns, and example patterns
#
#@micropython.viper
#def pattern_template(x: int, oY: int) -> int:
#    ### PATTERN [template]: Template for patterns. Not intended for use. ###
#    v = 0
#    for y in range(oY, oY+32):
#        v |= (
#            1 # pattern (1=lit pixel, for fill layer, 0=clear pixel)
#        ) << (y-oY)
#    return v
#
#@micropython.viper
#def pattern_fence(x: int, oY: int) -> int:
#    ### PATTERN [fence]: - basic dotted fences at roof and high floor ###
#    v = 0
#    for y in range(oY, oY+32):
#        v |= (
#            (1 if y<12 else 1 if y>32 else 0) & int(x%10 == 0) & int(y%2 == 0)
#        ) << (y-oY)
#    return v
#
#@micropython.viper
#def pattern_test(x: int, oY: int) -> int:
#    ### PATTERN [test]: long slope plus walls ###
#    v = 0
#    for y in range(oY, oY+32):
#        v |= (
#            int(x%120 == y*3) | (int(x%12 == 0) & int(y%2 == 0))
#        ) << (y-oY)
#    return v
#
#@micropython.viper
#def pattern_wall(x: int, oY: int) -> int:
#    ### PATTERN [wall]: dotted vertical lines repeating ###
#    v = 0
#    for y in range(oY, oY+32):
#        v |= (
#            int(x%16 == 0) & int(y%3 == 0)
#         ) << (y-oY)
#    return v
#
#@micropython.viper
#def pattern_catheral(x: int, oY: int) -> int:
#    ### PATTERN [cathedral]: Cathedral style repetative background wall ###
#    v = 0
#    for y in range(oY, oY+32):
#        v |= (
#            int(y > (32423421^(y-x*y)) % 64)
#        ) << (y-oY)
#    return v
#
#@micropython.viper
#def pattern_biomechanical_hall_wall(x: int, oY: int) -> int:
#    ### PATTERN [biomechanical_hall_wall]:
#    # Alien background wall with repetative feel
#    ###
#    buff = ptr32(_buf)
#    v = 0
#    if oY == 0:
#        buff[0] = int(shash(x,32,48))
#    v = 0
#    for y in range(oY, oY+32):
#        v |= (
#            int(y > (11313321^(x*(y+buff[0]))) % 64 + 5)
#        ) << (y-oY)
#
#    return v
#
#@micropython.viper
#def pattern_biomechanical_lab_wall(x: int, oY: int) -> int:
#    ### PATTERN [biomechanical_lab_wall]:
#    # Alien background wall with techy feel
#    ###
#    buff = ptr32(_buf)
#    v = 0
#    if oY == 0:
#        buff[0] = x-50+int(shash(x,100,120))
#        buff[1] = int(shash(x,32,48))
#    v = 0
#    for y in range(oY, oY+32):
#        v |= (
#            int(y > (11313321^(buff[0]*(y+buff[1]))) % 64 + 5)
#        ) << (y-oY)
#    return v
#
#@micropython.viper
#def pattern_alien_totem_plants(x: int, oY: int) -> int:
#    ### PATTERN [alien_totem_plants]:
#    # Tended garden of alien plants good for mid background
#    ###
#    buff = ptr32(_buf)
#    if oY == 0:
#        buff[0] = int(shash(x,128,40)) + int(shash(x,16,16)) + int(shash(x,4,4))
#    v = 0
#    for y in range(oY, oY+32):
#        v |= (
#            int(y > (32423421^(x*x*(y-buff[0])))%64) if y > buff[0] else 0
#         ) << (y-oY)
#    return v
#
#@micropython.viper
#def pattern_toothsaw(x: int, y: int) -> int:
#    ### PATTERN [toothsaw]: TODO use and update for word ###
#    return int(y > (113111^x+11) % 64 // 2 + 24)
#
#@micropython.viper
#def pattern_revtoothsaw(x: int, y: int) -> int:
#    ### PATTERN [revtoothsaw]: TODO use and update for word ###
#    return int(y > (11313321^x) % 64)
#
#@micropython.viper
#def pattern_diamondsaw(x: int, y: int) -> int:
#    ### PATTERN [diamondsaw]: TODO use and update for word ###
#    return int(y > (32423421^x) % 64)
#
#
#@micropython.viper
#def pattern_zebra_hills(x: int, oY: int) -> int:
#    ### PATTERN [zebra_hills]: Hills with internal zebra pattern ###
#    buff = ptr32(_buf)
#    if oY == 0:
#        buff[0] = int(shash(x,128,40)) + int(shash(x,16,16)) + int(shash(x,4,4))
#    v = 0
#    for y in range(oY, oY+32):
#        v |= (
#            (int(y > (32423421^(x*(y-buff[0])))%32) if y > buff[0] + 4
#                else 1 if y > buff[0] else 0)
#         ) << (y-oY)
#    return v
#
#@micropython.viper
#def pattern_fallen_tree(x: int, oY: int) -> int:
#    ### PATTERN [fallentree]: TODO use  ###
#    v = 0
#    for y in range(oY, oY+32):
#        v |= (
#            int(y > (32423421^(x+y)) % 64)
#        ) << (y-oY)
#    return v
#
#@micropython.viper
#def pattern_vine_hang(x: int, oY: int) -> int:
#    ### PATTERN [panels]: TODO use ###
#    u = int(shash(x,12,40)) + int(shash(x,5,8))
#    v = 0
#    for y in range(oY, oY+32):
#        v |= (
#            1 if   (y)%((u)%10+5) < u//8-y//16 else 0
#        ) << (y-oY)
#    return v
#
#@micropython.viper
#def pattern_panels(x: int, oY: int) -> int:
#    ### PATTERN [panels]: TODO use ###
#    v = 0
#    for y in range(oY, oY+32):
#        v |= (
#            1 if (x*y)%100 == 0 else 0
#        ) << (y-oY)
#    return v
#
################################################################

@micropython.viper
def pattern_none(x: int, oY: int) -> int:
    ### PATTERN [none]: empty ###
    return 0

@micropython.viper
def pattern_fill(x: int, oY: int) -> int:
    ### PATTERN [fill]: completely filled ###
    return -1 # 1 for all bits

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
        buff[2] = int(x % (buff[0]>>3) == 0)
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
            ((int(y < (buff[0]>>1)*3) | buff[2]) # ground fill
            # ceiling fill
            & (int(y > 10-buff[1]) | int(y > 5) | int(y == 5) | buff[1]%(y+1)))
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
        buff[0] = 50 - (t1*t1>>8) - (t2*t2>>2) - t3*t3*4
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
            1 if (p*p)%(y+1) == 0 else 0
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
        buff[0] = 10 + int(shash(x,32,24))+int(shash(x,24,8))+int(shash(x,7,2))
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(y > buff[0]) | int(y < buff[0]-10)
         ) << (y-oY)
    return v

@micropython.viper
def pattern_cloudy_snowy_mountains(x: int, oY: int) -> int:
    ### PATTERN [cloudy_snowy_mountains]:
    # Distant snowy mountains background with clouds
    ###
    # buff: [ripple-modifier, snow-capping, cloud-height, cloud-level]
    buff = ptr32(_buf)
    xa = x*8
    if oY == 0:
        u = int(shash(xa,32,16))
        buff[0] = int(shash(xa,128,40))+u+int(shash(xa,4,4))
        buff[1] = u>>1
        # cloud parameters
        e = (x+10)%64-10
        e = 10+e if e < 0 else 10-e if e<10 else 0
        buff[2] = (int(shash(x,16,32)) + int(shash(x,8,16))-20-e*e)//3+5
        buff[3] = int(ihash(x>>6))%40
    v = 0
    for y in range(oY, oY+32):
        cloud = int(buff[3] > y > buff[3]-buff[2])
        v |= (
            (int(y > (113111^(xa*(y-buff[0])))>>7%386)
                if y+8 > buff[0]+(16-buff[1])
                else 1 if y > buff[0] else 0 if y+3 > buff[0] else cloud)
         ) << (y-oY)
    return v

@micropython.viper
def pattern_cloudy_plains(x: int, oY: int) -> int:
    ### PATTERN [cloudy_plains]:
    # Puffy clouds with fairly-flat ground (foreground)
    ###
    # buff: [cloud-height, cloud-level, ground height]
    buff = ptr32(_buf)
    if oY == 0:
        e = (x+10)%64-10
        e = 10+e if e < 0 else 10-e if e<10 else 0
        u = int(shash(x,8,16))
        buff[0] = ((int(shash(x,16,8)) + u-20-e*e)>>1)+10
        buff[1] = int(ihash(x>>6))%12+1
        buff[2] = u>>1
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(buff[1] > y > buff[1]-buff[0]) | int(y>58-buff[2])
         ) << (y-oY)
    return v

@micropython.viper
def pattern_tree_wall(x: int, oY: int) -> int:
    ### PATTERN [panels]: TODO use ###
    xa = x*x*40//((x%40+20)+1)
    return ((
            int(0x00000FFF)<<((xa+oY)%64-16) |
            uint(0xFFF00000)>>(32-(xa)%32)
        ) if xa%12 > 4 # Tree middle
        else -1 if (xa-1)%12 > 2 # Tree edges
        else 0 # Tree gaps
    )

@micropython.viper
def pattern_ferns(x: int, oY: int) -> int:
    ### PATTERN [ferns]: Midbackground jungle-fern ground cover ###
    buff = ptr32(_buf)
    if oY == 0:
        buff[0] = int(shash(x,64,40))+int(shash(x,32,48))+int(shash(x,4,8))-10
    v = 0
    for y in range(oY, oY+32):
        v |= (
            (int(y > (32423421^(x*(y-buff[0])))%128) if y > buff[0] + 5 else 0)
         ) << (y-oY)
    return v
@micropython.viper
def pattern_ferns_fill(x: int, oY: int) -> int:
    ### PATTERN [ferns_fill]: Associated fill layer for ferns.
    # Just has thicker leaves
    ###
    buff = ptr32(_buf)
    v = 0
    for y in range(oY, oY+32):
        v |= (
            (int(y > (32423421^(x*(y-buff[0])))%64) if y > buff[0] + 5 else 1)
         ) << (y-oY)
    return v

@micropython.viper
def pattern_forest_ferns(x: int, oY: int) -> int:
    ### PATTERN [ferns]: Midbackground jungle-fern ground cover ###
    buff = ptr32(_buf)
    if oY < 32:
        buff[2] = int(shash(x,40,30))+int(shash(x,16,24))+10 # Fern pattern
    v = 0
    for y in range(oY, oY+32):
        v |= (
            (int(y > (32423421^(x*(y-buff[2])))%56) if y > buff[2] + 10 else 0)
         ) << (y-oY)
    return v
@micropython.viper
def pattern_forest_ferns_fill(x: int, oY: int) -> int:
    ### PATTERN [ferns_fill]: Associated fill layer for ferns.
    # Just has thicker leaves
    ###
    buff = ptr32(_buf)
    v = 0
    oY -= 15
    for y in range(oY, oY+32):
        v |= (
            (int(y > (32423421^(x*(y-buff[2])))%64) if y > buff[2] else 1)
         ) << (y-oY)
    return v

@micropython.viper
def pattern_tree_branches(x: int, oY: int) -> int:
    ### PATTERN [tree_branches]: Forest tree top branches (foreground closed ceiling) ###
    buff = ptr32(_buf)
    if oY == 0:
        buff[3] = int(shash(x,32,30)) + int(shash(x,5,6)) - 10
    br = buff[3]
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int((y%(br%20+5) < br-y//6-5 and y < 30) or y == 0)
        ) << (y-oY)
    return v
@micropython.viper
def pattern_tree_branches_fill(x: int, oY: int) -> int:
    ### PATTERN [tree_branches_fill]:
    # Associated fill pattern for forest tree tops
    ###
    buff = ptr32(_buf)
    br = buff[3]
    v = 0
    for y in range(oY, oY+32):
        v |= (
           int((y*y)%((y+br+x)%10) < 1) if y%(br%20+5) < br-y//6-8 and y < 30 else 1
        ) << (y-oY)
    return v | int(1431655765)<<(x%2)

@micropython.viper
def pattern_forest(x: int, oY: int) -> int:
    ### PATTERN [forest]: Forest foreground ###
    buff = ptr32(_buf)
    if oY == 0:
        buff[0] = x+int(shash(x,50,80)) # Tree width / gap variance
        buff[1] = x*x*40//((x%40+20)+1) # Tree patterner
    xb = buff[0]
    return ((-1 if (xb-3)%120 > 94 # Trees
        else 0) # Tree gaps
        | int(pattern_forest_ferns(x, oY)) # Gaps and Ferms
        | int(pattern_tree_branches(x, oY))) # Branches and vines
@micropython.viper
def pattern_forest_fill(x: int, oY: int) -> int:
    ### PATTERN [forest_fill]: Associated fill pattern for forest. ###
    buff = ptr32(_buf)
    xb = buff[0]
    xa = buff[1]
    return (((
            int(0x00000FFF)<<((xa+oY)%64-16) |
            uint(0xFFF00000)>>(32-(xa)%32) |
            int(1431655765)<<(x%2)
        ) if xb%120 > 100 # Tree middle
        else -1)
        & int(pattern_forest_ferns_fill(x, oY))
        & int(pattern_tree_branches_fill(x, oY)))

@micropython.viper
def pattern_mid_forest(x: int, oY: int) -> int:
    ### PATTERN [mid_forest]: Dense trees and high ground fern cover.
    # Intended for mid background layer.
    ###
    buff = ptr32(_buf)
    if oY == 0:
        buff[0] = x+int(shash(x,50,80)) # Tree width / gap variance
        buff[1] = x*x*40//((x%40+20)+1) # Tree patterner
    xb = buff[0]
    v = 0
    for y in range(oY, oY+32):
        v |= (
            int(32423421%((y+x-200)%5000+400)<300) # sunlight
         ) << (y-oY)
    return (-1 if (xb-3)%60 > 39 # Trees
        else v
        ) | int(pattern_forest_ferns(x, oY+10)) # Gaps and Ferms
@micropython.viper
def pattern_mid_forest_fill(x: int, oY: int) -> int:
    ### PATTERN [mid_forest_fill]: Associated fill pattern to mid_forest.
    # Cuts out trees and ferns and also gives trees shadows and
    # adds shadow fern patterns.
    ###
    buff = ptr32(_buf)
    xb = buff[0]
    xa = buff[1]
    return ((
            int(0x00000FFF)<<((xa+oY)%64-16) |
            uint(0xFFF00000)>>(32-(xa)%32) |
            int(1431655765)<<(x//2%2)
        ) if xb%60 > 45 # Tree middle
        else -1 if (xb-3)%60 > 39 # Tree edge
        else 0 if (xb-5)%60 > 35 # Tree shadow
        else -1) & int(pattern_forest_ferns_fill(x, oY+5))

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



# TESTING (see file: Umby&Glow.py to activate pattern testing)
pattern_testing_back = pattern_fill
pattern_testing = pattern_forest
pattern_testing_fill = pattern_forest_fill


