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

_DIALOG_DISPLAY_FRAMES = const(180)

##
# Script - the story through the dialog of the characters.
# Script data includes the (additive) tape scroll amount for when
# each line of the script occurs and the dialog itself.
# Each entry is usually one line of dialog, but can also include naration
# or other messaging, or even level details. Each line of script
# includes a prefix indicating the character that says the line:
#     "@:" -> Umby says this (overlay at bottom of screen)
#     "^:" -> Glow says this (overlay at top of screen)
#     "" (no prefix) -> Narration (written to middle of background)
# The script can also include level changes which takes the form of a
# tuple with the following form:
#    (feed, spawner)
# E.g:
#    # Level: Cave filled with Bones
#    (
#     # (back, mid-back, mid-back-fill, foreground, foreground-fill)
#     [pattern_toplit_wall,
#      pattern_stalagmites, pattern_stalagmites_fill,
#      pattern_cave, pattern_cave_fill],
#     # Reset monster spawner to the new level
#     (bytearray([Bones]), bytearray([200])))
script = [
    # Cave with bones
    (-101, ([pattern_toplit_wall,
            pattern_stalagmites, pattern_stalagmites_fill,
            pattern_cave, pattern_cave_fill],
            (bytearray([Bones]), bytearray([200])))),
    (1, Bones),

    (220, "Chapter 1: The Cave"),

    (300, "@:Hi Glow!"),
    (0,   "^:Hi Umby!"),
    (0,   "@:These monsters are destroying our cave!"),
    (0,   "^:Where did they come from?"),
    (0,   "@:I dont know..."),
    (0,   "^:Do you think it was Lung?"),
    (0,   "@:Maybe..."),
    (0,   "@:But this isnt like his usual tricks."),

    (200, "Aim rockets: [UP/DOWN]"),

    (200, "---->"),
    (0,   "^:Hey Umby..."),
    (0,   "@:Yes, Glow?"),
    (0,   "^:They seem to be coming from outside."),
    (0,   "@:Indeed."),
    (0,   "@:Lets head to the entrance."),
    (60,  "---->"),
    (120,  "---->"),
    (120,  "---->"),

    (200, "Umbys platforms: B*2"),
    (200, "Glows tunnelling: [RIGHT/LEFT]+B [TAPPING:B]"),
    (200, "Shoot each other, not yourself!"),

    (600, "^:What are you thinking, Umby?"),
    (0,   "@:I think something is seriously wrong..."),
    (0,   "@:These monsters..."),
    (0,   "@:Ive never seen anything like them before."),
    (0,   "@:They seem really..."),
    (0,   "^:Alien?"),
    (0,   "@:Yes! They have, green blood!"),
    (0,   "^:Well, the cave entrance is just up ahead."),
    (60,  "---->"),

    (200, ([pattern_toplit_wall,
            pattern_stalagmites, pattern_stalagmites_fill,
            pattern_cave, pattern_cave_fill],
            (bytearray([]), bytearray([])))),

    (200, "^:Ummm... Umby?..."),
    (0,   "@:Yes Glow?..."),
    (0,   "^:Whats that rumbling?"),
    (0,   "@:Whatever it is, its big..."),
    (0,   "@:and its invaded the wrong cave!"),
    (0,   "^:Right. Lets rumble!"),

    (200, "Get ready!"),
    (0, BonesBoss),

    (600, "@:Nice work, Glow!"),
    (0,   "^:Back at ya, Umby!"),
    (0,   "@:I think we cleared the whole swarm."),
    (0,   "^:Is that all of them?"),
    (0,   "@:Lets head outside and find out..."),

    (80, ([pattern_toplit_wall,
            pattern_none, pattern_fill,
            pattern_tunnel, pattern_fill],
            (bytearray([]), bytearray([])))),

################################################################
# Story WIP and Ideas
#
###
### # TODO turn story into script
# TODO: Create bosses for all levels
###
#Umby and Glow save their cave.
#
#1.1) Umby, Glow in cave, with monsters and traps being about.
#1.2) Umby and Glow find monsters have infiltrated their cave.
#1.3) They suspect it is Lung.
#1.4) They decide to find out where they have come from.
#1.5) They leave their cave.
#
#Suspect bad worm
#Follow monsters to alien spaceship
#Find Lung held hostage
#Lung gives info as sacrifice (he will be flooded out - no time to save)
#Flood spaceship mainframe
#Go back home
#Cave -> forest -> plains -> space y -> rocket -> space -> spaceship ->
#    spaceship computer mainframe -> dolphin aquarium ->
#    flooded spaceship -> forrest -> cave
###
#
# Take your time, you don't want to be the early worm.
#
#"""
#The dolphins sold our planet? What for?!
#Mock tuna.
#Mock tuna?
#Yeah, synthesized tuna. They even thought they got the better deal. After the fish were wiped out, to the dolphins, the planet was just a big rock. From their point of view, they sold the aliens a rock for tuna.
#Gah! Tricky Blighters!
#
#Good thing we live near a SpaceY launch pad.
#We live near a SpaceY launch pad?
#Literally like every 3 weeks or so, the whole cave shakes itself half loose, and you always ask "Whats that?", and I always say "The downside of living near a SpaceY facility"
#Cool! Lets roll.
#
#
#Time to eat the frog!
#Eat the frog? - Do you mean: Try to do something impossible but by never giving up, eventually succeed?
#Yes. Eventually the worm eats all.
#"""
################################################################

    ## Credits ##
    (200, ([pattern_toplit_wall,
            pattern_none, pattern_fill,
            pattern_room, pattern_fill],
            (bytearray([]), bytearray([])))),
    (200, "Credits"),
    (160, "A convex.cc game by John VL"),
    (160, "For my Mum, who taught me how to tinker."),
    (160, "Hardware, Reference, and Dev Platform: ------------------"),
    (160, "TinyCircuits"),
    (160, "Special Thanks To: ------------------"),
    (160, "TinyCircuits"),
    (160, "TinyCircuits Thumby Discord Channel"),
    (160, "AyreGuitar"),
    (160, "-BBH-"),
    (160, "DarkGizmo"),
    (160, "Doogle"),
    (160, "Mason W."),
    (160, "Timendus"),
    (160, "Xyvir"),
    (160, "Game Development: ------------------"),
    (160, "John VL"),
    (160, "Graphics: ------------------"),
    (160, "John VL"),
    (160, "Lily VL"),
    (160, "Doogle"),
    (160, "Story and Writing: ------------------"),
    (160, "John VL"),
    (160, "DarkGizmo"),
    (160, "Play Testers: ------------------"),
    (160, "Andy N"),
    (160, "Doogle"),
    (160, "John VL"),
    (160, "Lily VL"),
    (160, "Mevlan S"),
    (160, "Paul K"),
    (160, "Vince B"),
    (160, "Thank you for playing!"),

    # TODO: encore level with randomisation of all previous content

    (4000000, "GOODBYE!")
]

