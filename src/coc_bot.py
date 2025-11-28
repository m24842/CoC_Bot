import loguru
import warnings

loguru.logger.remove()
warnings.filterwarnings("ignore", category=UserWarning, module='torch')

import sys
import time
import psutil
import requests
import subprocess
import utils
from utils import *
from configs import *
from upgrader import Upgrader
from attacker import Attacker

class CoC_Bot:
    def __init__(self):
        if DISABLE_DEEVICE_SLEEP:
            disable_sleep()
            Exit_Handler.register(enable_sleep)
        
        self.start_bluestacks()
        self.upgrader = Upgrader()
        self.attacker = Attacker()

    # ============================================================
    # 🖥️ System & Emulator Management
    # ============================================================
    
    def update_status(self, status):
        if WEB_APP_URL == "": return
        for _ in range(5):
            try:
                requests.post(
                    f"{WEB_APP_URL}/{utils.INSTANCE_ID}/status",
                    auth=(WEB_APP_AUTH_USERNAME, WEB_APP_AUTH_PASSWORD),
                    json={"status": status},
                    timeout=3
                )
                return
            except Exception as e:
                if configs.DEBUG: print("update_status", e)
    
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
        Exit_Handler.register(cleanup)
    
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
            except Exception as e:
                if configs.DEBUG: print("start_bluestacks", e)
            time.sleep(0.5)
        
        raise Exception("BlueStacks failed to start.")
    
    def check_bluestacks(self):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'bluestacks' in proc.info['name'].lower():
                return True
        return False

    # ============================================================
    # ⏱️ Task Execution
    # ============================================================
    
    def run(self):
        while True:
            try:
                if not running():
                    time.sleep(1)
                    continue
                
                if start_coc():
                    self.update_status("now")
                    
                    self.upgrader.run()
                    self.attacker.run(restart=False)
                    
                    stop_coc()
                    self.update_status(time.time())
                
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                print(e)
                stop_coc()
                self.update_status("error")