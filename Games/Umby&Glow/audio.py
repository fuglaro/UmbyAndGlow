## Audio engine and sound effects ##

from machine import PWM, Pin

_speaker = PWM(Pin(28))
_OFF = const(0)
_ON = const(32767)
_audio = _speaker.duty_u16
try:
    with open("/thumby.cfg", "r") as f:
        if "audioenabled,0" in f.read():
            _audio = int # Disable audio
except OSError:
    pass
_audio(_OFF)
_signal = None
_duration = 0
_t = 0
_no_interupt = False

@micropython.native
def audio_tick():
    ### Update the audio frequency for the next tick ###
    global _t
    if _t == _duration:
        return
    _signal(_t)
    _t += 1
    if _t == _duration:
        _audio(_OFF)

@micropython.native
def play(sound, duration, no_interupt=False):
    ### Play a sound for the given duration,
    # calling audio_tick at the rate you want the sound to change.
    ###
    global _signal, _duration, _no_interupt, _t
    if _no_interupt and _t != _duration:
        return
    _signal, _duration, _no_interupt, _t = sound, duration, no_interupt, 0
    audio_tick()
    _audio(_ON)

## Sound effects ##

@micropython.viper
def rocket_flight(t: int):
    ### Sound signal for rocket flight.
    # Ideal duration is 180
    ###
    _speaker.freq(1800-t*8)

@micropython.viper
def rocket_bang(t: int):
    ### Sound signal for rocket explosion.
    # Ideal duration is 40
    ###
    _speaker.freq(900 + (t*-155)%1000 if t < 10 else (t*193)%1000)

@micropython.viper
def rocket_kill(t: int):
    ### Sound signal for rocket explosion and killing a monster.
    # Ideal duration is 30
    ###
    _speaker.freq(900+(t*193)%1000)

@micropython.viper
def worm_jump(t: int):
    ### Sound signal for Umby's jump.
    # Ideal duration is 15
    ###
    _speaker.freq(800 if t < 5 else 1500)

@micropython.viper
def grapple_launch(t: int):
    ### Sound signal for Glow launching their grapple hook.
    # Ideal duration is 15
    ###
    _speaker.freq(1400-t)

@micropython.viper
def death(t: int):
    ### Sound signal for either worm dying.
    # Ideal duration is 240
    ###
    _speaker.freq(1500 if t < 60 else 1200 if t < 120 else 800)