_next_event = 0 # Index into the script for the next expected event
_next_at = script[0][0] # Position next event occurs

def story_reset(tape, start, lobby):
    ### Prepare everything for the level of gameplay
    # at the given position including the story position,
    # the feed patterns for each layer, and the monster spawner.
    # @param tape: The tape to manipulate.
    # @param start: The starting x position of the tape.
    # @param lobby: Whether to draw the starting platform
    ###
    global _next_event, _next_at
    # Loop through the script finding the starting position, and setting
    # the level as needed.
    ne = 0
    at = script[ne][0]
    while at <= start:
        event = script[ne][1]
        # Handle level type changes
        if isinstance(event, tuple):
            tape.feed[:] = event[0]
            tape.spawner = event[1]
        ne += 1
        at += script[ne][0]
    _next_event = ne
    _next_at = at
    # Reset the tape data to match the new details, and potentially
    # clear the starting area.
    tape.reset(start)
    if lobby:
        # Fill the visible tape with the starting platform
        for i in range(start, start+72):
            tape.redraw_tape(2, i, pattern_room, pattern_fill)
        # Draw starting instructions
        tape.write(1, "THAT WAY!", start+19, 26)
        tape.write(1, "------>", start+37, 32)

_dialog_queue = []
_dialog_c = 0 # Next line counter

@micropython.viper
def story_events(tape, coop_px: int):
    ### Update story events including dialog and level type changes ###
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
        _dialog_c = _DIALOG_DISPLAY_FRAMES

    # Check for, and potentially action, the next event
    pos = int(tape.x[0])
    pos = pos if pos > coop_px else coop_px # Furthest of both players
    if pos >= int(_next_at):
        event = script[_next_event][1]
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
            tape.mons.add(event, pos+144, 32)
        _next_event = int(_next_event) + 1
        _next_at = int(_next_at) + int(script[_next_event][0])

