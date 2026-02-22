import sys
from pathlib import Path

if hasattr(sys, "_MEIPASS"):
    path = Path(sys._MEIPASS) / "gui_server"
else:
    path = Path(__file__).parent.resolve()
    sys.path.append(str(path.parent))

sys.path.append(str(path))

import os
import time
import socket
from flask import Flask, render_template, jsonify, request
from configs import *

app = Flask(__name__)

class Instance:
    def __init__(self, id=None):
        self.id = id if id is not None else ""
        self.run_status = ""
        self.end_time = 0
        task_settings = {
            "heros": not UPGRADE_HEROS,
            "home_base": not UPGRADE_HOME_BASE,
            "builder_base": not UPGRADE_BUILDER_BASE,
            "home_lab": not UPGRADE_HOME_LAB,
            "builder_lab": not UPGRADE_BUILDER_LAB,
            "home_attacks": not ATTACK_HOME_BASE,
            "builder_attacks": not ATTACK_BUILDER_BASE,
            "lab_assistant": not ASSIGN_LAB_ASSISTANT,
            "builder_assistant": not ASSIGN_BUILDER_ASSISTANT,
        }
        self.exclusions = set(k for k, v in task_settings.items() if v)

instance = Instance("")

@app.route("/", methods=["GET"])
def home():
    return render_template(
        "gui.html",
        id=instance.id,
        web_app_url=WEB_APP_URL,
        current_time=time.time(),
        end_time=instance.end_time,
        run_status=instance.run_status,
        exclusions=list(instance.exclusions)
    )

@app.route("/id", methods=["GET", "POST"])
def handle_id():
    global instance
    if request.method == "GET":
        return jsonify({"id": instance.id})
    elif request.method == "POST":
        id = request.json.get("id", "").strip()
        if id not in INSTANCE_IDS:
            return jsonify(0)
        instance.id = id
        return jsonify(1)

@app.route("/current_time", methods=["GET"])
def handle_current_time():
    return {"current_time": time.time()}

@app.route("/end_time", methods=["GET", "POST"])
def handle_end_time():
    if request.method == "POST":
        data = request.json.get("time", 0)
        instance.end_time = int(data) * 60 + time.time()
    return {"end_time": instance.end_time}

@app.route("/running", methods=["GET"])
def handle_running():
    return {"running": instance.end_time == 0 or instance.end_time < time.time()}

@app.route("/status", methods=["GET", "POST"])
def handle_status():
    if request.method == "POST":
        data = request.json
        instance.run_status = data.get("status", "")
    return {"status": instance.run_status}

@app.route("/exclude", methods=["GET", "POST"])
def handle_exclude():
    if request.method == "POST":
        data = request.json
        action = data.get("action", "")
        item = data.get("item", "")
        if action == "add":
            instance.exclusions.add(item)
        elif action == "remove":
            instance.exclusions.discard(item)
    return {"exclusions": sorted(list(instance.exclusions))}

def find_open_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def start_server(port_pipe, id=None):
    global instance
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    instance = Instance(id)
    port = find_open_port()
    port_pipe.send(port)
    port_pipe.close()
    app.run(port=port, debug=DEBUG)

if __name__ == "__main__":
    from multiprocessing import Pipe
    parent_conn, child_conn = Pipe()
    start_server(child_conn)