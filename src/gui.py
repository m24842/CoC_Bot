try:
    import configs
except:
    import configs_build as configs

COC_BOT_GUI = None

def find_open_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def run_gui(server_port, pipe, debug=False):
    import sys, webview
    
    url = f"http://127.0.0.1:{server_port}"
    window = webview.create_window(
        "CoC Bot",
        url=url,
        width=400,
        height=600,
        min_size=(400, 600),
        resizable=(sys.platform == "darwin"),
    )
    
    def on_closed():
        pipe.send(-1)
    
    def set_aspect_ratio():
        if sys.platform != "darwin": return
        nswindow = window.native
        nswindow.setAspectRatio_((2, 3))

    window.events.closed += on_closed
    window.events.loaded += set_aspect_ratio
    webview.start(debug=debug)

class GUI:
    def __init__(self, id=None, debug=False):
        from multiprocessing import Process, Pipe
        from gui_server.gui_server import start_server
        
        if id is not None: assert id in configs.INSTANCE_IDS, f"Invalid instance ID"
        self.debug = debug
        self.id = id
        parent_conn, child_conn = Pipe()
        self.pipe = parent_conn
        self.server_port = find_open_port()
        self.server_proc = Process(target=start_server, args=(child_conn, self.server_port, id, False,))
        self.server_proc.start()
        self.window_proc = Process(target=run_gui, args=(self.server_port, child_conn, self.debug))
    
    def start(self):
        self.window_proc.start()

    def stop(self):
        if self.server_proc.is_alive():
            self.server_proc.terminate()
            self.server_proc.join()
        if self.window_proc.is_alive():
            self.window_proc.terminate()
            self.window_proc.join()

def init_gui(id=None, debug=False):
    global COC_BOT_GUI
    COC_BOT_GUI = GUI(id, debug=debug)
    COC_BOT_GUI.start()
    return COC_BOT_GUI.pipe

def get_gui():
    return COC_BOT_GUI

if __name__ == "__main__":
    pipe = init_gui(None, debug=True)
    while True:
        try: print("GUI Received:", pipe.recv())
        except EOFError: break
    get_gui().stop()
