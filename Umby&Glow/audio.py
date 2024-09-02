import engine_audio
from engine_resources import ToneSoundResource

tone = ToneSoundResource()
tone.frequency = 0

@micropython.native
def _speaker(freq):
    try:
        tone.frequency = freq
        engine_audio.play(tone, 0, False)
    except ValueError:
        pass # ignore out of bound frequencies
try:
    with open("/thumby.cfg", "r") as f:
        if "audioenabled,0" in f.read():
            _speaker = int # Disable audio
except OSError:
    pass

_signal = None
_duration = _t = 0
_no_interupt = False

def audio_tick():
    global _t
    if _t == _duration:
        return
    _signal(_t)
    _t += 1
    if _t == _duration:
        _speaker(0)

@micropython.native
def play(sound, duration, no_interupt=False):
    global _signal, _duration, _no_interupt, _t
    if _no_interupt and _t != _duration:
        return
    _signal = sound; _duration = duration; _no_interupt = no_interupt; _t = 0
    audio_tick()

@micropython.viper
def rocket_flight(t: int):
    _speaker(1800-t*8)

@micropython.viper
def rocket_bang(t: int):
    _speaker(900 + (t*-155)%1000 if t < 10 else (t*193)%1000)

@micropython.viper
def rocket_kill(t: int):
    _speaker(900+(t*193)%1000)

@micropython.viper
def worm_jump(t: int):
    _speaker(800 if t < 5 else 1500)

@micropython.viper
def grapple_launch(t: int):
    _speaker(1400-t)

@micropython.viper
def death(t: int):
    _speaker(1500 if t < 60 else 1200 if t < 120 else 800)



