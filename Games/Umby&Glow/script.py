## Script Loading and Level Progression ##

from monsters import *
from patterns import *

def _script():
    ### Returns iterator that feeds out script events ###
    with open("/Games/Umby&Glow/script.txt") as fp:
        ### Feeds out the script line by line ###
        for line in fp:
            if line and line[0] != "#" and line[0] != "\n":
                dist, _, ev_str = line.partition(",")
                yield int(dist), ev_str.strip()

def get_chapters():
    ### Return the chapters and their starting positions ###
    pos = -145
    for dist, ev in _script():
        pos += dist
        if ev.startswith('"CHAPTER~'):
            yield (eval(ev)[8:], pos)

_line = _script()
_next_at, _next_event = next(_line)
state = [_next_at] # Last event for save state

def _load_lvl(tape, ev):
    ### Load level patterns, monsters and player dynamics ###
    tape.feed = ev[0]
    tape.spawner = ev[1]
    for plyr in tape.players:
        plyr.space = ev[2]

def story_jump(tape, start, lobby):
    ### Prepare everything for the level of gameplay
    # at the given position including the story position,
    # the feed patterns for each layer, and the monster spawner.
    # Note this can only jump forwards in the script.
    # @param tape: The tape to manipulate.
    # @param start: The starting x position of the tape.
    # @param lobby: Whether to draw the starting platform
    ###
    global _next_event, _next_at
    # Loop through the script finding the starting position, and setting
    # the level as needed.
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
            _load_lvl(tape, eval(lvl))

    # Reset the tape data to match the new details, and potentially
    # clear the starting area.
    tape.reset(start)
    if lobby:
        # Fill the visible tape with the starting platform
        for i in range(start, start+72):
            tape.redraw_tape(2, i, pattern_room, pattern_fill)
        # Draw starting instructions
        tape.write(1, "THAT WAY!", start//2+19, 26)
        tape.write(1, "------>", start//2+37, 32)

_dialog_queue = []
_dialog_c = 0 # Next line counter
_active_battle = -1

@micropython.native
def add_dialog(tape, dialog):
    ### Say dialog or narration ###
    char = dialog[0]
    pos = 1 if char == '^' else 2 if char == '@' else 0
    # Handle worm dialog
    if pos:
        # Queue up the dialog in chunks of at most 2 lines each.
        # Split the text into lines that fit on screen.
        lines = [""]
        for word in dialog.split(' '):
            if (int(len(lines[-1])) + int(len(word)) + 1)*4 > 72:
                lines.append("")
            lines[-1] += (" " if lines[-1] else "") + word
        # Queue up each 2 lines dialog
        while lines:
            line = lines.pop(0)
            if lines:
                line += " " + lines.pop(0)
            _dialog_queue.append((pos, line))
    # Handle naration
    else:
        tape.message(0, dialog, 1)

@micropython.native
def story_events(tape, mons, coop_px):
    ### Update story events including dialog and level type changes.
    # Update to the new px tape position: coop (furthest tape scroll of both players)
    ###
    global _dialog_c, _next_event, _next_at, _active_battle
    # Don't progress script if respawning
    if tape.player and tape.player.mode > 200:
        return

    # Update current dialog queue.
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
    while reactions:
        add_dialog(tape, reactions.pop(0))

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
            _load_lvl(tape, event)
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

