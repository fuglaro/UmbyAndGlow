import time
import thumby

VIEW_W = 72 # width is in pixels
VIEW_H = 5 # height is in bytes (8 pixels)


##
# Draw a layer with the same format as the view for the next frame.
# Blocks to next frame.
# Consider passing a memoryview for efficiency.
# @param key: -1 -> [1: on, 0: off], 1 -> [1: on, 0: ignored], 0 -> [1: ignored, 0: off] 
def display(layer, key):
    for x in range(0, VIEW_W):
        thumby.display.blit(memoryview(layer)[x*5:(x+1)*5], x, 0, 1, 40, -1, 0, 0)
    thumby.display.update()


##
# Print a layer.
# Similar to "display" but sends to stdout and doesn't block.
# Intended for debugging.
def print_display(layer): 
    for y in range(0, VIEW_H):
        for b in range(0, 8):
            for x in range(0, VIEW_W):
                print("#" if layer[x*VIEW_H+y] & (1<<b) else " ", end="")
            print("")


# Layers - 1 bit per pixel from top left, descending then wrapping to the right
view = bytearray(VIEW_W*VIEW_H) # final composited display layer
back = bytearray(VIEW_W*VIEW_H) # non-interaction background layer
cave = bytearray(VIEW_W*VIEW_H) # non-interaction middle ground layer
cavefill = bytearray(VIEW_W*VIEW_H) # non-interaction middle ground layer (cleared pixels)
land = bytearray(VIEW_W*VIEW_H) # ground, platforms and roof layer (players interact)
landfill = bytearray(VIEW_W*VIEW_H) # ground, platforms and roof layer (cleared pixels)
trap = bytearray(VIEW_W*VIEW_H) # npcs and traps that kill the players
umby = bytearray(VIEW_W*VIEW_H) # the player: umby
glow = bytearray(VIEW_W*VIEW_H) # the player: glow



view[5] = 5
view[35] = 5
view[107] = 5
view[159] = 5
view[35*5+4] = 3

print_display(memoryview(view))
display(memoryview(view), -1)




