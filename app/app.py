import sys

sys.path.append("src")

import time
import sqlite3
from waitress import serve
from flask import Flask, render_template, jsonify, request
from configs import *

app = Flask(__name__)

run_status = ""
end_time = 0

def init_db():
    with sqlite3.connect(NOTIFICATIONS_DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_stamp REAL,
                data TEXT
            )
        """)

def get_notifications(limit=3):
    with sqlite3.connect(NOTIFICATIONS_DB_PATH) as conn:
        cursor = conn.execute("SELECT time_stamp, data FROM notifications ORDER BY time_stamp DESC LIMIT ?", (limit,))
        return [{"time_stamp": row[0], "data": row[1]} for row in cursor.fetchall()]

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", end_time=end_time, current_time=time.time(), notifications=get_notifications(), run_status=run_status)

@app.route("/current_time", methods=["GET"])
def handle_current_time():
    return {"current_time": time.time()}

@app.route("/end_time", methods=["GET", "POST"])
def handle_end_time():
    global end_time
    if request.method == "POST":
        if "preset" in request.form:
            end_time = int(request.form["preset"]) * 60 + time.time()
        elif "cancel" in request.form:
            end_time = 0
        else:
            end_time = int(request.form["custom_input"]) * 60 + time.time()
    
    return {"end_time": end_time}

@app.route("/running", methods=["GET"])
def handle_running():
    return {"running": end_time == 0 or end_time < time.time()}

@app.route("/status", methods=["GET", "POST"])
def handle_status():
    global run_status
    if request.method == "POST":
        data = request.json
        run_status = data["status"]

    return {"status": run_status}

@app.route("/notify", methods=["GET", "POST"])
def handle_notify():
    if request.method == "POST":
        data = request.json
        with sqlite3.connect(NOTIFICATIONS_DB_PATH) as conn:
            conn.execute("INSERT INTO notifications (time_stamp, data) VALUES (?, ?)",
                         (time.time(), str(data)))
        return jsonify({"status": "success", "received": data})
    
    return jsonify(get_notifications())

@app.after_request
def add_no_cache_headers(response):
    cache_control = "no-store, no-cache, must-revalidate, max-age=0"
    
    if request.path.startswith("/static/"):
        cache_control = "public, max-age=2592000"
    
    response.headers["Cache-Control"] = cache_control
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    init_db()
    if DEBUG: app.run(host="0.0.0.0", port=WEB_APP_PORT, debug=True)
    else: serve(app, host="0.0.0.0", port=WEB_APP_PORT, threads=8)