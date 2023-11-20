from dataclasses import dataclass, field
import pyloopr.const as const
import numpy as np
from typing import Callable

@dataclass
class Loop:
    id: int
    sample_rate: int
    time_signature: list[int] = field(default_factory=lambda: [4, 4])
    len: int = 0
    buf: np.ndarray = field(default_factory=lambda: np.empty((const.BUFFER_LOOP, 1), dtype="float32"))
    _status: int = const.LOOP_STOP
    _old_status: int = const.LOOP_STOP
    idx: int = 0
    # if return true indicates master loop >= sync point
    trigger: Callable[[], bool] | None = None
    pending: bool = False
    # fixed record length, if > 0 then is number of beats to record in a new loop
    fixed_beats: int = 0
    fixed_beats_post_status: int = const.LOOP_DUB
    # not implemented
    # gate, toggle
    trigger_mode: int = const.TRIGGER_TOGGLE
    # loop or one shot
    continuous: bool = True

    @property
    def status(self) -> int:
        return self._status
    
    @status.setter
    def status(self, val):
        self._old_status = self._status
        self._status = val
    
    @property
    def old_status(self) -> int:
        return self._old_status
    
    @property
    def beat_len(self) -> float:
        return self.len / self.time_signature[0]
