
from engine_draw import front_fb
from engine import tick, disable_fps_limit
fb = front_fb()
from framebuf import FrameBuffer, MONO_VLSB, RGB565
while not tick():
    pass
disable_fps_limit()

def C(R,G,B):
    return ((R*31//255)<<11) + ((G*63//255)<<5) + (B*31//255)

_WIDTH = const(128)
_HEIGHT = const(64)
_BUFF_SIZE = const((_HEIGHT // 8) * _WIDTH)
_BUFF_INT_SIZE = const(_BUFF_SIZE // 4)

class Grayscale:
    def __init__(self):
        self._drawBuffer = bytearray(_BUFF_SIZE*2)
        self.buffer = memoryview(self._drawBuffer)[:_BUFF_SIZE]
        self.shading = memoryview(self._drawBuffer)[_BUFF_SIZE:]
        self.lastUpdateEnd = 0
        self._fb_bw = FrameBuffer(self.buffer, _WIDTH, _HEIGHT, MONO_VLSB)
        self._col = bytearray(_BUFF_SIZE)
        self._fb_col = FrameBuffer(self._col, _WIDTH, _HEIGHT, MONO_VLSB)
        self._pal = FrameBuffer(bytearray(4), 2, 1, RGB565)

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
        pal = self._pal
        pal.pixel(1, 0, C(255,255,255))
        fb.blit(self._fb_bw, 0, 32, -1, pal)

        self._light_grey()
        pal.pixel(1 , 0, C(150,150,150))
        fb.blit(self._fb_col, 0, 32, 0x0000, pal)

        self._dark_grey()
        pal.pixel(1 , 0, C(80,80,80))
        fb.blit(self._fb_col, 0, 32, 0x0000, pal)

        tick()

display = Grayscale()
display_buffer = display.buffer
display_update = display.update

