# midi message.type
NOTE_ON = "note_on"
NOTE_OFF = "note_off"

# buffer samples
BUFFER_REC = 4096
# 60 MB?
BUFFER_LOOP = 1024 * 1000 * 60
LOOPS = 4

# loop state
LOOP_STOP = 0
LOOP_REC = 1
LOOP_PLAY = 2
LOOP_DUB = 3
LOOP_QUEUE_REC = 4
LOOP_QUEUE_STOP = 5
LOOP_QUEUE_PLAY = 6

# sync
SYNC_NONE = 0
SYNC_BAR = 1
SYNC_HALFBAR = 2
SYNC_BEAT = 3
SYNC_HALFBEAT = 4
SYNC_QUARTERBEAT = 5

# trigger mode
TRIGGER_TOGGLE = 0
TRIGGER_GATE = 1

# controls
CTRL_LOOP1 = 0
CTRL_LOOP2 = 1
CTRL_LOOP3 = 2
CTRL_LOOP4 = 3
CTRL_STATUS = 4
CTRL_STOP = 5
CTRL_FIXED_BEATS = 6

# reconfigure these controls so its (system/loop, loop id, control)
# to handle more than 4 loops maybe
# for midi control
MIDI_MAP = {
    "note": {
        (9, 40): (CTRL_LOOP1, CTRL_STATUS),
        (9, 41): (CTRL_LOOP2, CTRL_STATUS),
        (9, 42): (CTRL_LOOP3, CTRL_STATUS),
        (9, 43): (CTRL_LOOP4, CTRL_STATUS),
        (9, 36): (CTRL_LOOP1, CTRL_STOP),
        (9, 37): (CTRL_LOOP2, CTRL_STOP),
        (9, 38): (CTRL_LOOP3, CTRL_STOP),
        (9, 39): (CTRL_LOOP4, CTRL_STOP),
    },
    "control": {
        (21,): (CTRL_LOOP1, CTRL_FIXED_BEATS),
        (22,): (CTRL_LOOP2, CTRL_FIXED_BEATS),
        (23,): (CTRL_LOOP3, CTRL_FIXED_BEATS),
        (24,): (CTRL_LOOP4, CTRL_FIXED_BEATS),
    }
}