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
# of a mask pattern) come with an associated fill pattern. Fill patterns for
# the mask layers return black(0) or transparent(1) values. Transparency
# will show the white pixels of the associated layer and also other
# background layers.
# The two calls to each layer, and the calls to the mask layer are guaranteed
# to happen subsequently, and there is a _buf global variable to store
# persistent static variables across function calls for the same pattern and
# fill. This allows for optimisation of expensive operations for all pixels
# and transparency values of a column of pixels on the same tape layer.
# Pattens functions take two arguments:
# * x: tape position horizontally to calculate column of pixels
# * oY (yOrigin): top vertical position of the requested 32 bits (0 or 32).

from utils import *

from array import array

# Simple cache used across the writing of a single column of the tape.
# Since the tape patterns must be stateless across columns (for rewinding), this
# should not store data across columns.
_buf = array('i', [0, 0, 0, 0, 0, 0, 0, 0])

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
#
#@micropython.viper
#def pattern_quilted_diodes(x: int, oY: int) -> int:
#    ### PATTERN [quilted_diodes]: mix between electronics and fabric.
#    # Looks like it is ihe insides of a woven computer.
#    ###
#    snco = ptr32(sinco) # Note we (dangerously) use a bytearray as an int array
#
#    sf = 100 # size factor
#    xm = sf*12//10 # sector
#    x = x%xm-xm//2
#
#    v = 0
#    for ya in range(oY, oY+32):
#
#        y = ya*int(abs(x//100))
#
#        p1 = -1 if snco[(x^y)%99+1]<128 else 0
#        p2 = -1 if snco[(x*2^y*2)%99+1]<128 else 0
#        p3 = -1 if snco[(x*4^y*4)%99+1]<128 else 0
#        p4 = -1 if snco[(x*8^y*8)%99+1]<128 else 0
#        v |= (
#           0 if (p1^p2^p3^p4) else 1
#        ) << (ya-oY)
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
    return -128 if oY else 7

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

#@micropython.viper
#def pattern_alien_totem_plants(x: int, oY: int) -> int:
#    ### PATTERN [alien_totem_plants]:
#    # Tended garden of alien plants good for mid background
#    ###
#    buff = ptr32(_buf)
#    if oY == 0:
#        buff[0] = int(shash(x,128,40)) + int(shash(x,16,16)) + int(shash(x,4,4)) - 16
#    v = 0
#    for y in range(oY, oY+32):
#        y1 = y-20 if y>32 else 44-y
#        v |= (
#            int(y1 > (32423421^(x*x*(y1-buff[0])))%64) if y1 > buff[0] else 0
#         ) << (y-oY)
#    return v

#@micropython.viper
#def pattern_alien_totem_floor(x: int, oY: int) -> int:
#    ### PATTERN [alien_totem_floor]:
#    # Floor and roofing matching the style of alien_totem_plants.
#    ###
#    buff = ptr32(_buf)
#    if oY == 0:
#        buff[0] = int(shash(x,128,20)) + int(shash(x,16,8)) + int(shash(x,4,4)) + 40
#    v = 0
#    for y in range(oY, oY+32):
#        y1 = y if y>32 else 64-y
#        v |= (
#            int(y1 > (32423421^(x*x*(y1-buff[0])))%64) if y1 > buff[0] else 0
#         ) << (y-oY)
#    return v


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

# TESTING (see file: Umby&Glow.py to activate pattern testing)
pattern_testing_back = pattern_none
pattern_testing = pattern_none
pattern_testing_fill = pattern_fill


