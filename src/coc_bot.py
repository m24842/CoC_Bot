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
        if DISABLE_DEVICE_SLEEP:
            disable_sleep()
            Exit_Handler.register(enable_sleep)
        
        self.start_bluestacks()
        self.connect_adb()
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
                    timeout=(10, 20)
                )
                return
            except Exception as e:
                if configs.DEBUG: print("update_status", e)
    
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
            if self.check_bluestacks():
                if configs.DEBUG: print("BlueStacks started.")
                return
            time.sleep(0.5)
        
        raise Exception("BlueStacks failed to start.")
    
    def check_bluestacks(self):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'bluestacks' in proc.info['name'].lower():
                return True
        return False

    def connect_adb(self):
        for _ in range(120):
            try:
                connect_adb()
                if configs.DEBUG: print("Connected to ADB.")
                return
            except Exception as e:
                if configs.DEBUG: print("connect_adb", e)
            time.sleep(0.5)
        raise Exception("Failed to connect to ADB.")
    
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
                    
                    exclude_home_base = home_base_excluded()
                    exclude_home_lab = home_lab_excluded()
                    skip_home_base_upgrades = exclude_home_base and exclude_home_lab
                    exclude_home_attacks = home_attacks_excluded()
                    
                    exclude_builder_base = builder_base_excluded()
                    exclude_builder_lab = builder_lab_excluded()
                    skip_builder_base_upgrades = exclude_builder_base and exclude_builder_lab
                    exclude_builder_attacks = builder_attacks_excluded()
                    
                    # Check home base
                    if not skip_home_base_upgrades or not exclude_home_attacks:
                        to_home_base()
                    
                    if not skip_home_base_upgrades:
                        self.upgrader.run_home_base(exclude_home_base, exclude_home_lab)
                    if not exclude_home_attacks:
                        self.attacker.run_home_base(restart=not skip_home_base_upgrades or not skip_builder_base_upgrades)
                    
                    if not skip_builder_base_upgrades or not exclude_builder_attacks:
                        to_builder_base()
                    
                    # Check builder base
                    if not skip_builder_base_upgrades:
                        self.upgrader.collect_builder_attack_elixir()
                        self.upgrader.run_builder_base(exclude_builder_base, exclude_builder_lab)
                    if not exclude_builder_attacks:
                        self.attacker.run_builder_base()
                    
                    to_home_base()
                    stop_coc()
                    self.update_status(time.time())
                
                time.sleep(CHECK_INTERVAL)
            
            except Exception as e:
                print(e)
                stop_coc()
                self.update_status("error")