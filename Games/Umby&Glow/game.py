## Game Play including main loop ##

import gc
gc.threshold(8000) # Aggressive garbace collection while initialising.
gc.enable()
from os import mkdir
from time import ticks_ms
from audio import audio_tick
from comms import comms, inbuf, outbuf
from monsters import Monsters
from player import Player, bU, bD, bL, bR, bB, bA
from script import get_chapters, story_events, story_jump, state
from tape import Tape, display_update, EMULATED

_FPS = const(60)

tape = Tape()
mons = Monsters(tape)
tape.mons_clear = mons.clear
tape.mons_add = mons.add

def load_save(sav, load):
    ### Load the progress from the file "sav" if "load" is True ###
    start = 3
    if load:
        try:
            with open(sav, "r") as f:
                start = int(f.read()) - 145
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
    ch = [0, 0, 1, -1, 0] # Umby/Glow, 1P/2P, New/Load, Chapter, selection
    story_jump(tape, -999, False)
    story_events(tape, mons, -950) # Scroll in the menu's Bones monster
    chapters = list(get_chapters())

    def background_update():
        ### Update the menu's background landscape ###
        # Make the camera follow the monster
        mons.tick(t)
        mons.draw_and_check_death(t, None, None)
        tape.auto_camera(mons.x[0], mons.y[0]-64, 1, t)
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
        return ((" " if ch[i] else "<")
            + ("--" if i == ch[4] else "  ")
            + (">" if ch[i] else " "))
    def update_main_menu():
        ### Draw the main selection menu ###
        ch[4] = (ch[4] + (1 if not bD() else -1 if not bU() else 0)) % 3
        if not (bL() and bR()):
            ch[ch[4]] = 0 if not bL() else 1
        msg = "__UMBY "+sel(0)+" GLOW__ "
        msg += "____1P "+sel(1)+" 2P____ "
        msg += "___NEW "+sel(2)+" LOAD__"
        tape.clear_overlay()
        tape.message(0, msg, 3)

    def update_chapter_menu():
        ### Draw the (secret) character selection menu ###
        if bU() and bD():
            return
        # Find the next chapter
        ch[3] = (ch[3] + (-1 if not bU() else 1)) % len(chapters)
        # Display the selected chapter
        msg = "Chapter " + chapters[ch[3]][0]
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
                try:
                    mkdir("/Saves")
                except:
                    pass
                sav = "/Saves/Umby&Glow-"+("glow" if ch[0] else "umby")+".sav"
                if ch[3] == -1:
                    start = load_save(sav, ch[2])
                else: # Start at selected chapter
                    start = chapters[ch[3]][1]
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
    tape.message(0, "GET READY!!...", 3)
    background_update()
    tape.clear_overlay()
    return ch[0], ch[1], start, sav

@micropython.native
def run_game():
    ### Initialise the game and run the game loop ###
    # Basic setup
    # Start menu
    glow, coop, start, sav = run_menu()

    # Select character, or testing mode by holding Right+B+A (release R last)
    name = "Clip" if not (bU() or bA() or bB()) else "Glow" if glow else "Umby"
    p2name = "Umby" if glow else "Glow"
    prof = not bL() # Activate profiling by holding Right direction
    p1 = Player(tape, mons, name, start+10, 20)
    p2 = Player(tape, mons, p2name, start+10, 20, ai=not coop, coop=coop)
    tape.player = p1
    tape.players.append(p1)
    tape.players.append(p2)
    # Ready the level for playing
    t = 1;
    story_jump(tape, start, True)
    # Initialise coop send data
    p1.port_out(outbuf)

    # Memory clearing before relaxing gc and entering game loop
    gc.collect()
    gc.threshold(20000)

    # Main gameplay loop
    savst = coop_px = pstat = pstat2 = ptot = pfps1 = pfps2 = 0
    pw = pw2 = pfpst = ticks_ms()
    mons2 = Monsters(tape)
    ch = tape.check
    while(1):
        story_events(tape, mons, coop_px)
        # Update the game engine by a tick
        p1.tick(t)
        p2.tick(t)
        mons.tick(t)
        # Make the camera follow the action
        tape.auto_camera(p1.x, p1.y, p1.dir, t)

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

        # Save any script progress (script events function as save points)
        if (savst != state[0]):
            f = open(sav, "w")
            f.write(str(state[0]))
            f.close()
            savst = state[0]

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
            gc.collect() # Full garbage collect for good memory use reading.
            print(pstat, ptot*_FPS//t, gc.mem_alloc(), gc.mem_free(), pstat2,
                pfps1*1000//fpst, pfps2*1000//fpst, tape.x[0])
            pstat = pstat2 = pfps1 = pfps2 = 0
            pfpst = ticks_ms()
        pw = ticks_ms()

run_game()
