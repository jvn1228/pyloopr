import sounddevice as sd
from rich import print
from pyloopr.audio_engine import AudioEngine
from pyloopr.state import Loopr
import pyloopr.const as const
import asyncio

async def iterate_loops(loopr: Loopr):
    for loop in range(const.LOOPS):
        print(f"Now recording on loop {loop}")
        loopr.loop_statuses[loop] = const.LOOP_REC
        await asyncio.sleep(2)
        loopr.loop_statuses[loop] = const.LOOP_PLAY

async def main():
    device_info = sd.query_devices(sd.default.device, 'input')
    loopr = Loopr(
        192000,
        1,
        device_info["name"]
    )
    print(f"Device: [bold green]{device_info['name']}[/bold green]")
    print(f"Sample rate: [bold]{loopr.sample_rate}[/bold]")

    audio_engine = AudioEngine(loopr)

    await audio_engine.run()

    print("Exiting pyloopr")

if __name__ == "__main__":
    asyncio.run(main())