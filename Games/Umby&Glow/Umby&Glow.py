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

# TODO: Make Glows hook break lose if off top of screen (after 0-1 sec).
# TODO: Refactor explosions across Players and explode on monsters.
# TODO: Make testing mode draw be a cross-hair.
# TODO: Refactor Monsters to be type switchable single obkects (ready for coop comms)
# TODO: Finish working on help
# TODO: Make AI Umby
# TODO: Make AI Glow
# TODO: Make 2 player (remote monsters out of range go to background)
#          - Run all comms in a thread with thread locking on shared variables
#          - half frame rate for each two way comms.
# TODO: Make script/story outline
# TODO: Write script / story
# TODO: Add 8 more levels, extended game dynamics, and more monsters!
# TODO: Remove unused functions
# TODO: Full game description and overview (for arcade_description.txt file)
# TODO: Make demo video
# TODO: Submit to https://github.com/TinyCircuits/TinyCircuits-Thumby-Games

###
### # TODO turn story into script and delete.
###
#
#1 - player can switch characters (hold both buttons)
#2 - 2 players connect if devices have different characters
#
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
#Cave -> forest -> air -> rocket -> space -> spaceship ->
#    spaceship computer mainframe -> dolphin aquarium ->
#    flooded spaceship -> forrest -> cave
###




helper_text = [[ # Umby
    "Umby can jump high!",
    "Dont hit the roof too hard!"
    
    ], [ # Glow
    ""]]
# BITMAP: width: 7, height: 8
helper = bytearray([0,60,250,170,226,60,0])
helper_mask = bytearray([126,255,255,255,255,255,126])


##
# Script - the story through the dialog of the characters.
script = [
]


import gc
from time import ticks_ms
from sys import path
path.append("/Games/Umby&Glow")
from tape import Tape, display_update
from actors import Player, BonesTheMonster, bU, bD, bL, bR, bB, bA
from patterns import *


## Game Play ##

tape = Tape()

def set_level(start):
    ### Prepare everything for a level of gameplay including
    # the starting tape, and the feed patterns for each layer.
    # @param start: The starting x position of the tape.
    ###
    # Set the feed patterns for each layer.
    # (back, mid-back, mid-back-fill, foreground, foreground-fill)
    tape.feed[:] = [pattern_toplit_wall,
        pattern_stalagmites, pattern_stalagmites_fill,
        pattern_cave, pattern_cave_fill]
    # Reset monster spawner to the new level
    tape.types = [BonesTheMonster]
    tape.rates = bytearray([200])
    tape.reset(start)
    if start > -9999:
        # Fill the visible tape with the starting platform
        for i in range(start, start+72):
            tape.redraw_tape(2, i, pattern_room, pattern_fill)
        # Draw starting instructions
        tape.write(1, "THAT WAY!", start+19, 26)
        tape.write(1, "------>", start+37, 32)


def run_menu():
    ### Loads a starting menu and returns the selections.
    # @returns: a tuple of the following values:
    #     * Umby (0), Glow (1)
    #     * 1P (0), 2P (1)
    #     * New (0), Load (1)
    ###
    t = 0
    set_level(-9999)
    tape.add(BonesTheMonster, -9960, 25)
    m = tape.mons[0]
    ch = [0, 0, 1] # Umby/Glow, 1P/2P, New/Load
    h = s = 0
    while(bA()):
        # Update the menu text
        if h == 0 and (t == 0 or not (bU() and bD() and bL() and bR())):
            s = (s + (1 if not bD() else -1 if not bU() else 0)) % 3
            ch[s] = (ch[s] + (1 if not bR() else -1 if not bL() else 0)) % 2
            @micropython.native
            def sel(i):
                return (("  " if ch[i] else "<<")
                    + ("----" if i == s else "    ")
                    + (">>" if ch[i] else "  "))
            tape.clear_overlay()
            msg = "UMBY "+sel(0)+" GLOW "
            msg += "1P   "+sel(1)+"   2P "
            msg += "NEW  "+sel(2)+" LOAD"
            tape.message(0, msg)
            h = 1
        elif bU() and bD() and bL() and bR():
            h = 0
        # Make the camera follow the monster
        m.tick(t)
        m.draw(t)
        tape.auto_camera_parallax(m.x, m.y, 1, t)
        # Composite everything together to the render buffer
        tape.comp()
        # Flush to the display, waiting on the next frame interval
        display_update()
        t += 1
    tape.clear_overlay()
    return ch[0], ch[1], ch[2]

def load_save(sav, load):
    ### Load the progress from the file "sav" if "load" is True ###
    start = 3
    if load:
        try:
            f = open(sav, "r")
            start = int(f.read())
            f.close()
        except:
            pass
    return start

@micropython.native
def run_game():
    ### Initialise the game and run the game loop ###
    # Basic setup
    # Start menu
    glow, coop, load = run_menu()

    # Ready the level for playing
    sav = "/Games/Umby&Glow/" + ("glow" if glow else "umby") + ".sav"
    start = load_save(sav, load)
    t = 0;
    set_level(start)
    name = "Clip" if not (bR() or bA() or bB()) else "Glow" if glow else "Umby"
    p1 = Player(tape, name, start+10, 20)
    tape.players.append(p1)

    # Force memory cleanup before entering game loop
    gc.collect()

    # Main gameplay loop
    profiler = ticks_ms()
    while(1):
        # Speed amd memory profiling
        if (t % 60 == 0):
            print(ticks_ms() - profiler)
            print(gc.mem_alloc(), gc.mem_free())
            profiler = ticks_ms()
            # Save game every 30 seconds
            if (t % 1800):
                f = open(sav, "w")
                f.write(str(tape.x[0]))
                f.close()

        # Update the game engine by a tick
        p1.tick(t)
        for mon in tape.mons:
            mon.tick(t)

        # Make the camera follow the action
        tape.auto_camera_parallax(p1.x, p1.y, p1.dir, t)

        # Update the display buffer new frame data
        # Add all the monsters, and check for collisions along the way
        for mon in tape.mons:
            mon.draw(t)
            # Check if a rocket hits this monster
            if p1.rocket_on:
                if tape.check(p1.rocket_x-tape.x[0], p1.rocket_y+1, 224):
                    tape.mons.remove(mon)
                    p1.kill(t, mon)
        # If player is in play mode, check for monster collisions
        if (not p1.immune) and tape.check(p1.x-tape.x[0], p1.y, 224):
            p1.die(240, "Umby became monster food!")

        # Draw the players
        p1.draw(t)

        # Composite everything together to the render buffer
        tape.comp()
        # Flush to the display, waiting on the next frame interval
        display_update()

        t += 1
run_game()
