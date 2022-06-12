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

## Second thread for AI compute and 2 player communications ##

import _thread
import gc
from time import sleep_ms, ticks_ms

_FPS = const(60)

import time
def _thread_loop():
    while True:
        time.sleep(100)


class SideThread:
    def __init__(self, prof, p2=None):
        self._p2 = p2
        self._prof = prof
        self._p2buf = p2.data()

    @micropython.native
    def p2data(self):
        ### @returns the data for player 2 ###
        return self._p2.data()

    def run(self):
        pass#_thread.start_new_thread(_thread_loop, ())

    def _thread_loop(self):
        print("RUNNING THREAD")
        t = 0
        prof = self._prof
        # Side thread loop
        pstat, ptot, pw = 0, 0, ticks_ms()
        while True:


            self._p2buf = self._p2.data()


            t += 1

            # Rate limit to the FPS
            tick = ticks_ms()
            timer = tick + 1000//_FPS
            if not prof:
                sleep_ms(timer - tick)
                continue
            # Or rate limit with profiling
            pstat += tick - pw
            sleep_ms(timer - tick)
            if t % _FPS == 0:
                ptot += pstat
                #print(" "*24, pstat, ptot*_FPS//t, gc.mem_alloc(), gc.mem_free())
                pstat = 0
            pw = ticks_ms()
