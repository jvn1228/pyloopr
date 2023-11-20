import mido
import asyncio
import pyloopr.const as const
import numpy as np
from pyloopr.state import Loopr
from rich import print

class Controller:
    def __init__(self, loopr: Loopr):
        self.loopr = loopr

    def handle(self, msgs: list[int]):
        if msgs[0] in (const.CTRL_LOOP1, const.CTRL_LOOP2, const.CTRL_LOOP3, const.CTRL_LOOP4):
            assert len(msgs) > 1
            loop = self.loopr.loops[msgs[0]]
            
            if msgs[1] == const.CTRL_STATUS:
                if loop.status == const.LOOP_STOP:
                    if loop.len == 0:
                        print(f"Setting loop {msgs[0]} to REC")
                        if self.loopr.sync != const.SYNC_NONE:
                            loop.status = const.LOOP_QUEUE_REC
                        else:
                            loop.status = const.LOOP_REC
                    else:
                        print(f"Setting loop {msgs[0]} to PLAY")
                        if self.loopr.sync != const.SYNC_NONE:
                            loop.status = const.LOOP_QUEUE_PLAY
                        else:
                            loop.status = const.LOOP_PLAY
                elif loop.status == const.LOOP_REC:
                    print(f"Setting loop {msgs[0]} to PLAY")
                    if self.loopr.sync != const.SYNC_NONE:
                        loop.status = const.LOOP_QUEUE_PLAY
                    else:
                        loop.status = const.LOOP_PLAY
                elif loop.status == const.LOOP_PLAY:
                    print(f"Setting loop {msgs[0]} to DUB")
                    loop.status = const.LOOP_DUB
                elif loop.status == const.LOOP_DUB:
                    print(f"Setting loop {msgs[0]} to PLAY")
                    loop.status = const.LOOP_PLAY
            elif msgs[1] == const.CTRL_STOP:
                print(f"Setting loop {msgs[0]} to STOP")
                if self.loopr.sync != const.SYNC_NONE:
                    loop.status = const.LOOP_QUEUE_STOP
                else:
                    loop.status = const.LOOP_STOP
            elif msgs[1] == const.CTRL_FIXED_BEATS:
                fixed_beats = int(np.ceil(msgs[2] / 4))
                if fixed_beats != loop.fixed_beats:
                    print(f"Setting loop {loop.id} fixed beats to {fixed_beats}")
                    loop.fixed_beats = fixed_beats
            
            # To do implement queue statuses to new status logic

async def handle_midi_control(loopr: Loopr):
    mmap = const.MIDI_MAP
    controller = Controller(loopr)
    with mido.open_input() as inport:
        while True:
            msg = inport.poll()
            if msg:
                if msg.type == "note_on":
                    ctrl = mmap["note"].get((msg.channel, msg.note,))
                    if ctrl:
                        controller.handle(ctrl)
                elif msg.type == "control_change":
                    ctrl = mmap["control"].get((msg.control,))
                    if ctrl:
                        controller.handle((*ctrl, msg.value))
            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                print("Midi handler received cancelled")
                break