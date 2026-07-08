import sys, collections
from pathlib import Path
from functools import lru_cache
try:
    import configs
    from configs import *
except:
    import configs_build as configs
    from configs_build import *

if sys.platform == "win32":
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

APP_DATA_DIR = Path.home() / ".CoC_Bot"
APP_DATA_DIR.mkdir(exist_ok=True)

if getattr(sys, "frozen", False):
    CACHE_PATH = APP_DATA_DIR / "cache.json"
else:
    CACHE_PATH = Path(__file__).parent / "cache.json"

INSTANCE_ID, ADB_ADDRESS, BLUESTACKS_PID = [None] * 3
TEMP_CACHE = {}

def parse_args(debug=None, id=None, gui=None, gui_port=None):
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=configs.DEBUG, help="Enable debug mode")
    parser.add_argument("--id", type=str, default=None, help="Instance ID")
    parser.add_argument("--gui", action="store_true", default=configs.LOCAL_GUI, help="Run with GUI")
    parser.add_argument("--gui-port", type=int, default=None, help="GUI port")
    args = parser.parse_args()
    configs.DEBUG = args.debug if debug is None else debug
    configs.LOCAL_GUI = args.gui if gui is None else gui
    TEMP_CACHE["gui_port"] = args.gui_port if gui_port is None else gui_port
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
    ADB_ADDRESS = configs.ADB_ADDRESSES[configs.INSTANCE_IDS.index(id)]
    if WEB_APP_URL != "":
        if "pythonanywhere.com" in WEB_APP_URL:
            Scheduler.add_job(extend_pythonanywhere_hosting, args=(configs.PA_USERNAME, configs.PA_PASSWORD), trigger="interval", hours=24)
            Scheduler.add_job(get_vocab, trigger="interval", hours=24)
        
        try:
            requests.post(
                f"{WEB_APP_URL}/instances",
                json={"id": id},
                timeout=(10, 20)
            )
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("init_instance", e)

