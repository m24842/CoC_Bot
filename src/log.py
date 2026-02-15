import os
import sys
import loguru
import warnings

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

def enable_logging(id="main"):
    base_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    log_dir = os.path.join(base_dir, "debug")
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, f"{id}.log")
    log_file = open(log_path, "a", buffering=1)
    try:
        os.chmod(log_path, 0o666)
    except:
        pass

    if getattr(sys, "frozen", False):
        streams = [log_file]
    else:
        streams = [log_file, sys.stdout, sys.stderr]

    sys.stdout = Tee(*streams)
    sys.stderr = Tee(*streams)