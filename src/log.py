import os
import sys

class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()

    def flush(self):
        for s in self.streams:
            s.flush()

def enable_logging(id="main"):
    os.makedirs("debug", exist_ok=True)

    log = open(f"debug/{id}.log", "a", buffering=1)

    sys.stdout = Tee(sys.stdout, log)
    sys.stderr = Tee(sys.stderr, log)