def disable_sleep():
    import sys, subprocess, ctypes, os, shutil
    
    if sys.platform == "darwin":
        sleep_helper_temp = Path(__file__).parent / "sleep_helper.sh"
        sleep_helper_permanent = APP_DATA_DIR / "sleep_helper.sh"
        shutil.copyfile(sleep_helper_temp, sleep_helper_permanent)
        os.chmod(sleep_helper_permanent, 0o755)
        cmd = f'do shell script "{sleep_helper_permanent} {os.getpid()}" with administrator privileges'
        subprocess.Popen(
            ["osascript", "-e", cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
    elif sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    else:
        raise Exception("Unsupported OS")
    Exit_Handler.register(enable_sleep)

def enable_sleep():
    import sys, ctypes
    
    if sys.platform == "darwin":
        pass
    elif sys.platform == "win32":
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    else:
        raise Exception("Unsupported OS")

def to_system_home():
    ADB_Manager.adbutils_device.shell("input keyevent KEYCODE_HOME")

def file_search(root, target_name, keywords=[]):
    if (cached_path := Cache_Manager.get("file_search", {}).get(target_name, None)) is not None:
        return cached_path
    
    keywords = [kw.lower() for kw in keywords]
    root = Path(root).resolve()
    queue = collections.deque([root])
    visited = set([root.resolve()])
    while queue:
        current_dir = queue.popleft()
        
        try:
            for entries in current_dir.iterdir():
                if entries.is_file() and entries.name == target_name:
                    file_path = str(entries.resolve())
                    Cache_Manager.setdefault("file_search", {})[target_name] = file_path
                    return file_path
                
                if entries.is_dir():
                    real_path = entries.resolve()
                    if real_path not in visited:
                        visited.add(real_path)
                        if any(kw in entries.name.lower() for kw in keywords):
                            queue.appendleft(entries)
                        else:
                            queue.append(entries)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            continue
    return None

def running():
    import requests
    
    if WEB_APP_URL == "": return True
    try:
        response = requests.get(
            f"{WEB_APP_URL}/{INSTANCE_ID}/running",
            timeout=(1, 2)
        )
        if response.status_code == 200:
            return response.json().get("running", False)
        return False
    except Exception as e:
        if configs.DEBUG: print("running", e)
        return False

def click_with_timeout(locator_func, timeout=1, interval=0.1):
    import time
    x, y = locator_func()
    start = time.time()
    while (x is None or y is None) and time.time() - start < timeout:
        time.sleep(interval)
        x, y = locator_func()
    if x is not None and y is not None:
        Input_Handler.click(x, y)
        return True
    return False

def check_color(color, frame, tol=10):
    import numpy as np
    assert len(frame.shape) == 3 and frame.shape[2] == 3, "Frame must be a color image"
    diff = np.abs(frame - np.array(color).reshape((1, 1, 3))).sum(2) <= tol
    return np.any(diff)

def filter_color(color, frame, tol=10, return_mask=False):
    import numpy as np
    assert len(frame.shape) == 3 and frame.shape[2] == 3, "Frame must be a color image"
    mask = np.abs(frame - np.array(color).reshape((1, 1, 3))).sum(2) <= tol
    frame_filtered = frame.copy()
    frame_filtered[~mask] = [0, 0, 0]
    if return_mask:
        return frame_filtered, mask
    return frame_filtered

def get_vocab():
    from bs4 import BeautifulSoup
    from curl_cffi import requests as curl_requests
    
    vocab = set()
    
    other_words = [
        "prince",
        "copter",
    ]

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
            raise Exception("Failed to update vocabulary")
    
    vocab = vocab.union(other_words)
    text = sorted(list(vocab))
    Cache_Manager["vocab"] = text
    
    return list(vocab)

def spell_check(text, cutoff=70):
    import re
    from rapidfuzz import process, distance
    
    def spell_scorer(a, b, score_cutoff=0):
        lev = distance.Levenshtein.distance(a, b)
        length_penalty = abs(len(a) - len(b)) * 0.5
        score = 100 - 10 * (lev + length_penalty)
        return score if score >= score_cutoff else 0
    
    vocab = Cache_Manager.get("vocab", get_vocab())
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
    except (KeyboardInterrupt, SystemExit): raise
    except: return 0

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
    import requests
    
    telegram_chat_id = Cache_Manager.get("telegram_chat_id", None)
    if telegram_chat_id is not None:
        return telegram_chat_id

    res = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
        timeout=(10, 20)
    )
    if res.status_code == 200:
        res = res.json()
        if res["ok"] and len(res["result"]) > 0:
            chat_id = res["result"][-1]["message"]["chat"]["id"]
            Cache_Manager["telegram_chat_id"] = chat_id
            return chat_id

    raise Exception("Failed to get Telegram chat ID. Please send a message to your bot first.")

def send_notification(text):
    import requests
    
    if WEB_APP_URL != "":
        try:
            requests.post(
                f"{WEB_APP_URL}/{INSTANCE_ID}/notify",
                json=text,
                timeout=(1, 2)
            )
        except (KeyboardInterrupt, SystemExit): raise
        except: pass

    if TELEGRAM_BOT_TOKEN != "":
        try:
            telegram_text = f"[{INSTANCE_ID}]\n{text}"
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": get_telegram_chat_id(),"text": telegram_text},
                timeout=(1, 2)
            )
        except (KeyboardInterrupt, SystemExit): raise
        except: pass

def update_status(status):
    import requests
    
    if WEB_APP_URL != "":
        try:
            requests.post(
                f"{WEB_APP_URL}/{INSTANCE_ID}/status",
                json={"status": status},
                timeout=(1, 2)
            )
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("update_status", e)
    if (gui_port := TEMP_CACHE.get("gui_port")) is not None:
        try:
            requests.post(
                f"http://localhost:{gui_port}/{INSTANCE_ID}/status",
                json={"status": status},
                timeout=(1, 2)
            )
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("update_status", e)

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

def to_home_base(ref_cache=False):
    import cv2, time, numpy as np
    
    if ref_cache and TEMP_CACHE.get("location") == "home_base": return
    
    TEMP_CACHE["location"] = "home_base"
    
    try:
        get_home_builders(0, return_amount=False)
        return
    except (KeyboardInterrupt, SystemExit): raise
    except: pass
    
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

