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

# Speed up the CPU speed
from machine import freq
freq(125000000) # Safe to up to 133000000, if needed.

import gc
from time import ticks_ms
from comms import comms, inbuf, outbuf
from tape import Tape, display_update, Monsters, EMULATED
from player import Player, bU, bD, bL, bR, bB, bA
from audio import audio_tick
from script import script, story_events, story_reset

##
# AUDIO TESTING: (set the audio to play then quit)
#from audio import *
#from time import sleep_ms
#play(rocket_bang, 40, True)
#for i in range(250):
#    audio_tick()
#    sleep_ms(1000//60)
#raise Exception("STOP")
##

##
# COMMS TESTING: (test 2 player coop comms in WebIDE emulayer or with 1 device)
#@micropython.native
#def comms():
#    ### Fakes 2 play comms (relays p1 data, offset horizontally) ###
#    inbuf[:] = outbuf[:]
#    px = inbuf[0]<<24 | inbuf[1]<<16 | inbuf[2]<<8 | inbuf[3]
#    px += 10
#    inbuf[0] = px>>24
#    inbuf[1] = px>>16
#    inbuf[2] = px>>8
#    inbuf[3] = px
#    return 1

_FPS = const(60)

## Game Play ##

tape = Tape()

def load_save(sav, load):
    ### Load the progress from the file "sav" if "load" is True ###
    start = 3
    if load:
        try:
            f = open(sav, "r")
            # Subtract 300 from last save position to not skip boss battles
            start = int(f.read()) - 300
            f.close()
        except:
            pass
    return start if start > 3 else 3

def run_menu():
    ### Loads a starting menu and returns the selections.
    # @returns: a tuple of the following values:
    #     * Umby (0), Glow (1)
    #     * 1P (0), 2P (1)
    #     * Player start location
    ###
    handshake = held = t = 0
    ch = [0, 0, 1, 0, 0] # Umby/Glow, 1P/2P, New/Load, Chapter, selection
    story_reset(tape, -101, False)
    # Scroll in the menu's Bones monster
    tape.scroll_tape(0, 0, 1)
    story_events(tape, 0)

    def background_update():
        ### Update the menu's background landscape ###
        # Make the camera follow the monster
        mons = tape.mons
        mons.tick(t)
        mons.draw_and_check_death(t, None, None)
        tape.auto_camera_parallax(mons.x[0], mons.y[0]-64, 1, t)
        # Composite everything together to the render buffer
        tape.comp()
        # Flush to the display, waiting on the next frame interval
        display_update()
        if not EMULATED:
            # Composite everything together to the render buffer
            # for the half-frame to achieve twice the frame rate as
            # engine tick to help smooth dimming pixels
            tape.comp()
            display_update()
        tape.clear_stage()

    ## Main menu ##

    def sel(i):
        ### Menu arrows for a particular selection ###
        return (("  " if ch[i] else "<<")
            + ("----" if i == ch[4] else "    ")
            + (">>" if ch[i] else "  "))
    def update_main_menu():
        ### Draw the main selection menu ###
        ch[4] = (ch[4] + (1 if not bD() else -1 if not bU() else 0)) % 3
        if not (bL() and bR()):
            ch[ch[4]] = 0 if not bL() else 1
        msg = "UMBY "+sel(0)+" GLOW "
        msg += "1P   "+sel(1)+"   2P "
        msg += "NEW  "+sel(2)+" LOAD"
        tape.clear_overlay()
        tape.message(0, msg, 3)

    def update_chapter_menu():
        ### Draw the (secret) character selection menu ###
        if bU() and bD():
            return
        d = -1 if not bU() else 1
        # Find the next chapter
        while True:
            ch[3] = (ch[3] + d) % len(script)
            entry = script[ch[3]][1]
            if isinstance(entry, str) and entry.startswith("Chapter "):
                chapter = entry[8:].split(':')[0]
                break
        # Display the selected chapter
        msg = "Chapter " + chapter
        tape.clear_overlay()
        tape.message(0, msg, 3)

    menu = update_main_menu
    menu()
    while menu:
        # Update menu selection (U/D/L/R)
        if held == 0 and not (bU() and bD() and bL() and bR()):
            menu()
            held = 1
        elif bU() and bD() and bL() and bR() and bB() and bA():
            held = 0
        # Check for accepting for next stage (A)
        if not bA() and held != 2:
            # Secret chapter menu (DOWN+B+A)
            if not (bD() or bA() or bB()):
                menu = update_chapter_menu
                menu()
                held = 2
            else:
                # Find the starting position (of this player)
                sav = "/Games/Umby&Glow/"+("glow" if ch[0] else "umby")+".sav"
                if ch[3] == 0:
                    start = load_save(sav, ch[2])
                else: # Start at selected chapter
                    start = -1
                    for i in range(0, ch[3]+1):
                        start += script[i][0] - 1
                menu = None
        # Update background
        background_update()
        t += 1

    ## Negotiate 2 player communication and starting position (if needed)
    if ch[1]:
        tape.clear_overlay()
        # Waiting for other player...
        tape.message(0, "WAITING...", 3)
        while handshake < 240:
            # Get ready to send starting location information
            outbuf[0] = start>>24
            outbuf[1] = start>>16
            outbuf[2] = start>>8
            outbuf[3] = start
            # Communicate with other player on start position
            if comms():
                handshake += 60
                p2start = inbuf[0]<<24 | inbuf[1]<<16 | inbuf[2]<<8 | inbuf[3]
                if p2start > start:
                    start = p2start
            # Update background
            background_update()
            t += 1

    tape.clear_overlay()
    return ch[0], ch[1], start, sav

