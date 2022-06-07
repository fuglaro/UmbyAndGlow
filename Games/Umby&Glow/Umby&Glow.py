import time
import thumby

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





backOffsetX = 0
caveOffsetX = 0
landOffsetX = 0




##
# Drawable pattern - dotted vertical lines repeating
def wall_pattern(x, y):
    #return 0 if (x % 16) or (y % 3) else 1
    return 1 if x/3%(VIEW_H*8) == y else 0

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
#
def fill(pattern, layer, offsetX=0, width=VIEW_W):
    for x in range(offsetX, offsetX+width):
        for y in range(0, VIEW_H):
            v = 0
            for b in range(0, 8):
                v |= pattern(x, y*8+b) << b
            layer[x%VIEW_W*VIEW_H+y] = v


##
# Drawable pattern - basic undulating stalactites and stalagmites
def saws_pattern(x, y):
    return 0#1 if (y < 8) or (y >= VIEW_H*8 - 8) else 0 TODO



fill(wall_pattern, memoryview(back))
fill(room_pattern, memoryview(land))
fill(fence_pattern, memoryview(cave))

land[5] = 5
land[35] = 5
land[107] = 5
land[159] = 5
land[35*5+4] = 3

thumby.display.setFPS(240)




t = 0;
timer = time.ticks_ms()
while(1):

    if (t % 60 == 0):
        print(time.ticks_ms() - timer)
        timer = time.ticks_ms()
    
    if (t % 4 == 0):
        backOffsetX += 1
        fill(wall_pattern, memoryview(back), backOffsetX+VIEW_W-1, 1)
    caveOffsetX += 1 if t % 2 == 0 else 0
    landOffsetX += 1
    


    # Composite a view with new frame data, drawing to screen
    thumby.display.blit(memoryview(bytearray(
    0  #  back[(x+backOffsetX)%VIEW_W*VIEW_H+y]
       # | cave[(x+caveOffsetX)%VIEW_W*VIEW_H+y]
    #    | land[(x+landOffsetX)%VIEW_W*VIEW_H+y]
        for y in range(0, VIEW_H) for x in range(0, VIEW_W)
        )), 0, 0, VIEW_W, VIEW_H*8, -1, 0, 0)
    thumby.display.update()


    t += 1