def get_home_builders(timeout=60, return_amount=True, raise_exception=True, use_cached_frame=False):
    import time, cv2
    
    start = time.time()
    while True:
        try:
            section = Frame_Handler.get_frame_section(0.49, 0.04, -0.455, 0.08, high_contrast=True, use_cached=use_cached_frame)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/home_builders.png")
            
            slash = cv2.cvtColor(Asset_Manager.misc_assets["slash"], cv2.COLOR_RGB2GRAY)
            res = cv2.matchTemplate(section, slash, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if raise_exception and max_val < 0.9: raise Exception("Slash not found")
            
            if not return_amount: return max_val >= 0.9
            
            text = fix_digits(''.join(OCR_Handler.get_text(section)).replace(' ', '').replace('/', ''))
            available = int(text[0])
            return available
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("get_home_builders", e)
        time.sleep(0.1)
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
            ADB_Manager.adbutils_device.shell(f"am start {'-S' if i==0 else ''} -W -n com.supercell.clashofclans/com.supercell.titan.GameApp")
            Input_Handler.click_exit(4, 0.1)
            
            Frame_Handler.get_frame()
            
            try:
                get_home_builders(0, return_amount=False, use_cached_frame=True)
                TEMP_CACHE["location"] = "home_base"
                break
            except (KeyboardInterrupt, SystemExit): raise
            except: pass
            
            try:
                get_builder_builders(0, return_amount=False, use_cached_frame=True)
                TEMP_CACHE["location"] = "builder_base"
                break
            except (KeyboardInterrupt, SystemExit): raise
            except: pass
            
            cont_x, cont_y = Frame_Handler.locate(Asset_Manager.misc_assets["continue"], grayscale=False, thresh=0.8, ref="cc", use_cached=True)
            if cont_x is not None and cont_y is not None:
                Input_Handler.click(cont_x, cont_y)
            
            update_coc(timeout=5, from_in_game=True)
            
            i += 1
        if time.time() - start > timeout:
            stop_coc()
            raise Exception("Failed to start CoC")
        print("CoC started", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))
        return True
    except (KeyboardInterrupt, SystemExit): raise
    except:
        return False

def stop_coc():
    from datetime import datetime
    print("Stopping CoC...", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))
    ADB_Manager.adbutils_device.shell("am force-stop com.supercell.clashofclans")
    to_system_home()
    print("CoC stopped", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))

def update_coc(timeout=10, from_in_game=False):
    import uiautomator2 as u2
    conn = ADB_Manager.uiautomator_device
    if not from_in_game:
        ADB_Manager.adbutils_device.shell('am start -a android.intent.action.VIEW -d "market://details?id=com.supercell.clashofclans"')
    else:
        try:
            conn(text="UPDATE").click(timeout=0)
        except (KeyboardInterrupt, SystemExit): raise
        except:
            print("Failed to click update button")
            if not from_in_game: to_system_home()
            return
    
    try:
        conn(text="Update").click(timeout=timeout)
    except (KeyboardInterrupt, SystemExit): raise
    except:
        print("Failed to click update button")
        pass
    if not from_in_game: to_system_home()

def to_builder_base(ref_cache=False):
    import cv2, time, numpy as np
    
    if ref_cache and TEMP_CACHE.get("location") == "builder_base": return
    
    TEMP_CACHE["location"] = "builder_base"
    
    try:
        get_builder_builders(0, return_amount=False)
        return
    except (KeyboardInterrupt, SystemExit): raise
    except: pass
    
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

