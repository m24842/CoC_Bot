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
from flask import Flask, render_template, jsonify, abort, request
from configs import *

app = Flask(__name__)
bot_pipe = None

class Instance:
    def __init__(self, id=None):
        self.id = id if id is not None else ""
        self.run_status = ""
        self.end_time = 0
        task_settings = {
            "heroes": not UPGRADE_HEROES,
            "home_base": not UPGRADE_HOME_BASE,
            "builder_base": not UPGRADE_BUILDER_BASE,
            "home_lab": not UPGRADE_HOME_LAB,
            "builder_lab": not UPGRADE_BUILDER_LAB,
            "home_attacks": not ATTACK_HOME_BASE,
            "builder_attacks": not ATTACK_BUILDER_BASE,
            "lab_assistant": not ASSIGN_LAB_ASSISTANT,
            "builder_apprentice": not ASSIGN_BUILDER_APPRENTICE,
        }
        self.exclusions = set(k for k, v in task_settings.items() if v)

instances = {}

@app.route("/", methods=["GET"])
def home():
    return render_template(
        "home.html",
        ids=sorted(list(instances.keys())),
    )

@app.route("/<id>", methods=["GET"])
def handle_instance(id):
    instance = instances.get(id)
    if not instance: abort(404)
    return render_template(
        "instance.html",
        id=id,
        web_app_url=WEB_APP_URL,
        end_time=instance.end_time,
        current_time=time.time(),
        run_status=instance.run_status,
        exclusions=list(instance.exclusions),
    )

@app.route("/instance", methods=["POST"])
def handle_instance_start_stop():
    data = request.json
    action = data.get("action", "")
    id = data.get("id", "")
    if action == "start":
        if id not in INSTANCE_IDS:
            return jsonify(0)
        if id not in instances:
            instances[id] = Instance(id)
            bot_pipe.send({"action": "start", "id": id})
        return jsonify(1)
    elif action == "stop":
        instance = instances.pop(id, None)
        if instance:
            bot_pipe.send({"action": "stop", "id": id})
        return jsonify(1)
    return jsonify(0)

@app.route("/current_time", methods=["GET"])
def handle_current_time():
    return {"current_time": time.time()}

@app.route("/<id>/end_time", methods=["GET", "POST"])
def handle_end_time(id):
    instance = instances.get(id)
    if not instance: abort(404)
    if request.method == "POST":
        data = request.json.get("time", 0)
        instance.end_time = int(data) * 60 + time.time()
    return {"end_time": instance.end_time}

@app.route("/<id>/running", methods=["GET"])
def handle_running(id):
    instance = instances.get(id)
    if not instance: abort(404)
    return {"running": instance.end_time == 0 or instance.end_time < time.time()}

@app.route("/<id>/status", methods=["GET", "POST"])
def handle_status(id):
    instance = instances.get(id)
    if not instance: abort(404)
    if request.method == "POST":
        data = request.json
        instance.run_status = data.get("status", "")
    return {"status": instance.run_status}

@app.route("/<id>/exclude", methods=["GET", "POST"])
def handle_exclude(id):
    instance = instances.get(id)
    if not instance: abort(404)
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

def start_server(pipe, id=None, debug=False):
    global bot_pipe
    bot_pipe = pipe
    
    if not debug:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    if id is not None:
        instances[id] = Instance(id)
    
    port = find_open_port()
    bot_pipe.send(port)
    app.run(port=port, debug=DEBUG)

if __name__ == "__main__":
    from multiprocessing import Pipe
    parent_conn, child_conn = Pipe()
    start_server(child_conn)