@micropython.native
def run_game():
    ### Initialise the game and run the game loop ###
    # Basic setup
    # Start menu
    glow, coop, start, sav = run_menu()

    # Ready the level for playing
    t = 1;
    story_reset(tape, start, True)
    # Select character, or testing mode by holding Right+B+A (release R last)
    name = "Clip" if not (bL() or bA() or bB()) else "Glow" if glow else "Umby"
    p2name = "Umby" if glow else "Glow"
    prof = not bL() # Activate profiling by holding Right direction
    p1 = Player(tape, name, start+10, 20)
    p2 = Player(tape, p2name, start+10, 20, ai=not coop, coop=coop)
    tape.players.append(p1)
    # Initialise coop send data
    p1.port_out(outbuf)

    # Force memory cleanup before entering game loop
    gc.collect()

    # Main gameplay loop
    pstat = pstat2 = ptot = pfps1 = pfps2 = 0
    pw = pw2 = pfpst = ticks_ms()
    mons = tape.mons
    mons2 = Monsters(tape)
    ch = tape.check
    coop_px = 0
    while(1):
        story_events(tape, coop_px)
        # Update the game engine by a tick
        p1.tick(t)
        p2.tick(t)
        mons.tick(t)
        # Make the camera follow the action
        tape.auto_camera_parallax(p1.x, p1.y, p1.dir, t)

        # Update coop networking
        if coop:
            if comms():
                # Update player 2 data (and also monsters)
                coop_px = p2.port_in(inbuf)
                mons2.port_in(inbuf)
                # Send player 1 data (and also monsters)
                p1.port_out(outbuf)
                mons.port_out(outbuf)

        # Half frame render
        if not EMULATED:
            # Composite everything together to the render buffer
            # for the half-frame to achieve twice the frame rate as
            # engine tick to help smooth dimming pixels
            if not prof:
                tape.comp()
                display_update()
            else:
                tape.comp()
                pw2 = ticks_ms()
                display_update()
                pstat2 += ticks_ms() - pw2
                pfps2 += 1

        # Drawing and collisions
        tape.clear_stage()
        # Draw all the monsters, and check for collisions along the way
        mons.draw_and_check_death(t, p1, p2)
        mons2.draw_and_check_death(t, None, None)

        # Check for death by monster
        if ch(p1.x-tape.x[0], p1.y, 224):
            p1.die("Umby became monster food!")
        # Draw the players
        p1.draw(t)
        p2.draw(t)

        # Composite everything together to the render buffer
        tape.comp()
        audio_tick()
        t += 1

        # Save game every 30 seconds
        if (t % 1800 == 0):
            f = open(sav, "w")
            f.write(str(tape.x[0]))
            f.close()

        # Flush to the display, waiting on the next frame interval
        if not prof:
            display_update()
            continue
        # Or flush display with speed and memory profiling
        pstat += ticks_ms() - pw
        pfps1 += 1
        display_update()
        if t % _FPS == 0:
            fpst = ticks_ms() - pfpst
            ptot += pstat
            print(pstat, ptot*_FPS//t, gc.mem_alloc(), gc.mem_free(), pstat2,
                pfps1*1000//fpst, pfps2*1000//fpst, tape.x[0])
            pstat = pstat2 = pfps1 = pfps2 = 0
            pfpst = ticks_ms()
        pw = ticks_ms()

run_game()
