import time
import thumby

VIEW_W = 72 # width is in pixels
VIEW_H = 5 # height is in bytes (8 pixels)
MID = int(VIEW_H * 8 / 2) - 1 # middle row of pixels


##
# Draw a layer with the same format as the view for the next frame.
# Blocks to next frame.
# Consider passing a memoryview for efficiency.
def display(layer):
    for x in range(0, VIEW_W):
        thumby.display.blit(memoryview(layer)[x*VIEW_H:(x+1)*VIEW_H], x, 0, 1, VIEW_H*8, -1, 0, 0)
    thumby.display.update()


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
    return 1 if (abs(y-MID) > MID - 12) and not ((x % 3) or (y % 3)) else 0

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

cave[5] = 5
cave[35] = 5
cave[107] = 5
cave[159] = 5
cave[35*5+4] = 3


t = 1;
while(1):

    #fill(wall_pattern, t/4, 0, memoryview(back))
    fill(room_pattern, t/2, 0, memoryview(land))
    fill(fence_pattern, t, 0, memoryview(cave))

    # Composite a view with new frame data, drawing to screen
    display(memoryview(bytearray(
        back[b] | cave[b] | land[b]
        for b in range(0, VIEW_W*VIEW_H))))

    t += 1


