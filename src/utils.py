import sys
from pathlib import Path
from functools import lru_cache
import configs
from configs import *

if sys.platform == "win32":
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

APP_DATA_DIR = Path.home() / ".CoC_Bot"
APP_DATA_DIR.mkdir(exist_ok=True)

if getattr(sys, "frozen", False):
    CACHE_PATH = APP_DATA_DIR / "cache.json"
else:
    CACHE_PATH = Path(__file__).parent / "cache.json"

INSTANCE_ID = None
ADB_ADDRESS, ADB_DEVICE, MINITOUCH_DEVICE = None, None, None
ADB_WINDOW_DIMS = WINDOW_DIMS

def parse_args(debug=None, id=None, gui=None):
    import argparse
    
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
    import requests
    
    assert id in configs.INSTANCE_IDS, f"Invalid instance ID. Must be one of: {configs.INSTANCE_IDS}"
    INSTANCE_ID = id
    ADB_ADDRESS = configs.ADB_ADDRESSES[configs.INSTANCE_IDS.index(INSTANCE_ID)]
    if WEB_APP_URL != "":
        if "pythonanywhere.com" in WEB_APP_URL:
            Scheduler.add_job(extend_pythonanywhere_hosting, args=(configs.PA_USERNAME, configs.PA_PASSWORD), trigger="interval", hours=24)
        
        requests.post(
            f"{WEB_APP_URL}/instances",
            json={"id": INSTANCE_ID},
            timeout=(10, 20)
        )

def disable_sleep():
    import sys, subprocess, ctypes, os, shutil
    
    if sys.platform == "darwin":
        sleep_helper_temp = Path(__file__).parent / "sleep_helper.sh"
        sleep_helper_permanent = APP_DATA_DIR / "sleep_helper.sh"
        shutil.copyfile(sleep_helper_temp, sleep_helper_permanent)
        os.chmod(sleep_helper_permanent, 0o755)
        subprocess.Popen(["osascript", "-e", f'do shell script "{sleep_helper_permanent} {os.getpid()}" with administrator privileges'])
    elif sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

def enable_sleep():
    import sys, ctypes
    
    if sys.platform == "darwin":
        pass
    elif sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

def to_system_home():
    ADB_DEVICE.shell("input keyevent KEYCODE_HOME")

