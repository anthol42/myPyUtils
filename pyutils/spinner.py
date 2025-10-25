import time
import threading
from typing import Union, Literal
moon = tuple("🌑🌒🌓🌔🌕🌖🌗🌘")
modern = tuple("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
legacy = ("[|]", "[/]", "[-]", "[\\]")
trig = ("◢", "◣", "◤", "◥")
circle = ('◐','◓','◑','◒')
bounce = ('⠁','⠂','⠄','⠂', '⠄')
globe = ('🌍','🌎','🌏')
clock = ('🕐','🕑','🕒','🕓','🕔','🕕','🕖','🕗','🕘','🕙','🕚','🕛')
wave = ('▁','▃','▄','▅','▆','▇','▆','▅','▄','▃')

class Spinner:
    def __init__(self, desc: str = "", sep: str = "  ", refresh_rate: float = 4, chars: Union[tuple[str], Literal[
        'legacy','modern', 'trig', 'circle', 'bounce', 'wave', 'moon', 'globe', 'clock'
    ]] = 'modern'):
        if isinstance(chars, str):
            match chars:
                case 'legacy':
                    chars = legacy
                case 'modern':
                    chars = modern
                case 'trig':
                    chars = trig
                case 'circle':
                    chars = circle
                case 'bounce':
                    chars = bounce
                case 'wave':
                    chars = wave
                case 'moon':
                    chars = moon
                case 'globe':
                    chars = globe
                case 'clock':
                    chars = clock
                case _:
                    raise ValueError(f"Unknown spinner type: {chars}")
        self.chars = chars
        self.desc = desc
        self.sep = sep
        self.refresh_rate = refresh_rate

    def start(self) -> 'Spinner':
        self._stop_event = threading.Event()
        self._runner = threading.Thread(target=self.spinner,
                                        args=(self._stop_event, self.chars, self.desc, self.sep, self.refresh_rate**-1),
                                        daemon=True)
        self._runner.start()
        return self

    def stop(self) -> 'Spinner':
        self._stop_event.set()
        self._runner.join()
        return self

    def __enter__(self) -> 'Spinner':
        return self.start()

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.stop()
        print(f"\033[2K\r", end="", flush=True)
        return False

    @staticmethod
    def spinner(stop_event, chars: list[str], desc: str, sep: str = "  ", delay: float = 0.25):
        pointer = 0
        while not stop_event.is_set():
            print(f'\033[2K\r{chars[pointer]}{sep}{desc}', end="")
            pointer += 1
            pointer %= len(chars)
            time.sleep(delay)