import time
import thumby
from array import array

VIEW_W = 72 # width is in pixels
VIEW_H = 5 # height is in bytes (8 pixels)
MID = int(VIEW_H * 8 / 2) - 1 # middle row of pixels






##
# Scrolling tape with each layer a section after the other.
# Layers each have 1 bit per pixel from top left, descending then wrapping to the right
# The vertical height is 64 pixels and comprises of 2 ints each with 32 bits. 
# Each layer is a layer in the composited render stack.
# Layers from left to right:
# - 0: far background
# - 144: close background
# - 288: close background fill (opaque off pixels)
# - 432: landscape including ground, platforms, and roof
# - 720: landscape fill (opaque off pixels)
tape = array('I', (0 for i in range(0, 72*2*5)))
# The scroll distance of each layer in the tape.
tapeScroll = array('i', [0, 0, 0, 0, 0])


frame = bytearray(VIEW_W*VIEW_H) # composited render buffer (in VLSB format)

@micropython.viper
def comp(frame: ptr8, tape: ptr32, tapeScroll: ptr32): # TODO del
    tp0 = tapeScroll[0]
    tp1 = tapeScroll[1]
    tp3 = tapeScroll[3]
    for x in range(0, 72):
        a = tape[(x+tp0)%72*2] | tape[(x+tp1)%72*2+144] | tape[(x+tp3)%72*2+432]
        b = tape[(x+tp0)%72*2+1] | tape[(x+tp1)%72*2+144] | tape[(x+tp3)%72*2+432]
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
# Drawable pattern - basic undulating stalactites and stalagmites
def saws_pattern(x, y):
    return 0#1 if (y < 8) or (y >= VIEW_H*8 - 8) else 0 TODO


# TODO fix naming of pattern functions
# TODO viper pattern functions

# PATTERN: test (slope plus walls)
@micropython.viper
def pattern_test(x: int, y: int) -> int:
    return int(x%120 == y*3) | (int(x%12 == 0) & int(y%3 == 0))

@micropython.viper
def extend_tape(pattern, tape: ptr32, tapeScroll: ptr32, layer: int):
    tapePos = tapeScroll[layer] + 1
    tapeScroll[layer] = tapePos
    x = tapePos + 72
    for w in range(0, 2):
        y = w*32
        v = 0
        for b in range(0, 32):
            v |= int(pattern(x, y)) << b
            y+=1
        tape[layer*144 + x%72*2+w] = v



for i in range(0, 72):
    extend_tape(wall_pattern, memoryview(tape), tapeScroll, 3)
    extend_tape(fence_pattern, memoryview(tape), tapeScroll, 1)
    extend_tape(pattern_test, memoryview(tape), tapeScroll, 0)






thumby.display.setFPS(240)



t = 0;
timer = time.ticks_ms()
while(1):

    if (t % 60 == 0):
        print(time.ticks_ms() - timer)
        timer = time.ticks_ms()


    # Composite a view with new frame data, drawing to screen
    comp(frame, tape, tapeScroll)
    thumby.display.blit(frame, 0, 0, 72, 40, -1, 0, 0) # TODO see why this is so slow.
    thumby.display.update()

    extend_tape(wall_pattern, memoryview(tape), tapeScroll, 3)
    if (t%2==0):
        extend_tape(fence_pattern, memoryview(tape), tapeScroll, 1)
        if (t%4==0):
            extend_tape(pattern_test, memoryview(tape), tapeScroll, 0)
    t += 1


