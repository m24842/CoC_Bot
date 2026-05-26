import sys
import loguru
import warnings
from pathlib import Path

loguru.logger.remove()
warnings.filterwarnings("ignore", category=UserWarning, module='torch')

class Logger:
    def __init__(self, level):
        self.level = level

    def write(self, data):
        data = data.strip()
        if data:
            loguru.logger.log(self.level, data)

    def flush(self):
        pass

class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except:
                pass

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except:
                pass

def enable_logging(id):
    if getattr(sys, "frozen", False):
        APP_DATA_DIR = Path.home() / ".CoC_Bot"
        APP_DATA_DIR.mkdir(exist_ok=True)
        LOG_DIR = APP_DATA_DIR / "debug"
    else:
        LOG_DIR = Path("debug")

    LOG_DIR.mkdir(exist_ok=True)

    LOG_PATH = LOG_DIR / f"{id}.log"

    exclude_modules = [
        "pyminitouch",
    ]

    loguru.logger.add(
        LOG_PATH,
        rotation="10 MB",
        retention=5,
        compression="zip",
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        filter=lambda record: not any(record["name"].startswith(mod) for mod in exclude_modules),
    )

    if getattr(sys, "frozen", False):
        sys.stdout = Logger("INFO")
        sys.stderr = Logger("ERROR")
    else:
        sys.stdout = Tee(sys.__stdout__, Logger("INFO"))
        sys.stderr = Tee(sys.__stderr__, Logger("ERROR"))