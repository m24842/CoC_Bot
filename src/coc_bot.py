import loguru
import warnings

loguru.logger.remove()
warnings.filterwarnings("ignore", category=UserWarning, module='torch')

import sys
import time
import psutil
import atexit
import requests
import subprocess
from datetime import datetime
import utils
from utils import *
from configs import *
from upgrader import Upgrader
from attacker import Attacker

class CoC_Bot:
    def __init__(self):
        if DISABLE_DEEVICE_SLEEP:
            disable_sleep()
            atexit.register(enable_sleep)
        
        self.start_bluestacks()
        self.frame_handler = Frame_Handler()
        self.upgrader = Upgrader()
        self.assets = self.upgrader.assets.copy()
        self.attacker = Attacker()

    # ============================================================
    # 🖥️ System & Emulator Management
    # ============================================================

    @property
    def running(self):
        if WEB_APP_URL == "": return True
        try:
            response = requests.get(f"{WEB_APP_URL}/running", timeout=3)
            if response.status_code == 200:
                return response.json().get("running", False)
            return False
        except Exception as e:
            if DEBUG: print("running", e)
            return False
    
    def update_status(self, status):
        if WEB_APP_URL == "": return
        try:
            requests.post(f"{WEB_APP_URL}/status", json={"status": status}, timeout=3)
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
                connect_adb()
                return
            except: pass
            time.sleep(0.5)
        
        raise Exception("BlueStacks failed to start.")
    
    def check_bluestacks(self):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'bluestacks' in proc.info['name'].lower():
                return True
        return False
    
    def start(self, timeout=60):
        try:
            print("Starting CoC...", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))
            start = time.time()
            while time.time() - start < timeout:
                try:
                    utils.ADB_DEVICE.shell("am start -W -n com.supercell.clashofclans/com.supercell.titan.GameApp")
                    click_exit(5, 0.1)
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
        utils.ADB_DEVICE.shell("am force-stop com.supercell.clashofclans")
        print("CoC stopped", datetime.now().strftime("%I:%M:%S %p %m-%d-%Y"))

    # ============================================================
    # 📱 Screen Interaction
    # ============================================================
    
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
                
                text = fix_digits(''.join(get_text(section)).replace(' ', '').replace('/', ''))
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