import sys
import time
import psutil
import atexit
import easyocr
import requests
import adbutils
import subprocess
from datetime import datetime
from pyminitouch import MNTDevice
from utils import *
from configs import *
from upgrader import Upgrader
from attacker import Attacker

class CoC_Bot:
    def __init__(self):
        if DISABLE_SLEEP:
            disable_sleep()
            atexit.register(enable_sleep)
        
        self.device, self.mt_device = None, None
        self.start_bluestacks()
        self.reader = easyocr.Reader(['en'])
        self.frame_handler = Frame_Handler(self.device)
        self.upgrader = Upgrader(self.device, self.reader)
        self.assets = self.upgrader.assets.copy()
        self.attacker = Attacker(self.device, self.mt_device, self.reader)

    # ============================================================
    # 🖥️ System & Emulator Management
    # ============================================================

    @property
    def running(self):
        if WEB_APP_IP == "": return True
        try:
            response = requests.get(f"http://{WEB_APP_IP}:{WEB_APP_PORT}/running", timeout=3)
            if response.status_code == 200:
                return response.json().get("running", False)
            return False
        except Exception as e:
            if DEBUG: print("running", e)
            return False
    
    def update_status(self, status):
        if WEB_APP_IP == "": return
        try:
            requests.post(f"http://{WEB_APP_IP}:{WEB_APP_PORT}/status", json={"status": status}, timeout=3)
        except Exception as e:
            if DEBUG: print("update_status", e)
    
    def start_web_app(self):
        proc = subprocess.Popen(
            [sys.executable, "./app/app.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        def cleanup():
            try:
                proc.terminate()
            except Exception:
                pass
        atexit.register(cleanup)
    
    def start_bluestacks(self):
        if sys.platform == "darwin":
            subprocess.Popen([
                "osascript", "-e",
                'tell application "BlueStacks" to launch\n'
                'tell application "BlueStacks" to set visible of front window to false'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 6
            subprocess.Popen([r"C:\Program Files\BlueStacks_nxt\HD-Player.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo=startupinfo)
        
        for _ in range(120):
            if self.check_bluestacks(): break
            time.sleep(0.5)
        
        for _ in range(120):
            try:
                self.device, self.mt_device = self.connect_adb()
                return
            except: pass
            time.sleep(0.5)
        
        raise Exception("BlueStacks failed to start.")
    
    def check_bluestacks(self):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'bluestacks' in proc.info['name'].lower():
                return True
        return False
    
    def connect_adb(self):
        res = adbutils.adb.connect("127.0.0.1:5555")
        if "connected" not in res:
            raise Exception("Failed to connect to ADB.")
        device, mt_device = None, None
        try:
            device = adbutils.adb.device("127.0.0.1:5555")
            mt_device = MNTDevice("127.0.0.1:5555")
            atexit.register(mt_device.stop)
        except:
            raise Exception("Failed to get ADB device.")
        return device, mt_device
    
    def start(self, timeout=60):
        try:
            print("Starting CoC...", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))
            start = time.time()
            while time.time() - start < timeout:
                try:
                    self.device.shell("am start -W -n com.supercell.clashofclans/com.supercell.titan.GameApp")
                    self.click_exit(5)
                    self.get_builders(1)
                    break
                except:
                    pass
                time.sleep(1)
            if time.time() - start > timeout:
                self.stop()
                raise Exception("Failed to start CoC")
            print("CoC started", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))
            return True
        except:
            return False
    
    def stop(self):
        print("Stopping CoC...", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))
        self.device.shell("am force-stop com.supercell.clashofclans")
        print("CoC stopped", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))

    # ============================================================
    # 📱 Screen Interaction
    # ============================================================

    def click(self, x, y, n=1, delay=0):
        if x < 0: x = 1 + x
        if y < 0: y = 1 + y
        command = [f"input tap {int(x*WINDOW_DIMS[0])} {int(y*WINDOW_DIMS[1])}"] * n
        if delay == 0:
            command = " && ".join(command) + ";"
            self.device.shell(command)
        else:
            for c in command:
                self.device.shell(c)
                time.sleep(delay)
    
    def click_exit(self, n=1):
        self.click(0.99, 0.01, n, delay=0.1)
    
    def get_builders(self, timeout=60):
        start = time.time()
        while time.time() < start + timeout:
            try:
                section = self.frame_handler.get_frame_section(0.49, 0.04, -0.455, 0.08, high_contrast=True)
                if DEBUG: self.frame_handler.save_frame(section, "debug/builders.png")
                
                slash = cv2.cvtColor(self.assets["slash"], cv2.COLOR_RGB2GRAY)
                res = cv2.matchTemplate(section, slash, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val < 0.9: continue
                
                text = fix_digits(''.join(get_text(section, self.reader)).replace(' ', '').replace('/', ''))
                available = int(text[0])
                return available
            except Exception as e:
                if DEBUG: print("get_builders", e)
            time.sleep(1)
        raise Exception("Failed to get builders")
    
    # ============================================================
    # ⏱️ Task Execution
    # ============================================================
    
    def run(self):
        while True:
            try:
                if not self.running:
                    time.sleep(1)
                    continue
                
                if self.start():
                    self.update_status("now")
                    
                    self.upgrader.run()
                    self.attacker.run()
                    
                    self.stop()
                    self.update_status(time.time())
                
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                print(e)
                self.stop()
                self.update_status("error")