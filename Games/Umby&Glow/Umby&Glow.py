import time
import thumby

VIEW_W = 72 # width is in pixels
VIEW_H = 5 # height is in bytes (8 pixels)


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
def walls_pattern(x, y):
    return 0 if (x % 16) or (y % 2) else 1

##
# Drawable pattern - basic flat roof and floor
def room_pattern(x, y):
    return 1 if (y < 1) or (y >= VIEW_H*8 - 1) else 0

def fill(pattern, layer, offsetX, offsetY):
    for x in range(0, VIEW_W):
        for y in range(0, VIEW_H):
            for b in range(0, 8):
                layer[x*VIEW_H+y] |= pattern(x + offsetX, (y + offsetY)*8+b) << b




cave[5] = 5
cave[35] = 5
cave[107] = 5
cave[159] = 5
cave[35*5+4] = 3

fill(walls_pattern, memoryview(back), 0, 0)
fill(room_pattern, memoryview(land), 0, 0)


# Composite a view with new frame data, drawing to screen
display(memoryview(bytearray(
    back[b] | land[b]
    for b in range(0, VIEW_W*VIEW_H))))




