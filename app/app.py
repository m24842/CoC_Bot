import sys

sys.path.append("src")

import os
import time
import sqlite3
from waitress import serve
from flask import Flask, render_template, jsonify, abort, request
from configs import *

PATH = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

run_statuses = {}
end_times = {}
ids = set()

def init_db(id):
    db_path = os.path.join(PATH, f"data/notifications_{id}.db")
    with sqlite3.connect(db_path) as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS notifications_{id} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_stamp REAL,
                data TEXT
            )
        """)
        conn.commit()

def get_notifications(id, limit=3):
    db_path = os.path.join(PATH, f"data/notifications_{id}.db")
    if not os.path.exists(db_path): return []
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(f"SELECT time_stamp, data FROM notifications_{id} ORDER BY time_stamp DESC LIMIT ?", (limit,))
        return [{"time_stamp": row[0], "data": row[1]} for row in cursor.fetchall()]

@app.route("/", methods=["GET"])
def home():
    return render_template("home.html", ids=list(ids))

@app.route("/<id>", methods=["GET"])
def instance(id):
    init_db(id)
    if id not in ids: abort(404)
    return render_template("instance.html", id=id, end_time=end_times.get(id, 0), current_time=time.time(), notifications=get_notifications(id), run_status=run_statuses.get(id, ""))

@app.route("/<id>/current_time", methods=["GET"])
def handle_current_time(id):
    return {"current_time": time.time()}

@app.route("/<id>/end_time", methods=["GET", "POST"])
def handle_end_time(id):
    global end_times
    if request.method == "POST":
        if "preset" in request.form:
            end_times[id] = int(request.form["preset"]) * 60 + time.time()
        elif "cancel" in request.form:
            end_times[id] = 0
        else:
            end_times[id] = int(request.form["custom_input"]) * 60 + time.time()
    
    return {"end_time": end_times.get(id, 0)}

@app.route("/<id>/running", methods=["GET"])
def handle_running(id):
    return {"running": end_times.get(id, 0) == 0 or end_times.get(id, 0) < time.time()}

@app.route("/<id>/status", methods=["GET", "POST"])
def handle_status(id):
    global run_statuses
    if request.method == "POST":
        data = request.json
        run_statuses[id] = data["status"]

    return {"status": run_statuses.get(id, "")}

@app.route("/<id>/notify", methods=["POST"])
def handle_notify(id):
    data = request.json
    db_path = os.path.join(PATH, f"data/notifications_{id}.db")
    if os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            conn.execute(f"INSERT INTO notifications_{id} (time_stamp, data) VALUES (?, ?)",
                            (time.time(), str(data)))
    return jsonify({"status": "success", "received": data})

@app.route("/<id>/notifications", methods=["POST"])
def handle_notifications(id):
    n = request.json
    return jsonify(get_notifications(id, n))

@app.route("/instances", methods=["GET", "POST"])
def instances():
    global ids
    if request.method == "POST":
        data = request.json
        id = data.get("id", "").strip()
        if id == "":
            return jsonify({"status": "error", "message": "Invalid ID"}), 400
        ids.add(id)
        init_db(id)
        return jsonify({"status": "success", "id": id})

    return jsonify({"ids": list(ids)})

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

if __name__ == "__main__":
    if True: app.run(host="0.0.0.0", port=WEB_APP_PORT, debug=True)
    else: serve(app, host="0.0.0.0", port=WEB_APP_PORT, threads=8)