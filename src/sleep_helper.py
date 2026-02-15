import os
import sys
import subprocess
import time
import signal

def displaysleep(value):
    subprocess.run(["pmset", "-a", "displaysleep", str(value)], check=True)

def parent_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def main():
    parent_pid = int(sys.argv[1])
    displaysleep(1)

    def cleanup(*args):
        try:
            displaysleep(0)
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    try:
        while parent_alive(parent_pid):
            time.sleep(60)
    finally:
        cleanup()

if __name__ == "__main__":
    main()