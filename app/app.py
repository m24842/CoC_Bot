import sys

sys.path.append("src")

import os
import time
import json
import sqlite3
from waitress import serve
from flask import Flask, render_template, jsonify, abort, request
from configs import *

PATH = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

class Instance:
    def __init__(self, id, run_status="", end_time=0, exclusions=set()):
        self.id = id
        self.run_status = run_status
        self.end_time = end_time
        self.exclusions = exclusions
        self.data_path = os.path.join(PATH, "data")
        self.init_db(id)
    
    def __eq__(self, other):
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
    
    def to_dict(self):
        return {
            "id": self.id,
            "run_status": self.run_status,
            "end_time": self.end_time,
            "exclusions": sorted(list(self.exclusions)),
        }
    
    def init_db(self, id):
        notifications_path = os.path.join(self.data_path, f"{id}_notifications.db")
        if not os.path.exists(notifications_path):
            with sqlite3.connect(notifications_path) as conn:
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {id}_notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        time_stamp REAL,
                        data TEXT
                    )
                """)
                conn.commit()
    
    def get_notifications(self, limit=3):
        notifications_path = os.path.join(self.data_path, f"{self.id}_notifications.db")
        with sqlite3.connect(notifications_path) as conn:
            cursor = conn.execute(f"SELECT time_stamp, data FROM {self.id}_notifications ORDER BY time_stamp DESC LIMIT ?", (limit,))
            return [{"time_stamp": row[0], "data": row[1]} for row in cursor.fetchall()]

    def add_notification(self, data):
        notifications_path = os.path.join(self.data_path, f"{self.id}_notifications.db")
        with sqlite3.connect(notifications_path) as conn:
            conn.execute(f"INSERT INTO {self.id}_notifications (time_stamp, data) VALUES (?, ?)",
                            (time.time(), str(data)))
            conn.commit()

instances = {}

def get_known_instances():
    global instances
    data = {}
    cache_path = os.path.join(PATH, "data/cache.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                data = json.load(f)
        except:
            data = {}
    known_instances = data.get("known_instances", {})
    for id in known_instances:
        id = str(id)
        info = known_instances[id]
        instances[id] = Instance(id, run_status=info.get("run_status", ""), end_time=info.get("end_time", 0), exclusions=set(info.get("exclusions", [])))

def update_known_instances():
    global instances
    data = {id: instances[id].to_dict() for id in instances}
    cache_path = os.path.join(PATH, "data/cache.json")
    with open(cache_path, "w") as f:
        json.dump({"known_instances": data}, f, indent=4)

@app.route("/", methods=["GET"])
def home():
    return render_template("home.html", ids=sorted(instances.keys()))

@app.route("/<id>", methods=["GET"])
def handle_instance(id):
    instance = instances[id]
    if id not in instances: abort(404)
    return render_template("instance.html", id=id, end_time=instance.end_time, current_time=time.time(), notifications=instance.get_notifications(), exclusions=sorted(list(instance.exclusions)), run_status=instance.run_status)

@app.route("/<id>/current_time", methods=["GET"])
def handle_current_time(id):
    return {"current_time": time.time()}

@app.route("/<id>/end_time", methods=["GET", "POST"])
def handle_end_time(id):
    global instances
    instance = instances[id]
    if request.method == "POST":
        data = request.json.get("time", 0)
        instance.end_time = int(data) * 60 + time.time()
        update_known_instances()
    
    return {"end_time": instance.end_time}

@app.route("/<id>/running", methods=["GET"])
def handle_running(id):
    instance = instances[id]
    return {"running": instance.end_time == 0 or instance.end_time < time.time()}

@app.route("/<id>/status", methods=["GET", "POST"])
def handle_status(id):
    global instances
    instance = instances[id]
    if request.method == "POST":
        data = request.json
        instance.run_status = data.get("status", "")
        update_known_instances()

    return {"status": instance.run_status}

@app.route("/<id>/exclude", methods=["GET", "POST"])
def handle_exclude(id):
    global instances
    instance = instances[id]
    if request.method == "POST":
        data = request.json
        action = data.get("action", "")
        item = data.get("item", "")
        if action == "add":
            instance.exclusions.add(item)
        elif action == "remove":
            instance.exclusions.discard(item)
    return {"exclusions": sorted(list(instance.exclusions))}

@app.route("/<id>/notify", methods=["POST"])
def handle_notify(id):
    global instances
    data = request.json
    instances[id].add_notification(data)
    return jsonify({"status": "success", "received": data})

@app.route("/<id>/notifications", methods=["POST"])
def handle_notifications(id):
    n = request.json
    return jsonify(instances[id].get_notifications(n))

@app.route("/instances", methods=["GET", "POST"])
def handle_instances():
    global instances
    if request.method == "POST":
        data = request.json
        id = str(data.get("id", "")).strip()
        if id == "":
            return jsonify({"status": "error", "message": "Invalid ID"}), 400
        if id not in instances:
            instances[id] = Instance(id)
            update_known_instances()
        return jsonify({"status": "success", "id": id})

    return jsonify({"ids": sorted(instances.keys())})

@app.after_request
def add_cache_headers(response):
    if request.path.startswith("/static/"):
        # Cache static files for 30 days
        response.headers["Cache-Control"] = "public, max-age=2592000"
        response.headers.pop("Pragma", None)
        response.headers.pop("Expires", None)
    else:
        # No caching for dynamic routes
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

get_known_instances()
if __name__ == "__main__":
    if DEBUG: app.run(host="0.0.0.0", port=WEB_APP_PORT, debug=True)
    else: serve(app, host="0.0.0.0", port=WEB_APP_PORT, threads=8)