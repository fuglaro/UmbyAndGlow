
from engine_draw import front_fb
from engine import tick, fps_limit
from framebuf import FrameBuffer, MONO_VLSB, RGB565
while not tick():
    pass
fps_limit(60)
from engine_io import rumble

def C(R,G,B):
    return ((R*31//255)<<11) + ((G*63//255)<<5) + (B*31//255)
text = FrameBuffer(bytearray(4), 2, 1, RGB565)
text.pixel(1, 0, C(180,180,180))
white = FrameBuffer(bytearray(4), 2, 1, RGB565)
white.pixel(1, 0, C(255,255,255))
light = FrameBuffer(bytearray(4), 2, 1, RGB565)
light.pixel(1 , 0, C(150,150,150))
dark = FrameBuffer(bytearray(4), 2, 1, RGB565)
dark.pixel(1 , 0, C(80,80,80))


_WIDTH = const(128)
_HEIGHT = const(64)
_BUFF_SIZE = const((_HEIGHT // 8) * _WIDTH)
_BUFF_INT_SIZE = const(_BUFF_SIZE // 4)

shake = 0

class Grayscale:
    def __init__(self):
        self._drawBuffer = bytearray(_BUFF_SIZE*2)
        self.buffer = memoryview(self._drawBuffer)[:_BUFF_SIZE]
        self.shading = memoryview(self._drawBuffer)[_BUFF_SIZE:]
        self.lastUpdateEnd = 0
        self._fb_bw = FrameBuffer(self.buffer, _WIDTH, _HEIGHT, MONO_VLSB)
        self._col = bytearray(_BUFF_SIZE)
        self._fb_col = FrameBuffer(self._col, _WIDTH, _HEIGHT, MONO_VLSB)
        self.borders = bytearray(32//8*72)
        self._fb_borders = FrameBuffer(self.borders, 72, 32, MONO_VLSB)

    @micropython.viper
    def _light_grey(self):
        bw = ptr32(self.buffer)
        gs = ptr32(self.shading)
        out = ptr32(self._col)
        for i in range(_BUFF_INT_SIZE):
            out[i] = bw[i] & gs[i]

    @micropython.viper
    def _dark_grey(self):
        bw = ptr32(self.buffer)
        gs = ptr32(self.shading)
        out = ptr32(self._col)
        for i in range(_BUFF_INT_SIZE):
            out[i] = gs[i] & (-1-bw[i])

    @micropython.native
    def update(self):
        fb = front_fb()
        fb.fill(0)

        fb.blit(self._fb_borders, 0, -20, -1, text)
        fb.blit(self._fb_borders, 0, 108, -1, text)

        fb.blit(self._fb_bw, 0, 32+shake, -1, white)

        self._light_grey()
        fb.blit(self._fb_col, 0, 32+shake, 0x0000, light)

        self._dark_grey()
        fb.blit(self._fb_col, 0, 32+shake, 0x0000, dark)

        rumble(abs(shake)/6.0)
        while not tick():
            pass

display = Grayscale()
display_buffer = display.buffer
display_update = display.update
borders = display.borders

