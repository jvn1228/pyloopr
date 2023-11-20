from rich import print
import sounddevice as sd
import mido
import sys

def listen_midi():
    print("Starting [bold]midi listener[/bold]")
    try:
        with mido.open_input() as inport:
            for msg in inport:
                print(msg)
    except KeyboardInterrupt:
        print("Exiting [bold]midi listener[/bold]")
        sys.exit(0)

def get_devices():
    print(sd.query_devices())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Need to specify util tool")
        sys.exit(1)

    util = sys.argv[1]
    match util:
        case "listen_midi": listen_midi()
        case "get_devices": get_devices()
        case _: print("Unknown util tool") or sys.exit(1)