import os
import re
import sys
import cv2
import json
import time
import signal
import atexit
import ctypes
import easyocr
import adbutils
import requests
import argparse
import subprocess
import numpy as np
import portalocker
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from rapidfuzz import process, distance
from curl_cffi import requests as curl_requests
from pyminitouch import MNTDevice, CommandBuilder
import configs
from configs import *
from gui import get_gui

if sys.platform == "win32":
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

if getattr(sys, "frozen", False):
    APP_DATA_DIR = Path.home() / ".CoC_Bot"
    APP_DATA_DIR.mkdir(exist_ok=True)
    CACHE_PATH = APP_DATA_DIR / "cache.json"
else:
    CACHE_PATH = Path(__file__).parent / "cache.json"

INSTANCE_ID = None
ADB_ADDRESS, ADB_DEVICE, MINITOUCH_DEVICE = None, None, None
ADB_WINDOW_DIMS = WINDOW_DIMS

def parse_args(debug=None, id=None, gui=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=configs.DEBUG, help="Enable debug mode")
    parser.add_argument("--id", type=str, default=None, help="Instance ID")
    parser.add_argument("--gui", action="store_true", default=configs.LOCAL_GUI, help="Run with GUI")
    args = parser.parse_args()
    configs.DEBUG = args.debug if debug is None else debug
    configs.LOCAL_GUI = args.gui if gui is None else gui
    if id is not None:
        assert id in configs.INSTANCE_IDS, f"Invalid instance ID. Must be one of: {configs.INSTANCE_IDS}"
        args.id = id
    elif args.id is None and not configs.LOCAL_GUI:
        args.id = configs.DEFAULT_INSTANCE_ID
    return args

def init_instance(id):
    global INSTANCE_ID, ADB_ADDRESS
    assert id in configs.INSTANCE_IDS, f"Invalid instance ID. Must be one of: {configs.INSTANCE_IDS}"
    INSTANCE_ID = id
    ADB_ADDRESS = configs.ADB_ADDRESSES[configs.INSTANCE_IDS.index(INSTANCE_ID)]
    if WEB_APP_URL != "":
        requests.post(
            f"{WEB_APP_URL}/instances",
            auth=(WEB_APP_AUTH_USERNAME, WEB_APP_AUTH_PASSWORD),
            json={"id": INSTANCE_ID},
            timeout=(10, 20)
        )

def disable_sleep():
    if sys.platform == "darwin":
        if os.geteuid() == 0:
            subprocess.run(["sudo", "pmset", "-a", "disablesleep", "1"], check=True)
        else:
            sleep_helper = Path(__file__).parent / "sleep_helper.sh"
            subprocess.Popen(["osascript", "-e", f'do shell script "{sleep_helper} {os.getpid()}" with administrator privileges'])
    elif sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

def enable_sleep():
    if sys.platform == "darwin":
        if os.geteuid() == 0:
            subprocess.run(["sudo", "pmset", "-a", "disablesleep", "0"], check=True)
    elif sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

