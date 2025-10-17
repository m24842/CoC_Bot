import re
import sys
import cv2
import ctypes
import smtplib
import requests
import subprocess
import numpy as np
from email.mime.text import MIMEText
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
    return [text for _, text, _ in result]

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

def click(device, x, y, n=1):
    if x < 0: x = 1 + x
    if y < 0: y = 1 + y
    command = [f"input tap {int(x*WINDOW_DIMS[0])} {int(y*WINDOW_DIMS[1])}"] * n
    command = " && ".join(command) + ";"
    device.shell(command)

def swipe(device, x1, y1, x2, y2, duration=100):
    if x1 < 0: x1 = 1 + x1
    if y1 < 0: y1 = 1 + y1
    if x2 < 0: x2 = 1 + x2
    if y2 < 0: y2 = 1 + y2
    command = f"input swipe {int(x1*WINDOW_DIMS[0])} {int(y1*WINDOW_DIMS[1])} {int(x2*WINDOW_DIMS[0])} {int(y2*WINDOW_DIMS[1])} {duration};"
    device.shell(command)

def send_notification(text):
    if WEB_APP_IP != "":
        try: requests.post(f"http://{WEB_APP_IP}:1234/notify", json=text)
        except: pass

    if PHONE_NUMBER != "" and EMAIL_ADDRESS != "" and APP_PASSWORD != "":
        msg = MIMEText(text)
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = f"{PHONE_NUMBER}@vtext.com"
        msg["Subject"] = ""

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, APP_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, msg["To"], msg.as_string())

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
    
    def locate(self, template, frame=None, grayscale=True, thresh=0):
        if grayscale: template = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
        h, w = template.shape[:2]
        frame = self.get_frame(grayscale) if frame is None else frame
        res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if DEBUG: print(max_val)
        if max_val > thresh:
            return (max_loc[0] + w/2) / WINDOW_DIMS[0], (max_loc[1] + h/2) / WINDOW_DIMS[1]
        return None, None