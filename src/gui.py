import time
import webview
import requests
from multiprocessing import Process, Pipe, Event
from gui_server.gui_server import start_server
import configs

COC_BOT_GUI = None

def run_gui(server_port, stop_event, debug=False):
    url = f"http://localhost:{server_port}"
    window = webview.create_window(
        "CoC Bot",
        url=url,
        width=400,
        height=600,
        resizable=False,
    )
    
    def on_closed():
        stop_event.set()

    window.events.closed += on_closed
    webview.start(debug=debug)

class GUI:
    def __init__(self, id=None, stop_event=None, debug=False):
        if id is not None: assert id in configs.INSTANCE_IDS, f"Invalid instance ID"
        self.debug = debug
        self.id = id
        self.stop_event = stop_event if stop_event is not None else Event()
        parent_conn, child_conn = Pipe()
        self.server_proc = Process(target=start_server, args=(child_conn, id))
        self.server_proc.start()
        self.server_port = parent_conn.recv()
        self.window_proc = Process(target=run_gui, args=(self.server_port, self.stop_event, self.debug))
    
    def get_id(self):
        while self.id in [None, ""]:
            response = requests.get(f"http://localhost:{self.server_port}/id")
            if response.ok:
                self.id = response.json().get("id")
            time.sleep(0.1)
        return self.id
    
    def start(self):
        self.window_proc.start()

    def stop(self):
        if self.server_proc.is_alive():
            self.server_proc.terminate()
            self.server_proc.join()
        if self.window_proc.is_alive():
            self.window_proc.terminate()
            self.window_proc.join()

def init_gui(id=None, stop_event=None, debug=False):
    global COC_BOT_GUI
    COC_BOT_GUI = GUI(id, stop_event=stop_event, debug=debug)
    COC_BOT_GUI.start()

def get_gui():
    return COC_BOT_GUI

if __name__ == "__main__":
    init_gui(None, debug=True)
    get_gui().stop_event.wait()
    get_gui().stop()