def connect_adb():
    global ADB_DEVICE, MINITOUCH_DEVICE, ADB_WINDOW_DIMS
    if ADB_ABS_DIR != "": os.environ["PATH"] = ADB_ABS_DIR + os.pathsep + os.environ["PATH"]
    subprocess.run(["adb", "start-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    res = adbutils.adb.connect(ADB_ADDRESS)
    if "connected" not in res:
        subprocess.run(["adb", "kill-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        raise Exception("Failed to connect to ADB.")
    device, mt_device = None, None
    try:
        device = adbutils.device(ADB_ADDRESS)
        mt_device = MNTDevice(ADB_ADDRESS)
        Exit_Handler.register(mt_device.stop)
    except:
        subprocess.run(["adb", "kill-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        raise Exception("Failed to get ADB device.")
    ADB_DEVICE, MINITOUCH_DEVICE = device, mt_device
    ADB_WINDOW_DIMS = ADB_DEVICE.window_size(landscape=False)

def running():
    if WEB_APP_URL == "": return True
    try:
        response = requests.get(
            f"{WEB_APP_URL}/{INSTANCE_ID}/running",
            auth=(WEB_APP_AUTH_USERNAME, WEB_APP_AUTH_PASSWORD),
            timeout=(10, 20)
        )
        if response.status_code == 200:
            return response.json().get("running", False)
        return False
    except Exception as e:
        if configs.DEBUG: print("running", e)
        return False

def check_color(color, frame, tol=10):
    assert len(frame.shape) == 3 and frame.shape[2] == 3, "Frame must be a color image"
    diff = np.abs(frame - np.array(color).reshape((1, 1, 3))).sum(2) <= tol
    return np.any(diff)

def get_vocab():
    other_words = [
        "prince",
        "copter",
    ]
    
    data = {}
    existing_vocab = None
    for _ in range(1):
        if CACHE_PATH.exists():
            with portalocker.Lock(CACHE_PATH, "r", timeout=5) as f:
                data = json.load(f)
                if "vocab" in data:
                    existing_vocab = set(data["vocab"]["text"] + other_words)
                    if time.time() - data["vocab"]["last_updated"] > 86400: break
                    return list(existing_vocab)
    
    vocab = set()
    endpoints = [
        "A-I",
        "J-P",
        "Q-Z",
    ]

    for endpoint in endpoints:
        # Bypass bot detection
        res = curl_requests.get(
            f"https://clashofclans.fandom.com/wiki/Glossary/{endpoint}",
            timeout=(10, 20),
            impersonate="chrome",
        )
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "lxml")
            elements = soup.select("h3 span.mw-headline")
            for e in elements:
                words = [s for s in e.text.lower().split(" ") if len(s) > 2]
                vocab = vocab.union(words)
        else:
            if existing_vocab is not None: return existing_vocab
            raise Exception("Failed to update vocabulary")
    
    vocab = vocab.union(other_words)
    text = sorted(list(vocab))
    data["vocab"] = {
        "last_updated": time.time(),
        "text": text,
    }
    
    with portalocker.Lock(CACHE_PATH, "w", timeout=5) as f:
        json.dump(data, f, indent=4)

    return list(vocab)

def spell_check(text, cutoff=70):
    def spell_scorer(a, b, score_cutoff=0):
        lev = distance.Levenshtein.distance(a, b)
        length_penalty = abs(len(a) - len(b)) * 0.5
        score = 100 - 10 * (lev + length_penalty)
        return score if score >= score_cutoff else 0
    
    vocab = get_vocab()
    words = re.split(r"[ _]+", text)
    results = []

    for word in words:
        suggestion = word
        if word not in vocab:
            match = process.extractOne(word, vocab, scorer=spell_scorer, score_cutoff=cutoff)
            if match is not None: suggestion = match[0]
        results.append(suggestion)

    return " ".join(results)

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

def to_int_tuple(*args):
    return tuple(map(int, args))

def get_telegram_chat_id():
    data = {}
    if CACHE_PATH.exists():
        with portalocker.Lock(CACHE_PATH, "r", timeout=5) as f:
            data = json.load(f)
            if "telegram_chat_id" in data: return data["telegram_chat_id"]
    
    res = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
        auth=(WEB_APP_AUTH_USERNAME, WEB_APP_AUTH_PASSWORD),
        timeout=(10, 20)
    )
    if res.status_code == 200:
        res = res.json()
        if res["ok"] and len(res["result"]) > 0:
            chat_id = res["result"][-1]["message"]["chat"]["id"]
            data["telegram_chat_id"] = chat_id
            with portalocker.Lock(CACHE_PATH, "w", timeout=5) as f:
                json.dump(data, f, indent=4)
            return chat_id

    raise Exception("Failed to get Telegram chat ID")

def send_notification(text):
    if WEB_APP_URL != "":
        try:
            requests.post(
                f"{WEB_APP_URL}/{INSTANCE_ID}/notify",
                auth=(WEB_APP_AUTH_USERNAME, WEB_APP_AUTH_PASSWORD),
                json=text,
                timeout=(10, 20)
            )
        except: pass

    if TELEGRAM_BOT_TOKEN != "":
        try:
            telegram_text = f"[{INSTANCE_ID}]\n{text}"
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                auth=(WEB_APP_AUTH_USERNAME, WEB_APP_AUTH_PASSWORD),
                data={"chat_id": get_telegram_chat_id(),"text": telegram_text},
                timeout=(10, 20)
            )
        except: pass

def get_exclusions():
    if WEB_APP_URL != "":
        res = requests.get(
            f"{WEB_APP_URL}/{INSTANCE_ID}/exclude",
            auth=(WEB_APP_AUTH_USERNAME, WEB_APP_AUTH_PASSWORD),
            timeout=(10, 20)
        )
        if res.status_code == 200:
            exclusions = res.json().get("exclusions", [])
            return exclusions
        return []
    elif configs.LOCAL_GUI:
        return get_gui().get_exclusions()

def heros_excluded():
    try:
        return "heros" in get_exclusions()
    except:
        return configs.UPGRADE_HEROS

def home_base_excluded():
    try:
        return "home_base" in get_exclusions()
    except:
        return configs.UPGRADE_HOME_BASE

def builder_base_excluded():
    try:
        return "builder_base" in get_exclusions()
    except:
        return configs.UPGRADE_BUILDER_BASE

def home_lab_excluded():
    try:
        return "home_lab" in get_exclusions()
    except:
        return configs.UPGRADE_HOME_LAB

def builder_lab_excluded():
    try:
        return "builder_lab" in get_exclusions()
    except:
        return configs.UPGRADE_BUILDER_LAB

def home_attacks_excluded():
    try:
        return "home_attacks" in get_exclusions()
    except:
        return not configs.ATTACK_HOME_BASE

def builder_attacks_excluded():
    try:
        return "builder_attacks" in get_exclusions()
    except:
        return not configs.ATTACK_BUILDER_BASE

def to_home_base():
    try:
        get_home_builders(1)
        return
    except:
        pass
    
    Input_Handler.zoom(dir="out")
    for _ in range(3):
        Input_Handler.swipe_up(
            y1=0.5,
            y2=1.0,
        )
    for _ in range(3):
        Input_Handler.swipe_left(
            x1=1.0,
            x2=0.0,
        )
    for scale in np.linspace(0.3, 1.0, 10):
        template = cv2.resize(Asset_Manager.misc_assets["boat_icon"], None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        x, y = Frame_Handler.locate(template, grayscale=True, thresh=0.7, ref="cc")
        if x is None or y is None: continue
    
        Input_Handler.click(x, y)
        time.sleep(2)
        break

def get_home_builders(timeout=60):
    start = time.time()
    while True:
        try:
            section = Frame_Handler.get_frame_section(0.49, 0.04, -0.455, 0.08, high_contrast=True)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/home_builders.png")
            
            slash = cv2.cvtColor(Asset_Manager.upgrader_assets["slash"], cv2.COLOR_RGB2GRAY)
            res = cv2.matchTemplate(section, slash, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val < 0.9: raise Exception("Slash not found")
            
            text = fix_digits(''.join(OCR_Handler.get_text(section)).replace(' ', '').replace('/', ''))
            available = int(text[0])
            return available
        except Exception as e:
            if configs.DEBUG: print("get_home_builders", e)
        time.sleep(0.5)
        if time.time() > start + timeout: break
    raise Exception("Failed to get home builders")

def start_coc(timeout=60):
    try:
        print("Starting CoC...", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))
        i = 0
        start = time.time()
        while time.time() - start < timeout:
            ADB_DEVICE.shell(f"am start {'-S' if i==0 else ''} -W -n com.supercell.clashofclans/com.supercell.titan.GameApp")
            Input_Handler.click_exit(4, 0.1)
            try:
                get_home_builders(1)
                break
            except:
                if not running(): return False
                pass
            
            try:
                get_builder_builders(1)
                break
            except:
                if not running(): return False
                pass
            
            i += 1
            time.sleep(1)
        if time.time() - start > timeout:
            stop_coc()
            raise Exception("Failed to start CoC")
        print("CoC started", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))
        return True
    except:
        return False

def stop_coc():
    print("Stopping CoC...", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))
    ADB_DEVICE.shell("am force-stop com.supercell.clashofclans")
    print("CoC stopped", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))

def to_builder_base():
    try:
        get_builder_builders(1)
        return
    except:
        pass
    
    Input_Handler.zoom(dir="out")
    Input_Handler.swipe_up()
    
    for scale in np.linspace(0.3, 1.0, 10):
        template = cv2.resize(Asset_Manager.misc_assets["boat_icon"], None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        x, y = Frame_Handler.locate(template, grayscale=True, thresh=0.7, ref="cc")
        if x is None or y is None: continue
    
        Input_Handler.click(x, y)
        time.sleep(2)
        break

def get_builder_builders(timeout=60):
    start = time.time()
    while True:
        try:
            section = Frame_Handler.get_frame_section(0.565, 0.04, -0.38, 0.08, high_contrast=True)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/builder_builders.png")
            
            slash = cv2.cvtColor(Asset_Manager.upgrader_assets["slash"], cv2.COLOR_RGB2GRAY)
            res = cv2.matchTemplate(section, slash, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val < 0.9: raise Exception("Slash not found")
            
            text = fix_digits(''.join(OCR_Handler.get_text(section)).replace(' ', '').replace('/', ''))
            available = int(text[0])
            return available
        except Exception as e:
            if configs.DEBUG: print("get_builder_builders", e)
        time.sleep(0.5)
        if time.time() > start + timeout: break
    raise Exception("Failed to get builder builders")

def require_exit(n=5, delay=0.1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = None
            try: result = func(*args, **kwargs)
            finally: Input_Handler.click_exit(n, delay)
            return result
        return wrapper
    return decorator

class OCR_Handler:
    @classmethod
    def get_text(cls, frame, local=True):
        if local:
            if not hasattr(cls, 'reader'):
                cls.reader = easyocr.Reader(['en'], gpu=True)
            result = cls.reader.readtext(frame)
            return [text for _, text, _ in result if text.strip()]
        else:
            w, h = frame.shape[1], frame.shape[0]
            if w < 1024 or h < 1024:
                scale = max(1024 / w, 1024 / h)
                frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
            _, img_encoded = cv2.imencode('.png', frame)
            response = requests.post(
                "https://api.easyocr.org/ocr",
                files={"file": ("image.png", img_encoded.tobytes())},
                timeout=(10, 20)
            )
            result = response.json()['words']
            return [res['text'] for res in result if res['text'].strip()]

class Asset_Manager:
    misc_assets = {}
    upgrader_assets = {}
    attacker_assets = {}
    
    @staticmethod
    def resource_path(rel_path):
        if hasattr(sys, "_MEIPASS"):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent.resolve()
        return base_path / rel_path
    
    @classmethod
    def load_misc_assets(cls):
        assets = {}
        path = cls.resource_path("assets/misc")
        for file in os.listdir(path):
            assets[file.replace('.png', '')] = cv2.imread(path / file, cv2.IMREAD_COLOR)
        cls.misc_assets = assets
    
    @classmethod
    def load_upgrader_assets(cls):
        assets = {}
        path = cls.resource_path("assets/upgrader")
        for file in os.listdir(path):
            assets[file.replace('.png', '')] = cv2.imread(path / file, cv2.IMREAD_COLOR)
        cls.upgrader_assets = assets

    @classmethod
    def load_attacker_assets(cls):
        assets = {}
        path = cls.resource_path("assets/attacker")
        for file in os.listdir(path):
            assets[file.replace('.png', '')] = cv2.imread(path / file, cv2.IMREAD_COLOR)
        cls.attacker_assets = assets

Asset_Manager.load_misc_assets()
Asset_Manager.load_upgrader_assets()
Asset_Manager.load_attacker_assets()

class Input_Handler:
    @classmethod
    def click(cls, x, y, n=1, delay=0):
        if x < 0: x = 1 + x
        if y < 0: y = 1 + y
        command = [f"input tap {int(x*ADB_WINDOW_DIMS[0])} {int(y*ADB_WINDOW_DIMS[1])}"] * n
        if delay == 0:
            command = " && ".join(command) + ";"
            ADB_DEVICE.shell(command)
        else:
            for c in command:
                ADB_DEVICE.shell(c)
                time.sleep(delay)

    @classmethod
    def click_exit(cls, n=1, delay=0):
        cls.click(0.99, 0.99, n, delay=delay)

    @classmethod
    def multi_click(cls, x1, y1, x2, y2, duration=0):
        MAX_X = int(MINITOUCH_DEVICE.connection.max_x)
        MAX_Y = int(MINITOUCH_DEVICE.connection.max_y)
        MINITOUCH_DEVICE.tap([(x1*MAX_X, y1*MAX_Y), (x2*MAX_X, y2*MAX_Y)], duration=duration)

    @classmethod
    def swipe(cls, x1, y1, x2, y2, duration=100, hold_end_time=0):
        if x1 < 0: x1 = 1 + x1
        if y1 < 0: y1 = 1 + y1
        if x2 < 0: x2 = 1 + x2
        if y2 < 0: y2 = 1 + y2
        
        builder = CommandBuilder()
        
        MAX_X = int(MINITOUCH_DEVICE.connection.max_x)
        MAX_Y = int(MINITOUCH_DEVICE.connection.max_y)
        
        x1 = int(x1 * MAX_X)
        y1 = int(y1 * MAX_Y)
        x2 = int(x2 * MAX_X)
        y2 = int(y2 * MAX_Y)
        
        builder.down(0, x1, y1, pressure=100)
        builder.publish(MINITOUCH_DEVICE.connection)
        builder.move(0, x2, y2, pressure=100)
        builder.wait(duration)
        builder.commit()
        builder.publish(MINITOUCH_DEVICE.connection)
        time.sleep(hold_end_time / 1000)
        builder.up(0)
        builder.publish(MINITOUCH_DEVICE.connection)

    @classmethod
    def swipe_up(cls, y1=0.5, y2=0.0, x=1.0, duration=100, hold_end_time=0):
        cls.swipe(x, y1, x, y2, duration=duration, hold_end_time=hold_end_time)

    @classmethod
    def swipe_down(cls, y1=0.5, y2=1.0, x=1.0, duration=100, hold_end_time=0):
        cls.swipe(x, y1, x, y2, duration=duration, hold_end_time=hold_end_time)

    @classmethod
    def swipe_left(cls, x1=0.5, x2=0.0, y=1.0, duration=100, hold_end_time=0):
        cls.swipe(x1, y, x2, y, duration=duration, hold_end_time=hold_end_time)

    @classmethod
    def swipe_right(cls, x1=0.5, x2=1.0, y=1.0, duration=100, hold_end_time=0):
        cls.swipe(x1, y, x2, y, duration=duration, hold_end_time=hold_end_time)

    @classmethod
    def zoom(cls, dir="out"):
        builder = CommandBuilder()
        
        MAX_X = int(MINITOUCH_DEVICE.connection.max_x)
        MAX_Y = int(MINITOUCH_DEVICE.connection.max_y)
        
        left_in = to_int_tuple(0.45*MAX_X, 0.5*MAX_Y)
        left_out = to_int_tuple(0.15*MAX_X, 0.5*MAX_Y)
        right_in = to_int_tuple(0.55*MAX_X, 0.5*MAX_Y)
        right_out = to_int_tuple(0.85*MAX_X, 0.5*MAX_Y)
        
        start = [left_in, right_in] if dir=="in" else [left_out, right_out]
        end = [left_out, right_out] if dir=="in" else [left_in, right_in]
        
        builder.down(0, *start[0], pressure=100)
        builder.down(1, *start[1], pressure=100)
        builder.publish(MINITOUCH_DEVICE.connection)
        builder.move(0, *end[0], pressure=100)
        builder.move(1, *end[1], pressure=100)
        builder.commit()
        builder.publish(MINITOUCH_DEVICE.connection)
        builder.up(0)
        builder.up(1)
        builder.publish(MINITOUCH_DEVICE.connection)

class Frame_Handler:
    @classmethod
    def get_frame(cls, grayscale=True):
        frame = np.array(ADB_DEVICE.screenshot())
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, WINDOW_DIMS, interpolation=cv2.INTER_NEAREST)
        if configs.DEBUG: cls.save_frame(frame, "debug/frame.png")
        if grayscale: frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        return frame

    @classmethod
    def get_frame_section(cls, x1, y1, x2, y2, high_contrast=False, thresh=200, grayscale=True):
        if x1 < 0: x1 = 1 + x1
        if y1 < 0: y1 = 1 + y1
        if x2 < 0: x2 = 1 + x2
        if y2 < 0: y2 = 1 + y2
        frame = cls.get_frame(grayscale)[int(WINDOW_DIMS[1]*y1):int(WINDOW_DIMS[1]*y2), int(WINDOW_DIMS[0]*x1):int(WINDOW_DIMS[0]*x2)]
        if high_contrast and grayscale: frame[frame < thresh] = 0
        return frame

    @classmethod
    def save_frame(cls, frame, filename="frame.png"):
        cv2.imwrite(filename, frame)

    @classmethod
    def screenshot(cls, filename="debug/screenshot.png", grayscale=False):
        frame = cls.get_frame(grayscale)
        cls.save_frame(frame, filename)
    
    @classmethod
    def locate(cls, template, frame=None, grayscale=True, thresh=0, ref="cc", return_confidence=False, return_all=False):
        if grayscale and len(template.shape) == 3:
            template = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
        h, w = template.shape[:2]
        frame = cls.get_frame(grayscale) if frame is None else frame
        fh, fw = frame.shape[:2]
        res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if configs.DEBUG: print(max_val)
        
        if return_all:
            ys, xs = np.where(res >= thresh)
            results = []
            for (x_loc, y_loc, val) in zip(xs, ys, res[ys, xs]):
                if ref[0] == 'c':
                    x_loc += w / 2
                elif ref[0] == 'r':
                    x_loc += w
                if ref[1] == 'c':
                    y_loc += h / 2
                elif ref[1] == 'b':
                    y_loc += h

                if return_confidence:
                    results.append((x_loc / fw, y_loc / fh, float(val)))
                else:
                    results.append((x_loc / fw, y_loc / fh))

            results.sort(key=lambda r: r[-1] if return_confidence else 0, reverse=True)
            return results
        
        if max_val > thresh:
            x_loc, y_loc = max_loc
            if ref[0] == 'c': x_loc += w / 2
            elif ref[0] == 'r': x_loc += w
            if ref[1] == 'c': y_loc += h / 2
            elif ref[1] == 'b': y_loc += h
            if return_confidence:
                return x_loc / fw, y_loc / fh, max_val
            else:
                return x_loc / fw, y_loc / fh
        if return_confidence:
            return None, None, max_val
        return None, None

class Exit_Handler:
    RUN_AT_EXIT = []
    
    @classmethod
    def register(cls, func):
        atexit.register(func)
        cls.RUN_AT_EXIT.append(func)
        return func

    @classmethod
    def handle_sig(cls, sig, frame):
        for func in cls.RUN_AT_EXIT:
            try: func()
            except: pass
        if sig == signal.SIGINT:
            raise KeyboardInterrupt
        sys.exit(0)

    @classmethod
    def setup_signal_handlers(cls):
        signals = [signal.SIGINT, signal.SIGTERM]
        if sys.platform != "win32":
            signals.append(signal.SIGHUP)
        for sig in signals:
            signal.signal(sig, cls.handle_sig)

Exit_Handler.setup_signal_handlers()
