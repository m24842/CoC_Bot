from multiprocessing import freeze_support, Process, Event
from coc_bot import CoC_Bot
from utils import parse_args
from log import enable_logging
from utils import init_instance
from gui import init_gui, get_gui

def main_proc(stop_event):
    args = parse_args()
    if args.gui:
        init_gui(args.id, stop_event=stop_event)
        if args.id is None: args.id = get_gui().get_id()
    init_instance(args.id)
    enable_logging(args.id)
    bot = CoC_Bot()
    bot.run()

if __name__ == "__main__":
    freeze_support()
    
    stop_event = Event()
    p = Process(target=main_proc, args=(stop_event,))
    p.start()
    try:
        stop_event.wait()
    finally:
        stop_event.set()
        p.terminate()
        p.join()