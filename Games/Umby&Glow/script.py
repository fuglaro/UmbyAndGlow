# Copyright © 2022 John van Leeuwen <jvl@convex.cc>
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

## Script and Level Progression ##

from monsters import *
from patterns import *

def _script():
    with open("/Games/Umby&Glow/script.txt") as fp:
        ### Feeds out the script line by line ###
        for ln, line in enumerate(fp):
            if line and line[0] != "#" and line[0] != "\n":
                dist, _, ev_str = line.partition(",")
                try:
                    yield int(dist), eval(ev_str.strip())
                except SyntaxError:
                    print(ln+1, line)
                    raise

def get_chapters():
    ### Return the chapters and their starting positions ###
    pos = -300
    for dist, entry in _script():
        pos += dist
        if isinstance(entry, str) and entry.startswith("CHAPTER~"):
            yield (entry[8:], pos)

_line = _script()
_next_at, _next_event = next(_line)

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
    level = None
    pos, ev = _next_at, _next_event
    while pos <= start:
        if isinstance(ev, tuple):
            level = ev # Handle level type changes
        dist, ev = next(_line)
        pos += dist
    _next_at, _next_event = pos, ev
    if level:
        tape.feed[:] = level[0]
        tape.spawner = level[1]
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

@micropython.viper
def story_events(tape, mons, coop_px: int):
    ### Update story events including dialog and level type changes.
    # Update to the new px tape position: coop (furthest tape scroll of both players)
    ###
    global _dialog_c, _next_event, _next_at
    # Update current dialog queue, if needed.
    dc = int(_dialog_c)
    if dc > 0: # Decrement the next-line counter
        dc -= 1
        if dc == 0:
            tape.clear_overlay()
        _dialog_c = dc
    if _dialog_queue and dc == 0:
        # "Say" next line
        position, text = _dialog_queue.pop(0)
        tape.message(position, text, 3)
        # Dialog display time (in ticks)
        _dialog_c = 60 + int(len(text))*5//2

    # Check for, and potentially action, the next event
    pos = int(tape.x[0])
    pos = pos if pos > coop_px else coop_px # Furthest of both players
    if pos >= int(_next_at):
        event = _next_event
        # Handle level type changes
        if isinstance(event, tuple):
            tape.feed = event[0]
            tape.spawner = event[1]
        # Handle script dialog and naration
        elif isinstance(event, str):
            char = event[0]
            pos = 1 if char == '^' else 2 if char == '@' else 0
            # Handle worm dialog
            if pos:
                # Queue up the dialog in chunks of at most 2 lines each.
                # Split the text into lines that fit on screen.
                lines = [""]
                for word in event.split(' '):
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
                tape.message(0, event, 1)
        # Handle specific monster spawns like bosses.
        else:
            mons.add(event, pos+144, 32)
        dist, _next_event = next(_line)
        _next_at += dist

