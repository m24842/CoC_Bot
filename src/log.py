import sys
import loguru
import warnings
from pathlib import Path

loguru.logger.remove()
warnings.filterwarnings("ignore", category=UserWarning, module='torch')

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
    log_file = open(LOG_PATH, "a", buffering=1)
    try:
        LOG_PATH.chmod(0o666)
    except:
        pass

    if getattr(sys, "frozen", False):
        sys.stdout = Tee(*[log_file])
        sys.stderr = Tee(*[log_file])
    else:
        sys.stdout = Tee(*[log_file, sys.__stdout__])
        sys.stderr = Tee(*[log_file, sys.__stderr__])