import numpy as np
import pyloopr.const as const
import pyloopr.controller as controller
import asyncio
import sounddevice as sd
import signal
from pyloopr.state import Loopr
from pyloopr.loop import Loop
from rich import print
from typing import Callable

def generate_trigger(loopr: Loopr) -> Callable[[int, int], bool]:
    sync = loopr.sync
    if sync == const.SYNC_BAR:
        return lambda old_idx, new_idx: new_idx < old_idx

class AudioEngine:
    def __init__(self, loopr: Loopr):
        self.loopr = loopr
        self.trigger = generate_trigger(self.loopr)

    async def run(self):
        event_loop = asyncio.get_running_loop()

        coroutines = set([
            self.record,
            self.playback,
            controller.handle_midi_control,
            self.sync
        ])

        tasks: set[asyncio.Task] = set([asyncio.create_task(coro(self.loopr)) for coro in coroutines])

        def handle_interrupt():
            print("[bold yellow]Keyboard interrupt received, cancelling coroutines[/bold yellow]")
            [task.cancel() for task in tasks]

        event_loop.add_signal_handler(signal.SIGINT, handle_interrupt)

        await asyncio.gather(*tasks)
        
        print("Coroutines finished")

    def get_trigger(self) -> Callable[[], bool]:
        # of course, when conforming to tempo, this will have to change
        if not self.loopr.sync_chain:
            return lambda : True

        sync_loop: Loop = self.loopr.loops[self.loopr.sync_chain[0]]
        start_idx = sync_loop.idx

        if self.loopr.sync == const.SYNC_BAR:
            return lambda : sync_loop.idx < start_idx

    # to do some kind of render using the master loop to check sync
    # what a mess
    # TO DO: if master loop stops, hand off control to another loop!
    # Bug: Restarting loops when all off
    # To implement tempo, we need a tempo loop hmm
    async def sync(self, loopr: Loopr):
        while True:
            if loopr.sync != const.SYNC_NONE:
                # If there are no master loop, immediately start recording
                if loopr.loops_recorded:
                    for loop in loopr.loops:
                        if loop.len:
                            # If at least one loop has data but there is no master loop
                            # we need to set the master loop before playing
                            if loop.status == const.LOOP_QUEUE_PLAY:
                                if loopr.loops_recorded == 1:
                                    print(f"sync setting master and playing {loop.id}")
                                    loop.status = const.LOOP_PLAY
                                    loopr.sync_chain.append(loop.id)
                                # Other loops will sync to this one
                                else:
                                    if not loop.pending:
                                        print(f"sync pending play {loop.id}")
                                        loop.pending = True
                                        loop.trigger = self.get_trigger()
                                    elif loop.trigger():
                                        print(f"Play triggered on {loop.id}")
                                        loopr.sync_chain.append(loop.id)
                                        loop.pending = False
                                        loop.status = const.LOOP_PLAY
                            # If there is no master loop, then this is the master loop and we
                            # stop immediately, otherwise send a sync request
                            elif loop.status == const.LOOP_QUEUE_STOP:
                                if loopr.loops_recorded == 1:
                                    print(f"sync setting master and stopping {loop.id}")
                                    loop.status = const.LOOP_STOP
                                else:
                                    if not loop.pending:
                                        print(f"sync pending stop {loop.id}")
                                        loop.pending = True
                                        loop.trigger = self.get_trigger()
                                    elif loop.trigger():
                                        print(f"Stop triggered on {loop.id}")
                                        loop.pending = False
                                        loop.status = const.LOOP_STOP
                                        loop.idx = 0
                                        # pass sync control to next loop
                                        if loopr.sync_chain[0] == loop.id:
                                            if len(loopr.sync_chain) > 1:
                                                print(f"Sync control will pass to loop {loopr.sync_chain[1]}")
                                        loopr.sync_chain = [lid for lid in loopr.sync_chain if lid != loop.id]
                            # If this is a fixed length loop this is an additional trigger
                            elif loop.status == const.LOOP_REC and loop.fixed_beats > 0:
                                if loop.len >= loopr.loops[loopr.sync_chain[0]].beat_len * loop.fixed_beats:
                                    print(f"Fixed recording switching to dub {loop.id}")
                                    print(f"Loop len {loop.len/loopr.loops[loopr.sync_chain[0]].len}x master len")
                                    loop.status = loop.fixed_beats_post_status

                        # There is master loop by this point (fingers crossed logic is good)
                        # We just have to sync up recording to that loop
                        elif loop.status == const.LOOP_QUEUE_REC:
                            if not loop.pending:
                                print(f"sync pending rec {loop.id}")
                                loop.pending = True
                                loop.trigger = self.get_trigger()
                            elif loop.trigger():
                                print(f"Rec Triggered on {loop.id}")
                                loop.pending = False
                                loop.status = const.LOOP_REC
                                loopr.loops_recorded += 1

                else:
                    for loop in loopr.loops:
                        if loop.status == const.LOOP_QUEUE_REC:
                            print(f"sync starting rec {loop.id}")
                            loop.status = const.LOOP_REC
                            loopr.loops_recorded += 1

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                print("[yellow]Sync[/yellow] received cancelled")
                break

    async def record(self, loopr: Loopr):
        def callback(indata, *args):
            mux = np.sum(indata, axis=1).reshape(-1,1)
            # copy live feed
            loopr.monitor_buffer[:const.BUFFER_REC] = mux
            # record loops
            for loop in loopr.loops:
                if (
                    loop.status == const.LOOP_REC or
                    (loop.status == const.LOOP_QUEUE_PLAY and loop.old_status == const.LOOP_REC) or
                    (loop.status == const.LOOP_QUEUE_STOP and loop.old_status == const.LOOP_REC)
                ):
                    blks = const.BUFFER_LOOP - loop.len if loop.len + const.BUFFER_REC > const.BUFFER_LOOP else const.BUFFER_REC
                    loop.buf[loop.len:loop.len+blks] = mux[:blks]
                    loop.len += blks
                    if loop.len >= const.BUFFER_LOOP:
                        loop.status = const.LOOP_PLAY
                elif loop.status == const.LOOP_DUB:
                    blks = loop.len - loop.idx if loop.idx + const.BUFFER_REC > loop.len else const.BUFFER_REC
                    remainder = const.BUFFER_REC - blks
                    loop.buf[loop.idx:loop.idx+blks] += mux[:blks]
                    if remainder:
                        loop.buf[:remainder] += mux[blks:]
                        

        stream = sd.InputStream(
            callback=callback,
            dtype=loopr.monitor_buffer.dtype,
            channels=4,
            samplerate=loopr.sample_rate,
            device=loopr.device,
            blocksize=const.BUFFER_REC
        )

        with stream:
            while True:
                try:
                    await asyncio.sleep(0)
                except asyncio.CancelledError:
                    print("[red]Record[/red] received cancelled")
                    break

    async def playback(self, loopr: Loopr):
        mux: np.ndarray = np.zeros((const.BUFFER_REC, 1), dtype="float32")

        def callback(outdata, *args):
            # live feed
            mux[:const.BUFFER_REC] = loopr.monitor_buffer
            # mix in loops
            for loop in loopr.loops:
                if (
                    loop.status == const.LOOP_PLAY or loop.status == const.LOOP_DUB or
                    (loop.status == const.LOOP_QUEUE_STOP and loop.old_status == const.LOOP_PLAY)
                ):
                    # need to impl sync
                    blks = const.BUFFER_REC if loop.len >= loop.idx + const.BUFFER_REC else loop.len - loop.idx
                    mux[:blks] += loop.buf[loop.idx:loop.idx+blks]
                    
                    loop.idx += blks
                    if loop.idx >= loop.len:
                        # stopping a loop will also set its index to 0
                        loop.idx = 0

            outdata[:const.BUFFER_REC] = mux[:const.BUFFER_REC]

        stream = sd.OutputStream(
            callback=callback,
            dtype=loopr.monitor_buffer.dtype,
            channels=1,
            samplerate=loopr.sample_rate,
            device=loopr.device,
            blocksize=const.BUFFER_REC
        )

        with stream:
            while True:
                try:
                    await asyncio.sleep(0)
                except asyncio.CancelledError:
                    print("[green]Playback[/green] received cancelled")
                    break