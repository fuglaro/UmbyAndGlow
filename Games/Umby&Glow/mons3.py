_Hoot = const(29)

@micropython.viper
def _tick_hoot(self, t: int, i: int):
    if t%2:
        data = ptr32(self.data)
        ii = i*5
        t//=2
        xs = ptr32(self.x); ys = ptr8(self.y)
        x = xs[i]; y = ys[i]-64
        tr = (t+i*97)%200
        tpx = int(self._tp.x[0])
        if tr==0:
            # Set new swoop location
            data[ii] = x; data[ii+1] = y
            data[ii+2] = t*x*y%100-50
            data[ii+3] = (t^(x*y))%50+5
            # Dont fly too far off to the right
            if data[ii+3] > tpx + 400:
                data[ii+3] = tpx + 400
        elif tr <= 50:
            # Exececute the swoop
            xs[i] = data[ii] + data[ii+2]*tr//50
            ys[i] = 64 + data[ii+1] + (data[ii+3]-data[ii+1])*tr//50
            # Add curve to swoop
            ys[i] += 20 - ((20-tr)*(20-tr)//20 if tr < 20
                else (tr-30)*(tr-30)//20 if tr >= 30 else 0)

mons.ticks = {_Hoot: _tick_hoot}