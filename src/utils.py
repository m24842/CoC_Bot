import os
import re
import sys
import cv2
import json
import time
import ctypes
import requests
import subprocess
import numpy as np
from configs import *

if sys.platform == "win32":
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

def disable_sleep():
    if sys.platform == "darwin":
        subprocess.run(["sudo", "pmset", "-a", "disablesleep", "1"], check=True)
    elif sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

def enable_sleep():
    if sys.platform == "darwin":
        subprocess.run(["sudo", "pmset", "-a", "disablesleep", "0"], check=True)
    elif sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

def check_color(color, frame, tol=10):
    assert len(frame.shape) == 3 and frame.shape[2] == 3, "Frame must be a color image"
    diff = np.abs(frame - np.array(color).reshape((1, 1, 3))).sum(2) <= tol
    return np.any(diff)

def get_text(frame, reader):
    result = reader.readtext(frame)
    return [text for _, text, _ in result if text.strip()]

def fix_digits(text):
    if type(text) is list:
        return [fix_digits(t) for t in text]
    return text.lower().replace('o', '0').replace('/', '1').replace('i', '1').replace('z', '2').replace('s', '5').replace('b', '6').replace('j', '7').replace('&', '8')

def parse_time(text):
    if type(text) is list:
        return [parse_time(t) for t in text]
    try:
        text = text.lower().replace(' ', '').replace('-', '')
        units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
        pattern = re.compile(r"(\d+)([dhms])")
        seconds = sum(int(v) * units[u] for v, u in pattern.findall(text))
        return seconds
    except:
        return 0

def click(device, x, y, n=1, delay=0):
    if x < 0: x = 1 + x
    if y < 0: y = 1 + y
    command = [f"input tap {int(x*WINDOW_DIMS[0])} {int(y*WINDOW_DIMS[1])}"] * n
    if delay == 0:
        command = " && ".join(command) + ";"
        device.shell(command)
    else:
        for c in command:
            device.shell(c)
            time.sleep(delay)

def swipe(device, x1, y1, x2, y2, duration=100):
    if x1 < 0: x1 = 1 + x1
    if y1 < 0: y1 = 1 + y1
    if x2 < 0: x2 = 1 + x2
    if y2 < 0: y2 = 1 + y2
    command = f"input swipe {int(x1*WINDOW_DIMS[0])} {int(y1*WINDOW_DIMS[1])} {int(x2*WINDOW_DIMS[0])} {int(y2*WINDOW_DIMS[1])} {duration};"
    device.shell(command)

def get_telegram_chat_id():
    data = {}
    cache_path = "src/cache.json"
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            data = json.load(f)
            if "telegram_chat_id" in data: return data["telegram_chat_id"]
    
    res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates").json()
    if res["ok"] and len(res["result"]) > 0:
        chat_id = res["result"][-1]["message"]["chat"]["id"]
        data["telegram_chat_id"] = chat_id
        with open(cache_path, "w") as f:
            json.dump(data, f, indent=4)
        return chat_id

    raise Exception("Failed to get Telegram chat ID")

def send_notification(text):
    if WEB_APP_URL != "":
        try: requests.post(f"{WEB_APP_URL}/notify", json=text)
        except: pass

    if TELEGRAM_BOT_TOKEN != "":
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data={"chat_id": get_telegram_chat_id(), "text": text})
        except: pass

class Frame_Handler:
    def __init__(self, device):
        self.device = device

    def get_frame(self, grayscale=True):
        frame = np.array(self.device.screenshot())
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if DEBUG: self.save_frame(frame, "debug/frame.png")
        if grayscale: frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        return frame

    def get_frame_section(self, x1, y1, x2, y2, high_contrast=False, thresh=200, grayscale=True):
        if x1 < 0: x1 = 1 + x1
        if y1 < 0: y1 = 1 + y1
        if x2 < 0: x2 = 1 + x2
        if y2 < 0: y2 = 1 + y2
        frame = self.get_frame(grayscale)[int(WINDOW_DIMS[1]*y1):int(WINDOW_DIMS[1]*y2), int(WINDOW_DIMS[0]*x1):int(WINDOW_DIMS[0]*x2)]
        if high_contrast and grayscale: frame[frame < thresh] = 0
        return frame
    
    def save_frame(self, frame, filename="frame.png"):
        cv2.imwrite(filename, frame)
    
    def locate(self, template, frame=None, grayscale=True, thresh=0, ref="cc", return_confidence=False):
        if grayscale: template = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
        h, w = template.shape[:2]
        frame = self.get_frame(grayscale) if frame is None else frame
        res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if DEBUG: print(max_val)
        if max_val > thresh:
            x_loc, y_loc = max_loc
            if ref[0] == 'c': x_loc += w / 2
            elif ref[0] == 'r': x_loc += w
            if ref[1] == 'c': y_loc += h / 2
            elif ref[1] == 'b': y_loc += h
            if return_confidence:
                return x_loc / WINDOW_DIMS[0], y_loc / WINDOW_DIMS[1], max_val
            else:
                return x_loc / WINDOW_DIMS[0], y_loc / WINDOW_DIMS[1]
        if return_confidence:
            return None, None, max_val
        return None, None