import sys
import time
import json
import webview
import requests
from pathlib import Path
from multiprocessing import Process, Manager, Event
import configs

COC_BOT_GUI = None

def run_gui(shared_dict, stop_event, debug=False):
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.resolve()
    html_file = base_path / "gui/gui.html"
    window = webview.create_window(
        "CoC Bot",
        f"file://{html_file}",
        width=400,
        height=600,
        resizable=False,
        js_api=GUI_API(shared_dict),
    )
    
    def on_closed():
        stop_event.set()

    window.events.closed += on_closed
    webview.start(debug=debug)

class GUI:
    def __init__(self, id=None, stop_event=None, debug=False):
        if id is not None: assert id in configs.INSTANCE_IDS, f"Invalid instance ID"
        self.debug = debug
        self.stop_event = stop_event if stop_event is not None else Event()
        self.manager = Manager()
        self.shared_dict = self.manager.dict()
        self.shared_dict["id"] = id
        self.shared_dict["status"] = ""
        self.shared_dict["end_time"] = 0
        self.shared_dict["exclude"] = self.manager.dict({
            "upgrade_heros": not configs.UPGRADE_HEROS,
            "upgrade_home_base": not configs.UPGRADE_HOME_BASE,
            "upgrade_builder_base": not configs.UPGRADE_BUILDER_BASE,
            "upgrade_home_lab": not configs.UPGRADE_HOME_LAB,
            "upgrade_builder_lab": not configs.UPGRADE_BUILDER_LAB,
            "attack_home_base": not configs.ATTACK_HOME_BASE,
            "attack_builder_base": not configs.ATTACK_BUILDER_BASE,
        })
        self.proc = Process(target=run_gui, args=(self.shared_dict, self.stop_event, self.debug), daemon=True)
    
    def get_id(self):
        while self.shared_dict["id"] is None:
            time.sleep(0.1)
        return self.shared_dict["id"]
    
    def set_status(self, status):
        self.shared_dict["status"] = status
    
    def get_exclusions(self):
        return [k for k, v in self.shared_dict["exclude"].items() if v]

    def start(self):
        self.proc.start()

    def stop(self):
        self.stop_event.set()
        self.proc.terminate()
        self.proc.join()

class GUI_API:
    def __init__(self, shared_dict):
        self.shared_dict = shared_dict
        self.url = configs.WEB_APP_URL
    
    def get_id(self):
        return self.shared_dict["id"]
    
    def set_id(self, id):
        if id in configs.INSTANCE_IDS:
            self.shared_dict["id"] = id
            return 1
        return 0
    
    def get_exclusions(self):
        try:
            return requests.get(
                f"{self.url}/{self.shared_dict['id']}/exclude",
                auth=(configs.WEB_APP_AUTH_USERNAME, configs.WEB_APP_AUTH_PASSWORD),
            ).json()
        except:
            excluded = [k for k, v in self.shared_dict["exclude"].items() if v]
            return {"exclusions": excluded}
    
    def exclude_item(self, action, item):
        try:
            requests.post(
                f"{self.url}/{self.shared_dict['id']}/exclude",
                auth=(configs.WEB_APP_AUTH_USERNAME, configs.WEB_APP_AUTH_PASSWORD),
                json={"action": action, "item": item}
            ).json()
        except:
            if action == "add":
                self.shared_dict["exclude"][item] = True
            elif action == "remove":
                self.shared_dict["exclude"][item] = False
    
    def get_notifications(self):
        return requests.post(
            f"{self.url}/{self.shared_dict['id']}/notifications",
            auth=(configs.WEB_APP_AUTH_USERNAME, configs.WEB_APP_AUTH_PASSWORD),
            json=json.dumps(3)
        ).json()
    
    def get_current_time(self):
        try:
            return requests.get(
                f"{self.url}/{self.shared_dict['id']}/current_time",
                auth=(configs.WEB_APP_AUTH_USERNAME, configs.WEB_APP_AUTH_PASSWORD),
            ).json()
        except:
            return {"current_time": int(time.time())}

    def get_end_time(self):
        try:
            return requests.get(
                f"{self.url}/{self.shared_dict['id']}/end_time",
                auth=(configs.WEB_APP_AUTH_USERNAME, configs.WEB_APP_AUTH_PASSWORD),
            ).json()
        except:
            return {"end_time": self.shared_dict["end_time"]}
    
    def set_end_time(self, end_time):
        try:
            requests.post(
                f"{self.url}/{self.shared_dict['id']}/end_time",
                auth=(configs.WEB_APP_AUTH_USERNAME, configs.WEB_APP_AUTH_PASSWORD),
                json={"time": end_time}
            ).json()
        except:
            self.shared_dict["end_time"] = 60 * int(end_time) + time.time()

    def get_status(self):
        try:
            return requests.get(
                f"{self.url}/{self.shared_dict['id']}/status",
                auth=(configs.WEB_APP_AUTH_USERNAME, configs.WEB_APP_AUTH_PASSWORD),
            ).json()
        except:
            return {"status": self.shared_dict["status"]}

def init_gui(id=None, stop_event=None, debug=False):
    global COC_BOT_GUI
    COC_BOT_GUI = GUI(id, stop_event=stop_event, debug=debug)
    COC_BOT_GUI.start()

def get_gui():
    return COC_BOT_GUI

if __name__ == "__main__":
    init_gui("main", debug=True)
