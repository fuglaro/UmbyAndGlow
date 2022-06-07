import time
import thumby
from array import array

VIEW_W = 72 # width is in pixels
VIEW_H = 5 # height is in bytes (8 pixels)
MID = int(VIEW_H * 8 / 2) - 1 # middle row of pixels




##
# Layers - 1 bit per pixel from top left, descending then wrapping to the right
back = bytearray(VIEW_W*VIEW_H) # non-interaction background layer
cave = bytearray(VIEW_W*VIEW_H) # non-interaction middle ground layer
cavefill = bytearray(VIEW_W*VIEW_H) # non-interaction middle ground layer (cleared pixels)
land = bytearray(VIEW_W*VIEW_H) # ground, platforms and roof layer (players interact)
landfill = bytearray(VIEW_W*VIEW_H) # ground, platforms and roof layer (cleared pixels)
trap = bytearray(VIEW_W*VIEW_H) # npcs and traps that kill the players
umby = bytearray(VIEW_W*VIEW_H) # the player: umby
glow = bytearray(VIEW_W*VIEW_H) # the player: glow

##
#
tape = array('I', (0 for i in range(0, 72*2)))


frame = bytearray(VIEW_W*VIEW_H) # composited render buffer (in VLSB format)

@micropython.viper
def comp(frame: ptr8, tape: ptr32, tapePos: int): # TODO del
    for x in range(0, 72):
        a = tape[(x+tapePos)%72*2]
        b = tape[(x+tapePos)%72*2+1]
        frame[x] = a
        frame[72+x] = a >> 8
        frame[144+x] = a >> 16
        frame[216+x] = a >> 24
        frame[288+x] = b

        
        
        # TODO 5th row and beyond

 #   0  #  back[(x+backtapePos)%VIEW_W*VIEW_H+y]
       # | cave[(x+cavetapePos)%VIEW_W*VIEW_H+y]
    #    | land[(x+landtapePos)%VIEW_W*VIEW_H+y]
  #      for y in range(0, VIEW_H) for x in range(0, VIEW_W)
   #     )




##
# Drawable pattern - dotted vertical lines repeating
def wall_pattern(x, y):
    #return 0 if (x % 16) or (y % 3) else 1
    #return 1 if x/3%(VIEW_H*8) == y else 0
    return 1 if x/3%(VIEW_H*8) == y or not ((x % 16) or (y % 3)) else 0

##
# Drawable pattern - basic flat roof and floor
def room_pattern(x, y):
    return 1 if (abs(y-MID) > MID - 3) else 0

##
# Drawable pattern - basic dotted fences at roof and floor
def fence_pattern(x, y):
    return 1 if (abs(y-MID) > MID - 12) and not ((x % 4) or (y % 4)) else 0

##
#
#
# TODO del
def fill_bytes(pattern, layer, tapePos=0, width=VIEW_W):
    for x in range(tapePos, tapePos+width):
        for y in range(0, VIEW_H):
            v = 0
            for b in range(0, 8):
                v |= pattern(x, y*8+b) << b
            layer[x%VIEW_W*VIEW_H+y] = v

def fill(pattern, layer, tapePos=0, width=VIEW_W): # TODO optimise for single column fill
    for x in range(tapePos, tapePos+width):
        for y in range(0, 2):
            v = 0
            for b in range(0, 32):
                v |= pattern(x, y*32+b) << b
            layer[x%VIEW_W*2+y] = v

##
# Drawable pattern - basic undulating stalactites and stalagmites
def saws_pattern(x, y):
    return 0#1 if (y < 8) or (y >= VIEW_H*8 - 8) else 0 TODO



fill_bytes(wall_pattern, memoryview(back))
fill_bytes(room_pattern, memoryview(land))
fill_bytes(fence_pattern, memoryview(cave))

fill(wall_pattern, memoryview(tape))


land[5] = 5
land[35] = 5
land[107] = 5
land[159] = 5
land[35*5+4] = 3

thumby.display.setFPS(240)



def extend_tape(tape, tapePos): # TODO optimise for single column fill
    x = tapePos + 72
    for y in range(0, 2):
        v = 0
        for b in range(0, 32):
            v |= wall_pattern(x, y*32+b) << b
        tape[x%72*2+y] = v

tapePos = 0;
timer = time.ticks_ms()
while(1):

    if (tapePos % 60 == 0):
        print(time.ticks_ms() - timer)
        timer = time.ticks_ms()


    # Composite a view with new frame data, drawing to screen
    comp(frame, tape, tapePos)
    thumby.display.blit(frame, 0, 0, 72, 40, -1, 0, 0) # TODO see why this is so slow.
    thumby.display.update()

    extend_tape(memoryview(tape), tapePos) # TODO no memoryview needed with viper
    tapePos += 1


