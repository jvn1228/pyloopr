from dataclasses import dataclass, field
import numpy as np
import pyloopr.const as const
from pyloopr.loop import Loop

@dataclass
class Loopr:
    sample_rate: int
    in_channels: int
    device: str
    bar_len: int = 0
    bars: int = 1
    tempo: float = 120.0
    time_signature: list[int] = field(default_factory=lambda: [4, 4])
    sync_chain: list[int] = field(default_factory=lambda: [])
    sync: int = const.SYNC_BAR
    play_idx: int = 0
    loops_recorded: int = 0
    loops_playing: int = 0
    monitor_buffer: np.ndarray = field(default_factory=lambda: np.empty((const.BUFFER_REC, 1), dtype="float32"))

    def __post_init__(self):
        self.loops: list[Loop] = [Loop(i, self.sample_rate, self.time_signature) for i in range(const.LOOPS)]