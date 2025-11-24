import time
from flask_apscheduler import APScheduler
from app import instances, update_known_instances

scheduler = APScheduler()
scheduler.add_job("instance_caching", update_known_instances, trigger="interval", seconds=1)
scheduler.start()

while True:
    time.sleep(1)