def connect_adb():
    global ADB_DEVICE, MINITOUCH_DEVICE, ADB_WINDOW_DIMS
    import subprocess, adbutils, os
    from pyminitouch import MNTDevice
    
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
    except KeyboardInterrupt: raise
    except SystemExit: raise
    except:
        subprocess.run(["adb", "kill-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        raise Exception("Failed to get ADB device.")
    ADB_DEVICE, MINITOUCH_DEVICE = device, mt_device
    ADB_WINDOW_DIMS = ADB_DEVICE.window_size(landscape=False)

def running():
    import requests
    
    if WEB_APP_URL == "": return True
    try:
        response = requests.get(
            f"{WEB_APP_URL}/{INSTANCE_ID}/running",
            timeout=(10, 20)
        )
        if response.status_code == 200:
            return response.json().get("running", False)
        return False
    except Exception as e:
        if configs.DEBUG: print("running", e)
        return False

def check_color(color, frame, tol=10):
    import numpy as np
    assert len(frame.shape) == 3 and frame.shape[2] == 3, "Frame must be a color image"
    diff = np.abs(frame - np.array(color).reshape((1, 1, 3))).sum(2) <= tol
    return np.any(diff)

def get_vocab():
    import json, time, portalocker
    from bs4 import BeautifulSoup
    from curl_cffi import requests as curl_requests
    
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
    import re
    from rapidfuzz import process, distance
    
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
    import re
    if type(text) is list:
        return [parse_time(t) for t in text]
    try:
        text = text.lower().replace(' ', '').replace('-', '')
        units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
        pattern = re.compile(r"(\d+)([dhms])")
        seconds = sum(int(v) * units[u] for v, u in pattern.findall(text))
        return seconds
    except KeyboardInterrupt: raise
    except SystemExit: raise
    except:
        return 0

def to_int_array(*args):
    import numpy as np
    return np.array(list(map(int, args)))

def render_text(text, font, font_size, color=(255, 255, 255)):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    
    @lru_cache(maxsize=32)
    def get_font(font, font_size):
        font_path = Asset_Manager.fonts.get(font)
        return ImageFont.truetype(font_path, font_size)
    
    font = get_font(font, font_size)
    temp = Image.new("RGB", (1, 1))
    bbox = ImageDraw.Draw(temp).textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    render = Image.new("RGB", (w, h), (0, 0, 0))
    ImageDraw.Draw(render).text((-bbox[0], -bbox[1]), text, font=font, fill=color)
    render = np.array(render)
    return render

def get_telegram_chat_id():
    import portalocker, requests, json
    
    data = {}
    if CACHE_PATH.exists():
        with portalocker.Lock(CACHE_PATH, "r", timeout=5) as f:
            data = json.load(f)
            if "telegram_chat_id" in data: return data["telegram_chat_id"]
    
    res = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
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
    import requests
    
    if WEB_APP_URL != "":
        try:
            requests.post(
                f"{WEB_APP_URL}/{INSTANCE_ID}/notify",
                json=text,
                timeout=(10, 20)
            )
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except: pass

    if TELEGRAM_BOT_TOKEN != "":
        try:
            telegram_text = f"[{INSTANCE_ID}]\n{text}"
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": get_telegram_chat_id(),"text": telegram_text},
                timeout=(10, 20)
            )
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except: pass

def extend_pythonanywhere_hosting(username, password):
    import requests
    
    assert "pythonanywhere.com" in WEB_APP_URL
    base_url = "https://www.pythonanywhere.com"
    login_url = f"{base_url}/login/"
    webapps_url = f"{base_url}/user/{username}/webapps/"
    extend_url = f"{base_url}/user/{username}/webapps/{username}.pythonanywhere.com/extend"
    
    headers = {"Referer": base_url}

    session = requests.Session()
    
    # Login
    session.get(login_url)
    session.post(
        login_url,
        data={
            "csrfmiddlewaretoken": session.cookies.get_dict().get("csrftoken"),
            "auth-username": username,
            "auth-password": password,
            "login_view-current_step": "auth",
        },
        headers=headers,
    )
    assert "Log out" in session.get(base_url).text
    
    # Extend hosting
    session.get(webapps_url)
    res = session.post(
        extend_url,
        headers=headers,
        data={"csrfmiddlewaretoken": session.cookies.get_dict().get("csrftoken")},
    )
    assert res.url == webapps_url

def to_home_base():
    import cv2, time, numpy as np
    
    try:
        get_home_builders(1)
        return
    except KeyboardInterrupt: raise
    except SystemExit: raise
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
    
    scale_templates = []
    for scale in np.arange(0.43, 0.47, 0.01):
        template = cv2.resize(Asset_Manager.misc_assets["boat_icon"], None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        scale_templates.append(template)
    
    for _ in range(5):
        xys = Frame_Handler.batch_locate(scale_templates, grayscale=True, thresh=0.7, ref="cc")
        for x, y in xys:
            if x is None or y is None: continue
            Input_Handler.click(x, y)
            time.sleep(2)
            return

def get_home_builders(timeout=60, return_amount=True, raise_exception=True):
    import time, cv2
    
    start = time.time()
    while True:
        try:
            section = Frame_Handler.get_frame_section(0.49, 0.04, -0.455, 0.08, high_contrast=True)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/home_builders.png")
            
            slash = cv2.cvtColor(Asset_Manager.upgrader_assets["slash"], cv2.COLOR_RGB2GRAY)
            res = cv2.matchTemplate(section, slash, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if raise_exception and max_val < 0.9: raise Exception("Slash not found")
            
            if not return_amount: return max_val >= 0.9
            
            text = fix_digits(''.join(OCR_Handler.get_text(section)).replace(' ', '').replace('/', ''))
            available = int(text[0])
            return available
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except Exception as e:
            if configs.DEBUG: print("get_home_builders", e)
        time.sleep(0.5)
        if time.time() > start + timeout: break
    raise Exception("Failed to get home builders")

def start_coc(timeout=60):
    import time
    from datetime import datetime
    
    try:
        if not running(): return False
        to_system_home()
        print("Starting CoC...", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))
        i = 0
        start = time.time()
        while time.time() - start < timeout:
            if not running(): return False
            ADB_DEVICE.shell(f"am start {'-S' if i==0 else ''} -W -n com.supercell.clashofclans/com.supercell.titan.GameApp")
            Input_Handler.click_exit(4, 0.1)
            
            try:
                get_home_builders(1, return_amount=False)
                break
            except KeyboardInterrupt: raise
            except SystemExit: raise
            except:
                pass
            
            try:
                get_builder_builders(1, return_amount=False)
                break
            except KeyboardInterrupt: raise
            except SystemExit: raise
            except:
                pass
            
            i += 1
            time.sleep(1)
        if time.time() - start > timeout:
            stop_coc()
            update_coc()
            raise Exception("Failed to start CoC")
        print("CoC started", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))
        return True
    except KeyboardInterrupt: raise
    except SystemExit: raise
    except:
        return False

def stop_coc():
    from datetime import datetime
    print("Stopping CoC...", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))
    ADB_DEVICE.shell("am force-stop com.supercell.clashofclans")
    to_system_home()
    print("CoC stopped", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))

