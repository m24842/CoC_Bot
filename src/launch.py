def launch_proc(args):
    from log import enable_logging
    from utils import init_instance
    from coc_bot import CoC_Bot
    
    init_instance(args.id)
    enable_logging(args.id)
    bot = CoC_Bot()
    bot.run()

def cmd_launch(args):
    import utils
    if utils.DISABLE_DEVICE_SLEEP: utils.disable_sleep()
    launch_proc(args)

def gui_launch(args):
    from multiprocessing import Process
    import utils
    from gui import init_gui, get_gui
    from copy import deepcopy
    
    procs = {}
    pipe = init_gui(args.id)
    args.gui_port = get_gui().server_port
    
    if utils.DISABLE_DEVICE_SLEEP: Process(target=utils.disable_sleep).start()
    
    if args.id is not None:
        p = Process(target=launch_proc, args=(args,))
        p.start()
        procs[args.id] = p
    try:
        while True:
            data = pipe.recv()
            if data == -1: raise SystemExit
            action, id = data.get("action"), data.get("id")
            if action == "start":
                args_copy = deepcopy(args)
                args_copy.id = data.get("id")
                p = Process(target=launch_proc, args=(args_copy,))
                p.start()
                procs[id] = p
            elif action == "stop":
                p = procs.pop(id, None)
                if p and p.is_alive():
                    p.terminate()
                    p.join()
    except (EOFError, KeyboardInterrupt, SystemExit):
        get_gui().stop()
        pipe.close()
        for p in procs.values():
            if p and p.is_alive():
                p.terminate()
                p.join()

def launch():
    import utils
    args = utils.parse_args()
    if args.gui: gui_launch(args)
    else: cmd_launch(args)
