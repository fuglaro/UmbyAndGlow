_CPU = const(80)

@micropython.viper
def _tick_cpu(self, t: int, i: int):
    xs = ptr32(self.x)
    data = ptr32(self.data)
    ii = i*5
    dmg = data[ii]
    if data[ii+1] != dmg:
        tape = self._tp
        say = self.reactions.extend
        data[ii+1] = dmg
        if dmg%7==1:
            say(["|!! CORE ALERT !! INTEGRITY:"+str(16-dmg)])
        if dmg == 2:
            say(["@: Nice! It's taking damage!"])
        elif dmg == 5:
            say(["@: Keep going!"])
        elif dmg == 9:
            say(["^: This is an absolute blast!"])
        elif dmg == 13:
            tape.cam_shake = 1 <<1|1
        elif dmg == 14:
            say(["@: Just a bit more!"])
            tape.cam_shake = 3 <<1|1
        elif dmg == 15:
            tape.cam_shake = 0 <<1|1
        p1 = tape.players[0]
        pr1 = int(p1.rocket_x) + int(p1.rocket_y) + 1
        tape.blast(t+i,(t^pr1)%72+int(tape.x[0]), (t*pr1)%64)

mons.ticks = {_CPU: _tick_cpu}