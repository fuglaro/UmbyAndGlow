_Lazer = const(9)
_EFalcon = const(31)

@micropython.viper
def _tick_e_falcon(self, t: int, i: int):
    ### E Falcon behavior: flying around on the right
    # shooting dual lazers
    ###
    xs = ptr32(self.x); ys = ptr8(self.y)
    x = xs[i]
    yy = ys[i]-60
    tpx = int(self._tp.x[0])
    ti = t+i*77
    # Shoot dual lazer projectiles
    if ti%300==10:
        self.add(_Lazer, x, ys[i]-68)
        self.add(_Lazer, x, ys[i]-60)
    if ti%300<30:
        return
    x += ti//120*77%32 - 16
    # Shift right into firing range
    if x < tpx+50+(i*6)%16 and ti%120>60 and ti%3==0:
        xs[i] += 1
    # Shift left into firing range
    elif x > tpx+56+(i*6)%16:
        xs[i] -= 1
    # Fly up or down and wrap around
    if ti%5==0:
        ys[i] = 60 + (yy + (1 if (x+ti%600//300)%2 else -1))%72

mons.ticks = {_EFalcon: _tick_e_falcon}