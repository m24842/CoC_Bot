import os
import sys

class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, message):
        for s in self.streams:
            s.write(message)
            s.flush()

    def flush(self):
        for s in self.streams:
            s.flush()

def enable_logging(id="main"):
    os.makedirs("debug", exist_ok=True)
    log_file = open(f"debug/{id}_output.log", "a")
    sys.stdout = Tee(sys.stdout, log_file)