def get_builder_builders(timeout=60, return_amount=True, raise_exception=True, use_cached_frame=False):
    import time, cv2
    
    start = time.time()
    while True:
        try:
            section = Frame_Handler.get_frame_section(0.565, 0.04, -0.38, 0.08, high_contrast=True, use_cached=use_cached_frame)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/builder_builders.png")
            
            slash = cv2.cvtColor(Asset_Manager.misc_assets["slash"], cv2.COLOR_RGB2GRAY)
            res = cv2.matchTemplate(section, slash, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if raise_exception and max_val < 0.9: raise Exception("Slash not found")
            
            if not return_amount: return max_val >= 0.9
            
            text = fix_digits(''.join(OCR_Handler.get_text(section)).replace(' ', '').replace('/', ''))
            available = int(text[0])
            return available
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("get_builder_builders", e)
        time.sleep(0.1)
        if time.time() > start + timeout: break
    raise Exception("Failed to get builder builders")

def require_exit(n=5, delay=0.1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = None
            try: result = func(*args, **kwargs)
            except (KeyboardInterrupt, SystemExit): raise
            except: pass
            Input_Handler.click_exit(n, delay)
            return result
        return wrapper
    return decorator

class classproperty:
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, owner):
        return self.func(owner)

class Exit_Handler:
    RUN_AT_EXIT = []
    
    @classmethod
    def register(cls, func):
        import atexit
        if func in cls.RUN_AT_EXIT: return
        atexit.register(func)
        cls.RUN_AT_EXIT.append(func)
        return func

    @classmethod
    def handle_sig(cls, sig, frame):
        import signal, atexit
        for func in cls.RUN_AT_EXIT:
            try:
                func()
                atexit.unregister(func)
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

class Scheduler:
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.start()
    
    add_job = scheduler.add_job

class Disk_Cache(collections.UserDict):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.load_cache()
        Exit_Handler.register(self.save_cache)
    
    def __setitem__(self, key, value):
        from datetime import datetime, timedelta
        super().__setitem__(key, value)
        Scheduler.add_job(
            self.save_cache,
            trigger="date",
            run_date=datetime.now() + timedelta(seconds=10),
            id="save_cache",
            replace_existing=True
        )

    def __getitem__(self, key):
        return super().__getitem__(key)

    def load_cache(self):
        import json, portalocker
        if self.path.exists():
            with portalocker.Lock(self.path, "r", timeout=5) as f:
                self.update(json.load(f))
        return self.data

    def save_cache(self):
        import json, portalocker
        with portalocker.Lock(self.path, "w", timeout=5) as f:
            json.dump(self.data, f, indent=4)

Cache_Manager = Disk_Cache(CACHE_PATH)

class BlueStacks_Manager:
    """
    BlueStacks internal instance name is NOT the same as the bot instance ID or the user-facing instance name.
    Generally should be of the form 'Pie64_X' 'Nougat64_X' 'Tiramisu64_X'
    """
    
    _internal_instance_name = None
    _mim_path = None
    
    @classmethod
    def init(cls):
        Exit_Handler.register(cls.stop)
    
    @classproperty
    def internal_instance_name(cls, instance_id=None):
        import json
        
        if cls._internal_instance_name is not None:
            return cls._internal_instance_name
        
        instance_id = instance_id if instance_id is not None else INSTANCE_ID
        
        if cls._mim_path is None or not Path(cls._mim_path).exists():
            if sys.platform == "darwin":
                cls._mim_path = "/Users/Shared/Library/Application Support/BlueStacks/Engine/UserData/MimMetaData.json"
            elif sys.platform == "win32":
                cls._mim_path = r"C:\ProgramData\BlueStacks_nxt\Engine\UserData\MimMetaData.json"
            else:
                raise Exception("Unsupported OS")
            if cls._mim_path is None or not Path(cls._mim_path).exists():
                cls._mim_path = file_search("/", "MimMetaData.json", ["bluestacks"])

        if cls._internal_instance_name is None and cls._mim_path is not None:
            if cls._mim_path is not None and Path(cls._mim_path).exists():
                mim_data = json.loads(Path(cls._mim_path).read_text())
                instances = {instance['Name']: instance["InstanceName"] for instance in mim_data["Organization"]}
                cls._internal_instance_name = instances.get(instance_id, None)
            else:
                if configs.DEBUG: print("MimMetaData.json not found, using default instance.")
        
        return cls._internal_instance_name
    
    @classmethod
    def check(cls):
        try:
            ADB_Manager.connect_once()
            return True
        except (KeyboardInterrupt, SystemExit): raise
        except: return False

    @classmethod
    def start(cls, instance_id=None, timeout=60):
        import sys, subprocess, time
        
        instance_id = instance_id if instance_id is not None else INSTANCE_ID
        
        if cls.check():
            if configs.DEBUG: print("Bluestacks already running.")
            return
        
        str_target_instance_name = cls.internal_instance_name if cls.internal_instance_name is not None else ""
        if sys.platform == "darwin":
            subprocess.Popen(
                ["open", "-n", "-g", "-a", "BlueStacks", "--args", "--instance", str_target_instance_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        elif sys.platform == "win32":
            bin_path = BLUESTACKS_BIN_PATH if BLUESTACKS_BIN_PATH != "" else r"C:\Program Files\BlueStacks_nxt\HD-Player.exe"
            if not Path(bin_path).exists():
                bin_path = file_search("/", "HD-Player.exe", ["bluestacks"])
            assert Path(bin_path).exists(), f"BlueStacks executable not found at {bin_path}"
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 7
            subprocess.Popen(
                [bin_path, "--instance", str_target_instance_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                startupinfo=startupinfo,
                creationflags=subprocess.DETACHED_PROCESS,
            )
        else:
            raise Exception("Unsupported OS")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if cls.check():
                if configs.DEBUG: print("BlueStacks started.")
                return
            time.sleep(0.5)
        
        raise Exception("BlueStacks failed to start.")

    @classmethod
    def stop(cls, timeout=60):
        import time

        if not cls.check():
            if configs.DEBUG: print("BlueStacks stopped.")
            return
        ADB_Manager.adbutils_device.shell("reboot -p")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if not cls.check():
                if configs.DEBUG: print("BlueStacks stopped.")
                return
            time.sleep(0.5)
        
        raise Exception("BlueStacks failed to stop.")

    @classmethod
    def restart(cls):
        cls.stop()
        cls.start()

class Task_Handler:
    
    cache_valid = False
    cached_exclusions = []
    
    @classmethod
    def get_exclusions(cls, use_cached=False):
        import requests
        
        if use_cached and cls.cache_valid:
            return cls.cached_exclusions
        if WEB_APP_URL != "":
            res = requests.get(
                f"{WEB_APP_URL}/{INSTANCE_ID}/exclude",
                timeout=(10, 20)
            )
            if res.status_code == 200:
                cls.cache_valid = True
                cls.cached_exclusions = res.json().get("exclusions", [])
                return cls.cached_exclusions
        elif configs.LOCAL_GUI and TEMP_CACHE.get("gui_port") is not None:
            res = requests.get(
                f"http://localhost:{TEMP_CACHE['gui_port']}/{INSTANCE_ID}/exclude",
                timeout=(10, 20)
            )
            if res.status_code == 200:
                cls.cache_valid = True
                cls.cached_exclusions = res.json().get("exclusions", [])
                return cls.cached_exclusions
        return None

    @classmethod
    def home_base_priority_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "home_base_priority" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return not configs.PRIORITY_HOME_BASE_UPGRADES

    @classmethod
    def home_lab_priority_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "home_lab_priority" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return not configs.PRIORITY_HOME_LAB_UPGRADES
    
    @classmethod
    def builder_base_priority_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "builder_base_priority" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return not configs.PRIORITY_BUILDER_BASE_UPGRADES
    
    @classmethod
    def builder_lab_priority_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "builder_lab_priority" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return not configs.PRIORITY_BUILDER_LAB_UPGRADES

    @classmethod
    def heroes_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "heroes" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return not configs.UPGRADE_HEROES

    @classmethod
    def home_base_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "home_base" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return not configs.UPGRADE_HOME_BASE

    @classmethod
    def builder_base_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "builder_base" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return not configs.UPGRADE_BUILDER_BASE

    @classmethod
    def home_lab_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "home_lab" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return not configs.UPGRADE_HOME_LAB

    @classmethod
    def builder_lab_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "builder_lab" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return not configs.UPGRADE_BUILDER_LAB

    @classmethod
    def home_attacks_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "home_attacks" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return not configs.ATTACK_HOME_BASE

    @classmethod
    def builder_attacks_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "builder_attacks" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return not configs.ATTACK_BUILDER_BASE

    @classmethod
    def lab_assistant_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "lab_assistant" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return not configs.ASSIGN_LAB_ASSISTANT

    @classmethod
    def builder_apprentice_excluded(cls, **kwargs):
        try:
            exclusions = cls.get_exclusions(**kwargs)
            if exclusions is not None:
                return "builder_apprentice" in exclusions
            raise Exception("No external exclusion source available")
        except (KeyboardInterrupt, SystemExit): raise
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
                except (KeyboardInterrupt, SystemExit): raise
                except: cls.backoff_time = time.time() + 600
        return cls.local_ocr(frame)

    @classmethod
    def local_ocr(cls, frame):
        if not hasattr(cls, 'reader'):
            import easyocr
            cls.reader = easyocr.Reader(['en'], gpu=True)
        result = cls.reader.readtext(frame, detail=0)
        return [text for text in result if text.strip()]

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

class DeviceProxy:
    def __init__(self, manager_cls, private_attr_name):
        self._manager_cls = manager_cls
        self._private_attr_name = private_attr_name

    @property
    def _real_device(self):
        return getattr(self._manager_cls, self._private_attr_name)

    def __getattr__(self, name):
        device = self._real_device
        if device is None:
            if not self._manager_cls.connect():
                raise RuntimeError("Device is not connected and auto-reconnect failed.")
            device = self._real_device

        attr = getattr(device, name)

        if callable(attr):
            def wrapper(*args, **kwargs):
                try:
                    return attr(*args, **kwargs)
                except Exception as e:
                    if configs.DEBUG:
                        print(f"[Auto-Recover] Error on {name}: {e}. Triggering reconnect...")
                    
                    if self._manager_cls.connect():
                        new_device = self._real_device
                        new_attr = getattr(new_device, name)
                        return new_attr(*args, **kwargs)
                    else:
                        raise RuntimeError("Action failed, and auto-reconnection timed out.") from e
            return wrapper
        
        return attr

class ADB_Manager:
    import uiautomator2 as u2
    from adbutils import AdbDevice
    from pyminitouch import MNTDevice
    
    _adbutils_device : AdbDevice | None = None
    _minitouch_device : MNTDevice | None = None
    _uiautomator_device : u2.Device | None = None

    @classmethod
    def is_connected(cls):
        import adbutils

        if cls._adbutils_device is None or cls._minitouch_device is None or cls._uiautomator_device is None:
            return False

        try:
            device_list = adbutils.adb.device_list()
            if cls._adbutils_device.serial not in [d.serial for d in device_list]: return False
            return True
        except (KeyboardInterrupt, SystemExit): raise
        except:
            return False

    @classmethod
    def connect_once(cls, addr=None):
        import subprocess, adbutils, os
        import uiautomator2 as u2
        from pyminitouch import MNTDevice
        
        if addr is None: addr = ADB_ADDRESS
        if ADB_ABS_DIR != "": os.environ["PATH"] = ADB_ABS_DIR + os.pathsep + os.environ["PATH"]
        if cls.is_connected(): return
        subprocess.run(["adb", "start-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        res = adbutils.adb.connect(addr)
        if "connected" not in res:
            subprocess.run(["adb", "kill-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            raise Exception("Failed to connect to ADB.")
        devices = []
        try:
            d1 = adbutils.device(addr)
            d2 = MNTDevice(addr)
            d3 = u2.connect(addr)
            devices = [d1, d2, d3]
            Exit_Handler.register(d2.stop)
        except (KeyboardInterrupt, SystemExit): raise
        except:
            subprocess.run(["adb", "kill-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            raise Exception("Failed to get ADB device.")
        cls._adbutils_device, cls._minitouch_device, cls._uiautomator_device = devices
    
    @classmethod
    def connect(cls, timeout=60):
        import time
        start = time.time()
        while time.time() - start < timeout:
            try:
                cls.connect_once()
                if configs.DEBUG: print("Connected to ADB.")
                return True
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                if configs.DEBUG: print("connect_adb", e)
            time.sleep(0.5)
        if configs.DEBUG: print("Failed to connect to ADB.")
        return False

    @classproperty
    def adbutils_device(cls):
        if cls._adbutils_device is None: cls.connect()
        return DeviceProxy(cls, "_adbutils_device")

    @classproperty
    def minitouch_device(cls):
        if cls._minitouch_device is None: cls.connect()
        return DeviceProxy(cls, "_minitouch_device")

    @classproperty
    def uiautomator_device(cls):
        if cls._uiautomator_device is None: cls.connect()
        return DeviceProxy(cls, "_uiautomator_device")

class Input_Handler:
    @classmethod
    def down(cls, x, y, pointer=0):
        from pyminitouch import CommandBuilder
        if x < 0: x = 1 + x
        if y < 0: y = 1 + y
        MAX_X = int(ADB_Manager.minitouch_device.connection.max_x)
        MAX_Y = int(ADB_Manager.minitouch_device.connection.max_y)
        x = int(x * MAX_X)
        y = int(y * MAX_Y)
        builder = CommandBuilder()
        builder.down(pointer, x, y, 100)
        builder.publish(ADB_Manager.minitouch_device.connection)

    @classmethod
    def up(cls, pointer=0):
        from pyminitouch import CommandBuilder
        builder = CommandBuilder()
        builder.up(pointer)
        builder.publish(ADB_Manager.minitouch_device.connection)

    @classmethod
    def click(cls, x, y, n=1, delay=0, pointer=0):
        import time
        from pyminitouch import CommandBuilder
        if x < 0: x = 1 + x
        if y < 0: y = 1 + y
        MAX_X = int(ADB_Manager.minitouch_device.connection.max_x)
        MAX_Y = int(ADB_Manager.minitouch_device.connection.max_y)
        x = int(x * MAX_X)
        y = int(y * MAX_Y)
        builder = CommandBuilder()
        for _ in range(n):
            builder.down(pointer, x, y, 100)
            builder.commit()
            builder.up(pointer)
            builder.publish(ADB_Manager.minitouch_device.connection)
            time.sleep(delay)

    @classmethod
    def click_exit(cls, n=1, delay=0):
        cls.click(0.99, 0.99, n, delay=delay)

    @classmethod
    def multi_click(cls, x1, y1, x2, y2, duration=0):
        MAX_X = int(ADB_Manager.minitouch_device.connection.max_x)
        MAX_Y = int(ADB_Manager.minitouch_device.connection.max_y)
        ADB_Manager.minitouch_device.tap([(x1*MAX_X, y1*MAX_Y), (x2*MAX_X, y2*MAX_Y)], duration=duration)

    @classmethod
    def swipe(cls, x1, y1, x2, y2, duration=100, hold_end_time=0, inter_points=0, pointer=0):
        import time, numpy as np
        from pyminitouch import CommandBuilder
        
        if x1 < 0: x1 = 1 + x1
        if y1 < 0: y1 = 1 + y1
        if x2 < 0: x2 = 1 + x2
        if y2 < 0: y2 = 1 + y2
        
        builder = CommandBuilder()
        
        MAX_X = int(ADB_Manager.minitouch_device.connection.max_x)
        MAX_Y = int(ADB_Manager.minitouch_device.connection.max_y)
        
        x1 = int(x1 * MAX_X)
        y1 = int(y1 * MAX_Y)
        x2 = int(x2 * MAX_X)
        y2 = int(y2 * MAX_Y)
        
        x_points = np.linspace(x1, x2, inter_points + 2, dtype=int)
        y_points = np.linspace(y1, y2, inter_points + 2, dtype=int)
        dt = duration / (inter_points + 1)
        
        builder.down(pointer, x1, y1, pressure=100)
        builder.publish(ADB_Manager.minitouch_device.connection)
        for x, y in zip(x_points, y_points):
            builder.move(pointer, x, y, pressure=100)
            builder.publish(ADB_Manager.minitouch_device.connection)
            if dt > 0: time.sleep(dt / 1000)
        if hold_end_time > 0: time.sleep(hold_end_time / 1000)
        builder.up(pointer)
        builder.publish(ADB_Manager.minitouch_device.connection)

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
        
        MAX_X = int(ADB_Manager.minitouch_device.connection.max_x)
        MAX_Y = int(ADB_Manager.minitouch_device.connection.max_y)
        
        left_in = to_int_array((0.15 + 0.30*percent)*MAX_X, 0.5*MAX_Y)
        left_out = to_int_array(0.15*MAX_X, 0.5*MAX_Y)
        right_in = to_int_array((0.85 - 0.30*percent)*MAX_X, 0.5*MAX_Y)
        right_out = to_int_array(0.85*MAX_X, 0.5*MAX_Y)
        
        start = [left_in, right_in] if dir=="in" else [left_out, right_out]
        end = [left_out, right_out] if dir=="in" else [left_in, right_in]
        
        builder.down(0, *start[0], pressure=100)
        builder.down(1, *start[1], pressure=100)
        builder.publish(ADB_Manager.minitouch_device.connection)
        builder.move(0, *end[0], pressure=100)
        builder.move(1, *end[1], pressure=100)
        builder.commit()
        builder.publish(ADB_Manager.minitouch_device.connection)
        builder.up(0)
        builder.up(1)
        builder.publish(ADB_Manager.minitouch_device.connection)

class Frame_Handler:
    pool = None
    cached_frame = None
    
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
    def get_frame(cls, grayscale=True, high_contrast=False, thresh=200, use_cached=False):
        import cv2, numpy as np
        if use_cached and cls.cached_frame is not None:
            frame = cls.cached_frame.copy()
        else:
            try: frame = ADB_Manager.adbutils_device.framebuffer() # faster than screenshot but potentially unstable
            except (KeyboardInterrupt, SystemExit): raise
            except: frame = ADB_Manager.adbutils_device.screenshot()
            frame = np.array(frame)[..., :3]
            frame = cv2.resize(frame, WINDOW_DIMS, interpolation=cv2.INTER_NEAREST)
            cls.cached_frame = frame.copy()
        if configs.DEBUG: cls.save_frame(frame, "debug/frame.png")
        if high_contrast: frame = cls.high_contrast(frame, thresh)
        elif grayscale: frame = cls.grayscale(frame)
        return frame

    @classmethod
    def get_frame_section(cls, x1, y1, x2, y2, high_contrast=False, thresh=200, grayscale=True, use_cached=False):
        frame = cls.get_frame(grayscale=grayscale, high_contrast=high_contrast, thresh=thresh, use_cached=use_cached)
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
    def locate(cls, template, frame=None, grayscale=True, thresh=0, ref="cc", null_val=None, return_confidence=False, return_all=False, use_cached=False):
        import cv2, numpy as np

        if grayscale: template = cls.grayscale(template)
        h, w = template.shape[:2]
        frame = cls.get_frame(grayscale=grayscale, use_cached=use_cached) if frame is None else frame
        fh, fw = frame.shape[:2]
        
        if h > fh or w > fw:
            if return_all:
                return []
            if return_confidence:
                return null_val, null_val, 0
            return null_val, null_val

        res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if configs.DEBUG: print("locate confidence:", max_val)
        
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
    def batch_locate(cls, templates, frame=None, grayscale=True, thresh=0, ref="cc", null_val=None, return_confidence=False, return_all=False, use_cached=False):
        from concurrent.futures import ThreadPoolExecutor
        
        if cls.pool is None:
            cls.pool = ThreadPoolExecutor()
            Exit_Handler.register(cls.pool.shutdown)
        
        frame = cls.get_frame(grayscale=grayscale, use_cached=use_cached) if frame is None else frame
        
        threads = []
        for template in templates:
            threads.append(cls.pool.submit(cls.locate, template, frame, grayscale, thresh, ref, null_val, return_confidence, return_all))
        return [thread.result() for thread in threads]

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
