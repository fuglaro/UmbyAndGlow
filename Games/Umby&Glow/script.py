## Script Loading and Level Progression ##

from monsters import *
import gc
from utils import *
from array import array
_buf = array('l', [0, 0, 0, 0, 0, 0, 0, 0])

w = None # World
_loaded = None
def _load_world(tape, mons, world, feed): # Load world
    global _loaded
    orig = [id(tape.feed[0]), id(tape.feed[1]), id(tape.feed[2])]
    if _loaded != world:
        global w
        tape.feed = None
        mons.ticks = None
        w = None
        gc.collect()
        with open(f"/Games/Umby&Glow/world{world}.py") as fp:
            exec(fp.read())
        gc.collect()
        try:
            with open(f"/Games/Umby&Glow/mons{world}.py") as fp:
                exec(fp.read())
            gc.collect()
        except OSError:
            pass
        _loaded = world
    tape.feed = eval(feed)
    # Reset any offscreen background changes
    if tape.feed[0] != orig[0]:
        start = tape.bx[0]
        for i in range(start+72, start+144):
            tape.redraw_tape(0, i, tape.feed[0], None)
    if tape.feed[1:2] != orig[1:2]:
        start = tape.midx[0]
        for i in range(start+72, start+144):
            tape.redraw_tape(1, i, tape.feed[1], tape.feed[2])

def _script():
    with open("/Games/Umby&Glow/script.txt") as fp:
        for line in fp:
            if line and line[0] != "#" and line[0] != "\n":
                dist, _, ev_str = line.partition(",")
                yield int(dist), ev_str.strip()

def get_chapters():
    pos = -145
    for dist, ev in _script():
        pos += dist
        if ev.startswith('"CHAPTER~') or ev.startswith('"~'):
            yield (eval(ev), pos)

_line = _script()
_next_at, _next_event = next(_line)
state = [_next_at] # Last event for save state

def _load_lvl(tape, mons, ev):
    _load_world(tape, mons, ev[0], ev[1])
    tape.spawner = ev[2]
    for plyr in tape.players:
        plyr.space = ev[3]

def story_jump(tape, mons, start, lobby):
    global _next_event, _next_at
    # Scan script finding the starting position
    if _next_at <= start:
        lvl = None
        for dist, _next_event in _line:
            state[0] = _next_at
            _next_at += dist
            if _next_event[0] == "(":
                lvl = _next_event
            if _next_at > start:
                break
        if lvl:
            _load_lvl(tape, mons, eval(lvl))

    # Reset the tape data to match the new details
    tape.reset(start)
    if lobby:
        # Fill the visible tape with the starting platform
        for i in range(start, start+72):
            tape.redraw_tape(2, i, pattern_room, pattern_fill)
        tape.write(1, "THAT WAY!", start//2+19, 26)
        tape.write(1, "------>", start//2+37, 32)

_dialog_queue = []
_dialog_c = 0 # Next line counter
_active_battle = -1

@micropython.native
def add_dialog(tape, dialog):
    char = dialog[0]
    pos = 1 if char == '^' else 2 if char == '@' else 0
    if pos: # Worm dialog
        # Split the text into lines that fit on screen.
        lines = [""]
        for word in dialog.split(' '):
            if (int(len(lines[-1])) + int(len(word)) + 1)*4 > 72:
                lines.append("")
            lines[-1] += (" " if lines[-1] else "") + word
        # Queue up each 2 lines of dialog
        while lines:
            line = lines.pop(0)
            if lines:
                line += " " + lines.pop(0)
            _dialog_queue.append((pos, line))
    else: # Narration
        tape.message(0, dialog, 1)

@micropython.native
def story_events(tape, mons, coop_px):
    global _dialog_c, _next_event, _next_at, _active_battle
    # Don't progress script if respawning
    if tape.player and tape.player.mode > 200:
        return

    # Update current dialog queue
    if _dialog_c > 0: # Decrement the next-line counter
        _dialog_c -= 1
        if _dialog_c == 0:
            tape.clear_overlay()
    if _dialog_queue and _dialog_c == 0:
        # "Say" next line
        position, text = _dialog_queue.pop(0)
        tape.message(position, text, 3)
        # Dialog display time (in ticks)
        _dialog_c = 60 + len(text)*5//2

    # Check for monster reaction dialog
    while mons.reactions:
        add_dialog(tape, mons.reactions.pop(0))

    # Check if we are in an active battle
    if _active_battle >= 0:
        if mons.is_alive(_active_battle):
            return
        _active_battle = -1

    # Check for, and potentially action, the next event
    pos = tape.x[0]
    pos = pos if pos > coop_px else coop_px # Furthest of both players
    if pos >= _next_at:
        state[0] = _next_at
        event = eval(_next_event)
        # Handle level type changes
        if isinstance(event, tuple):
            _load_lvl(tape, mons, event)
        # Handle script dialog and naration
        elif isinstance(event, str):
            add_dialog(tape, event)
        # Handle specific monster spawns like bosses.
        else:
            # Pause script until boss monsters are killed
            bat = mons.add(event, pos+144, 32)
            if event in boss_types:
                _active_battle = bat
        dist, _next_event = next(_line)
        _next_at += dist

