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
    return 0 if (x % 16) or (y % 3) else 1

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
def fill(pattern, offsetX, offsetY, layer):
    for x in range(0, VIEW_W):
        for y in range(0, VIEW_H):
            v = 0
            for b in range(0, 8):
                v |= pattern(x + offsetX, (y + offsetY)*8+b) << b
            layer[x*VIEW_H+y] = v


##
# Drawable pattern - basic undulating stalactites and stalagmites
def saws_pattern(x, y):
    return 0#1 if (y < 8) or (y >= VIEW_H*8 - 8) else 0 TODO



fill(wall_pattern, 0, 0, memoryview(back))
fill(room_pattern, 0, 0, memoryview(land))
fill(fence_pattern, 0, 0, memoryview(cave))

land[5] = 5
land[35] = 5
land[107] = 5
land[159] = 5
land[35*5+4] = 3

thumby.display.setFPS(60)




t = 1;
while(1):
    
    backOffsetX += 1 if t % 4 == 0 else 0
    caveOffsetX += 1 if t % 2 == 0 else 0
    landOffsetX += 1
    

    #fill(wall_pattern, int(t/4), 0, memoryview(back))
    #fill(fence_pattern, int(t/2), 0, memoryview(cave))
    #fill(room_pattern, t, 0, memoryview(land))
    
    # Composite a view with new frame data, drawing to screen
    thumby.display.blit(memoryview(bytearray(
        back[(x+backOffsetX)%VIEW_W*VIEW_H+y]
        | cave[(x+caveOffsetX)%VIEW_W*VIEW_H+y]
        | land[(x+landOffsetX)%VIEW_W*VIEW_H+y]
        for y in range(0, VIEW_H) for x in range(0, VIEW_W)
        )), 0, 0, VIEW_W, VIEW_H*8, -1, 0, 0)
    thumby.display.update()


    t += 1


