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


## Game loading screen ##

from machine import Pin, SPI
from ssd1306 import SSD1306_SPI

def _load_title_screen():
    # Title graphics.
    # BITMAP: width: 72, height: 40
    title = bytearray([3,3,3,3,131,131,3,3,135,135,5,13,13,9,9,9,11,27,27,147,
        149,55,43,109,83,79,71,223,137,135,155,173,175,151,15,145,187,157,199,
        107,45,99,203,155,155,157,157,223,111,55,57,31,15,7,3,7,13,7,3,129,193,
        255,65,65,3,3,7,13,27,115,69,207,0,0,0,0,63,127,64,64,127,63,0,120,124,
        4,120,4,124,120,0,127,127,68,124,124,0,124,124,64,124,252,0,0,0,129,65,
        65,128,0,0,0,0,0,8,28,28,8,20,0,8,0,8,0,0,0,164,169,2,0,128,161,163,
        167,174,124,248,240,0,2,169,164,0,0,0,0,0,14,7,3,3,1,49,249,253,221,
        181,189,189,57,1,1,3,3,7,7,7,7,7,7,7,3,3,1,0,0,0,115,206,132,139,208,
        60,68,128,0,0,0,248,252,12,4,4,4,204,204,64,0,252,252,0,0,131,199,79,
        203,143,15,199,195,0,200,18,196,192,0,0,0,32,96,96,112,56,24,152,88,
        173,111,207,128,134,205,67,225,161,225,161,225,193,193,129,130,2,5,2,7,
        7,2,0,0,128,128,128,0,0,0,128,128,128,192,67,167,230,204,136,140,143,7,
        0,0,143,143,136,0,7,143,72,207,135,0,7,15,8,7,8,15,7,0,96,188,246,91,
        239,251,246,250,255,255,167,171,139,255,135,235,135,255,195,191,195,
        255,131,171,187,255,255,255,251,131,251,255,131,239,131,255,131,171,
        187,255,131,255,131,235,151,255,255,255,199,187,187,255,135,235,135,
        255,195,191,195,255,131,171,187,255,254,252,248,248,240,240,224,224])

    # Setup basic display access
    display = SSD1306_SPI(72, 40,
        SPI(0, sck=Pin(18), mosi=Pin(19)), dc=Pin(17), res=Pin(20), cs=Pin(16))
    if "rate" not in dir(display): # Load the emulator display if using the IDE API
        from thumby import display
        display.display.buffer[:] = title
        display.update()
    else: # Otherwise use the raw one if on the thumby device
        # Load the nice memory-light display drivers
        display.buffer[:] = title
        display.show()
_load_title_screen()

# Launch the game
# (loads while title screen is displayed - thanks to Doogle!)
from sys import path
path.append("/Games/Umby&Glow")
import game