def update_coc(timeout=10):
    import uiautomator2 as u2
    ADB_DEVICE.shell('am start -a android.intent.action.VIEW -d "market://details?id=com.supercell.clashofclans"')
    try:
        u2.connect(ADB_ADDRESS)(text="Play").click(timeout=timeout)
        for _ in range(3): u2.connect(ADB_ADDRESS)(text="Play").click(timeout=0)
    except:
        pass
    to_system_home()

def to_builder_base():
    import cv2, time, numpy as np
    
    try:
        get_builder_builders(1)
        return
    except KeyboardInterrupt: raise
    except SystemExit: raise
    except:
        pass
    
    for _ in range(3):
        Input_Handler.zoom(dir="in")
    for _ in range(2):
        Input_Handler.zoom(dir="out", percent=0.75)
    for _ in range(3):
        Input_Handler.swipe_right()
        Input_Handler.swipe_up()
    
    scale_templates = []
    for scale in np.arange(0.43, 0.47, 0.01):
        template = cv2.resize(Asset_Manager.misc_assets["boat_icon"], None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        scale_templates.append(template)
    
    for _ in range(5):
        xys = Frame_Handler.batch_locate(scale_templates, grayscale=True, thresh=0.7, ref="cc")
        for x, y in xys:
            if x is None or y is None: continue
            Input_Handler.click(x, y)
            time.sleep(2)
            return
        Input_Handler.swipe(x1=0.5, y1=0.5, x2=0.25, y2=0.75, hold_end_time=100)

def get_builder_builders(timeout=60, return_amount=True, raise_exception=True):
    import time, cv2
    
    start = time.time()
    while True:
        try:
            section = Frame_Handler.get_frame_section(0.565, 0.04, -0.38, 0.08, high_contrast=True)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/builder_builders.png")
            
            slash = cv2.cvtColor(Asset_Manager.upgrader_assets["slash"], cv2.COLOR_RGB2GRAY)
            res = cv2.matchTemplate(section, slash, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if raise_exception and max_val < 0.9: raise Exception("Slash not found")
            
            if not return_amount: return max_val >= 0.9
            
            text = fix_digits(''.join(OCR_Handler.get_text(section)).replace(' ', '').replace('/', ''))
            available = int(text[0])
            return available
        except KeyboardInterrupt: raise
        except SystemExit: raise
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

class Exit_Handler:
    RUN_AT_EXIT = []
    
    @classmethod
    def register(cls, func):
        import atexit
        atexit.register(func)
        cls.RUN_AT_EXIT.append(func)
        return func

    @classmethod
    def handle_sig(cls, sig, frame):
        import signal
        for func in cls.RUN_AT_EXIT:
            try: func()
            except: pass
        if sig == signal.SIGINT:
            raise KeyboardInterrupt
        sys.exit(0)

    @classmethod
    def setup_signal_handlers(cls):
        import signal
        signals = [signal.SIGINT, signal.SIGTERM]
        if sys.platform != "win32":
            signals.append(signal.SIGHUP)
        for sig in signals:
            signal.signal(sig, cls.handle_sig)

Exit_Handler.setup_signal_handlers()

class Task_Handler:
    
    cached_exclusions = []
    
    @classmethod
    def get_exclusions(cls, use_cached=False):
        import requests
        from gui import get_gui
        
        if use_cached:
            return cls.cached_exclusions
        if WEB_APP_URL != "":
            res = requests.get(
                f"{WEB_APP_URL}/{INSTANCE_ID}/exclude",
                timeout=(10, 20)
            )
            if res.status_code == 200:
                cls.cached_exclusions = res.json().get("exclusions", [])
        elif configs.LOCAL_GUI:
            res = requests.get(
                f"http://localhost:{get_gui().server_port}/exclude",
                timeout=(10, 20)
            )
            if res.status_code == 200:
                cls.cached_exclusions = res.json().get("exclusions", [])
        return cls.cached_exclusions

    @classmethod
    def home_base_priority_excluded(cls, **kwargs):
        try:
            return "home_base_priority" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.PRIORITY_HOME_BASE_UPGRADES

    @classmethod
    def home_lab_priority_excluded(cls, **kwargs):
        try:
            return "home_lab_priority" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.PRIORITY_HOME_LAB_UPGRADES
    
    @classmethod
    def builder_base_priority_excluded(cls, **kwargs):
        try:
            return "builder_base_priority" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.PRIORITY_BUILDER_BASE_UPGRADES
    
    @classmethod
    def builder_lab_priority_excluded(cls, **kwargs):
        try:
            return "builder_lab_priority" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.PRIORITY_BUILDER_LAB_UPGRADES

    @classmethod
    def heroes_excluded(cls, **kwargs):
        try:
            return "heroes" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.UPGRADE_HEROES

    @classmethod
    def home_base_excluded(cls, **kwargs):
        try:
            return "home_base" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.UPGRADE_HOME_BASE

    @classmethod
    def builder_base_excluded(cls, **kwargs):
        try:
            return "builder_base" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.UPGRADE_BUILDER_BASE

    @classmethod
    def home_lab_excluded(cls, **kwargs):
        try:
            return "home_lab" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.UPGRADE_HOME_LAB

    @classmethod
    def builder_lab_excluded(cls, **kwargs):
        try:
            return "builder_lab" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.UPGRADE_BUILDER_LAB

    @classmethod
    def home_attacks_excluded(cls, **kwargs):
        try:
            return "home_attacks" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.ATTACK_HOME_BASE

    @classmethod
    def builder_attacks_excluded(cls, **kwargs):
        try:
            return "builder_attacks" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.ATTACK_BUILDER_BASE

    @classmethod
    def lab_assistant_excluded(cls, **kwargs):
        try:
            return "lab_assistant" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.ASSIGN_LAB_ASSISTANT

    @classmethod
    def builder_apprentice_excluded(cls, **kwargs):
        try:
            return "builder_apprentice" in cls.get_exclusions(**kwargs)
        except KeyboardInterrupt: raise
        except SystemExit: raise
        except:
            return not configs.ASSIGN_BUILDER_APPRENTICE

class OCR_Handler:
    
    backoff_time = 0
    
    @classmethod
    def get_text(cls, frame):
        import time
        if configs.GROQ_API_KEY != "":
            if time.time() > cls.backoff_time:
                try: return cls.external_ocr(frame)
                except: cls.backoff_time = time.time() + 600
        return cls.local_ocr(frame)

    @classmethod
    def local_ocr(cls, frame):
        if not hasattr(cls, 'reader'):
            import easyocr
            cls.reader = easyocr.Reader(['en'], gpu=True)
        result = cls.reader.readtext(frame)
        return [text for _, text, _ in result if text.strip()]

    @classmethod
    def external_ocr(cls, frame):
        import cv2, base64
        from groq import Groq
        
        base64_img = base64.b64encode(cv2.imencode(".jpg", frame)[1]).decode("utf-8")
        client = Groq(api_key=configs.GROQ_API_KEY, timeout=10, max_retries=0)
        chat_completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "what text is in this image? respond ONLY with the text. if there is no text respond with ~"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpg;base64,{base64_img}",
                            },
                        },
                    ],
                }
            ],
        )
        return chat_completion.choices[0].message.content.replace('~', '').splitlines()

