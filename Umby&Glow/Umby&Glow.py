# Copyright © 2022 John van Leeuwen <jvl@convex.cc>
# Copyright © 2022 Auri <@Auri#8401(Discord)>
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

# See https://github.com/fuglaro/UmbyAndGlow for full source repository

import engine_main

from machine import freq
freq(133000000)

from sys import path
path.append("/Games/Umby&Glow")

from display import display
splash = bytearray(b'\x03\x03\x03\x03\x83\x83\x03\x03\x87\x87\x05\r\r\t\t\t\x0b\x1b\x1b\x93\x957+mSOG\xdf\x89\x87\x9b\xad\xaf\x97\x0f\x91\xbb\x9d\xc7k-c\xcb\x9b\x9b\x9d\x9d\xdfo79\x1f\x0f\x07\x03\x07\r\x07\x03\x81\xc1\xffAA\x03\x03\x07\r\x1bsE\xcf\x00\x00\x00\x00?\x7f@@\x7f?\x00x|\x04x\x04|x\x00\x7f\x7fD||\x00||@|\xfc\x00\x00\x00\x81AA\x80\x00\x00\x00\x00\x00\x08\x1c\x1c\x08\x14\x00\x08\x00\x08\x00\x00\x00\xa4\xa9\x02\x00\x80\xa1\xa3\xa7\xae|\xf8\xf0\x00\x02\xa9\xa4\x00\x00\x00\x00\x00\x0e\x07\x03\x03\x011\xf9\xfd\xdd\xb5\xbd\xbd9\x01\x01\x03\x03\x07\x07\x07\x07\x07\x07\x07\x03\x03\x01\x00\x00\x00s\xce\x84\x8b\xd0<D\x80\x00\x00\x00\xf8\xfc\x0c\x04\x04\x04\xcc\xcc@\x00\xfc\xfc\x00\x00\x83\xc7O\xcb\x8f\x0f\xc7\xc3\x00\xc8\x12\xc4\xc0\x00\x00\x00 ``p8\x18\x98X\xado\xcf\x80\x86\xcdC\xe1\xa1\xe1\xa1\xe1\xc1\xc1\x81\x82\x02\x05\x02\x07\x07\x02\x00\x00\x80\x80\x80\x00\x00\x00\x80\x80\x80\xc0C\xa7\xe6\xcc\x88\x8c\x8f\x07\x00\x00\x8f\x8f\x88\x00\x07\x8fH\xcf\x87\x00\x07\x0f\x08\x07\x08\x0f\x07\x00`\xbc\xf6[\xef\xfb\xf6\xfa\xff\xff\xa7\xab\x9b\xff\x87\xdb\x83\xff\x83\x9f\xe3\xff\x87\xab\xbb\xff\xff\xff\xfb\x83\xfb\xff\x83\xdf\x83\xff\x87\xab\xbb\xff\x83\xff\x83\xdb\xa7\xff\xff\xff\x87\xbb\xb3\xff\x87\xdb\x83\xff\x83\x9f\xe3\xff\x87\xab\xbb\xff\xfe\xfc\xf8\xf8\xf0\xf0\xe0\xe0')
display.buffer[156:156+72] = splash[0:72]
display.buffer[284:284+72] = splash[72:144]
display.buffer[412:412+72] = splash[144:216]
display.buffer[540:540+72] = splash[216:288]
display.buffer[668:668+72] = splash[288:360]
del splash
display.update()

import game