class Asset_Manager:
    fonts = {}
    misc_assets = {}
    upgrader_assets = {}
    attacker_assets = {}
    
    @staticmethod
    def resource_path(rel_path):
        import sys
        from pathlib import Path
        if hasattr(sys, "_MEIPASS"):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent.resolve()
        return base_path / rel_path
    
    @classmethod
    def load_fonts(cls):
        import os
        cls.fonts = {}
        path = cls.resource_path("assets/fonts")
        for file in os.listdir(path):
            cls.fonts[file.replace('.ttf', '')] = str(path / file)

    @classmethod
    def load_misc_assets(cls):
        import os, cv2
        assets = {}
        path = cls.resource_path("assets/misc")
        for file in os.listdir(path):
            if not file.endswith('.png'): continue
            assets[file.replace('.png', '')] = cv2.cvtColor(cv2.imread(path / file, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        cls.misc_assets = assets
    
    @classmethod
    def load_upgrader_assets(cls):
        import os, cv2
        assets = {}
        path = cls.resource_path("assets/upgrader")
        for file in os.listdir(path):
            if not file.endswith('.png'): continue
            assets[file.replace('.png', '')] = cv2.cvtColor(cv2.imread(path / file, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        cls.upgrader_assets = assets

    @classmethod
    def load_attacker_assets(cls):
        import os, cv2
        assets = {}
        path = cls.resource_path("assets/attacker")
        for file in os.listdir(path):
            if not file.endswith('.png'): continue
            assets[file.replace('.png', '')] = cv2.cvtColor(cv2.imread(path / file, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        cls.attacker_assets = assets

Asset_Manager.load_misc_assets()
Asset_Manager.load_upgrader_assets()
Asset_Manager.load_attacker_assets()
Asset_Manager.load_fonts()

class Input_Handler:
    @classmethod
    def down(cls, x, y, pointer=0):
        from pyminitouch import CommandBuilder
        if x < 0: x = 1 + x
        if y < 0: y = 1 + y
        MAX_X = int(MINITOUCH_DEVICE.connection.max_x)
        MAX_Y = int(MINITOUCH_DEVICE.connection.max_y)
        x = int(x * MAX_X)
        y = int(y * MAX_Y)
        builder = CommandBuilder()
        builder.down(pointer, x, y, 100)
        builder.publish(MINITOUCH_DEVICE.connection)

    @classmethod
    def up(cls, pointer=0):
        from pyminitouch import CommandBuilder
        builder = CommandBuilder()
        builder.up(pointer)
        builder.publish(MINITOUCH_DEVICE.connection)

    @classmethod
    def click(cls, x, y, n=1, delay=0, pointer=0):
        import time
        from pyminitouch import CommandBuilder
        if x < 0: x = 1 + x
        if y < 0: y = 1 + y
        MAX_X = int(MINITOUCH_DEVICE.connection.max_x)
        MAX_Y = int(MINITOUCH_DEVICE.connection.max_y)
        x = int(x * MAX_X)
        y = int(y * MAX_Y)
        builder = CommandBuilder()
        for _ in range(n):
            builder.down(pointer, x, y, 100)
            builder.commit()
            builder.up(pointer)
            builder.publish(MINITOUCH_DEVICE.connection)
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
    def swipe(cls, x1, y1, x2, y2, duration=100, hold_end_time=0, inter_points=0, pointer=0):
        import time, numpy as np
        from pyminitouch import CommandBuilder
        
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
        
        x_points = np.linspace(x1, x2, inter_points + 2, dtype=int)
        y_points = np.linspace(y1, y2, inter_points + 2, dtype=int)
        dt = duration / (inter_points + 1)
        
        builder.down(pointer, x1, y1, pressure=100)
        builder.publish(MINITOUCH_DEVICE.connection)
        for x, y in zip(x_points, y_points):
            builder.move(pointer, x, y, pressure=100)
            builder.publish(MINITOUCH_DEVICE.connection)
            if dt > 0: time.sleep(dt / 1000)
        if hold_end_time > 0: time.sleep(hold_end_time / 1000)
        builder.up(pointer)
        builder.publish(MINITOUCH_DEVICE.connection)

    @classmethod
    def swipe_up(cls, y1=0.5, y2=0.0, x=1.0, **kwargs):
        cls.swipe(x, y1, x, y2, **kwargs)

    @classmethod
    def swipe_down(cls, y1=0.5, y2=1.0, x=1.0, **kwargs):
        cls.swipe(x, y1, x, y2, **kwargs)

    @classmethod
    def swipe_left(cls, x1=0.5, x2=0.0, y=1.0, **kwargs):
        cls.swipe(x1, y, x2, y, **kwargs)

    @classmethod
    def swipe_right(cls, x1=0.5, x2=1.0, y=1.0, **kwargs):
        cls.swipe(x1, y, x2, y, **kwargs)

    @classmethod
    def zoom(cls, dir="out", percent=1.0):
        from pyminitouch import CommandBuilder
        
        builder = CommandBuilder()
        
        MAX_X = int(MINITOUCH_DEVICE.connection.max_x)
        MAX_Y = int(MINITOUCH_DEVICE.connection.max_y)
        
        left_in = to_int_array((0.15 + 0.30*percent)*MAX_X, 0.5*MAX_Y)
        left_out = to_int_array(0.15*MAX_X, 0.5*MAX_Y)
        right_in = to_int_array((0.85 - 0.30*percent)*MAX_X, 0.5*MAX_Y)
        right_out = to_int_array(0.85*MAX_X, 0.5*MAX_Y)
        
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
    pool = None
    
    @classmethod
    def grayscale(cls, frame):
        import cv2
        if len(frame.shape) == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        return frame
    
    @classmethod
    def high_contrast(cls, frame, thresh=200):
        frame = cls.grayscale(frame)
        frame[frame < thresh] = 0
        return frame
    
    @classmethod
    def crop(cls, frame, x1, y1, x2, y2):
        if x1 < 0: x1 = 1 + x1
        if y1 < 0: y1 = 1 + y1
        if x2 < 0: x2 = 1 + x2
        if y2 < 0: y2 = 1 + y2
        h, w = frame.shape[:2]
        return frame[int(h*y1):int(h*y2), int(w*x1):int(w*x2)]
    
    @classmethod
    def get_frame(cls, grayscale=True, high_contrast=False, thresh=200):
        import cv2, numpy as np
        frame = np.array(ADB_DEVICE.screenshot())
        frame = cv2.resize(frame, WINDOW_DIMS, interpolation=cv2.INTER_NEAREST)
        if configs.DEBUG: cls.save_frame(frame, "debug/frame.png")
        if high_contrast: frame = cls.high_contrast(frame, thresh)
        elif grayscale: frame = cls.grayscale(frame)
        return frame

    @classmethod
    def get_frame_section(cls, x1, y1, x2, y2, high_contrast=False, thresh=200, grayscale=True):
        frame = cls.get_frame(grayscale=grayscale, high_contrast=high_contrast, thresh=thresh)
        frame = cls.crop(frame, x1, y1, x2, y2)
        return frame

    @classmethod
    def save_frame(cls, frame, filename="frame.png"):
        import cv2
        cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    @classmethod
    def screenshot(cls, filename="debug/screenshot.png", grayscale=False):
        frame = cls.get_frame(grayscale=grayscale)
        cls.save_frame(frame, filename)
    
    @classmethod
    def locate(cls, template, frame=None, grayscale=True, thresh=0, ref="cc", null_val=None, return_confidence=False, return_all=False):
        import cv2, numpy as np
        
        if grayscale: template = cls.grayscale(template)
        h, w = template.shape[:2]
        frame = cls.get_frame(grayscale=grayscale) if frame is None else frame
        fh, fw = frame.shape[:2]
                
        if h > fh or w > fw:
            if return_all:
                return []
            if return_confidence:
                return null_val, null_val, 0
            return null_val, null_val

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
            return null_val, null_val, max_val
        return null_val, null_val

    @classmethod
    def batch_locate(cls, templates, frame=None, grayscale=True, thresh=0, ref="cc", null_val=None, return_confidence=False, return_all=False):
        from concurrent.futures import ThreadPoolExecutor
        
        if cls.pool is None:
            cls.pool = ThreadPoolExecutor()
            Exit_Handler.register(cls.pool.shutdown)
        
        frame = cls.get_frame(grayscale=grayscale) if frame is None else frame
        
        threads = []
        for template in templates:
            threads.append(cls.pool.submit(cls.locate, template, frame, grayscale, thresh, ref, null_val, return_confidence, return_all))
        return [thread.result() for thread in threads]

class Scheduler:
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.start()
    Exit_Handler.register(scheduler.shutdown)
    
    add_job = scheduler.add_job

class Dev_Tools:
    @classmethod
    def optimal_template_font_size(cls, frame, text, font, font_size_range=(1, 100), color=(255, 255, 255), return_results=False, plot_results=False):
        import numpy as np, matplotlib.pyplot as plt
        templates = [render_text(text, font, size, color) for size in range(font_size_range[0], font_size_range[1] + 1)]
        results = Frame_Handler.batch_locate(templates, frame=frame, grayscale=True, return_confidence=True)
        confidences = [res[2] for res in results]
        optimal_size = confidences.index(max(confidences)) + font_size_range[0]
        
        if plot_results:
            plt.plot(np.arange(font_size_range[0], font_size_range[1] + 1), confidences)
            plt.xlabel("Font Size")
            plt.ylabel("Confidence")
            plt.title(f"Optimal Font Size: {optimal_size}")
            plt.show()
        
        if return_results:
            return optimal_size, results
        return optimal_size
