import utils
from utils import *
from configs import *
from upgrader import Upgrader
from attacker import Attacker

class CoC_Bot:
    def __init__(self):
        self.start_bluestacks()
        self.connect_adb()
        self.upgrader = Upgrader()
        self.attacker = Attacker()

    # ============================================================
    # 🖥️ System & Emulator Management
    # ============================================================
    
    def update_status(self, status):
        import requests
        from gui import get_gui
        
        if WEB_APP_URL != "":
            try:
                requests.post(
                    f"{WEB_APP_URL}/{utils.INSTANCE_ID}/status",
                    json={"status": status},
                    timeout=(1, 2)
                )
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                if configs.DEBUG: print("update_status", e)
        if get_gui() is not None:
            try:
                requests.post(
                    f"http://localhost:{get_gui().server_port}/status",
                    json={"status": status},
                    timeout=(1, 2)
                )
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                if configs.DEBUG: print("update_status", e)
    
    def start_bluestacks(self):
        import sys, subprocess, time
        
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
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'bluestacks' in proc.info['name'].lower():
                return True
        return False

    def connect_adb(self):
        import time
        for _ in range(120):
            try:
                connect_adb()
                if configs.DEBUG: print("Connected to ADB.")
                return
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                if configs.DEBUG: print("connect_adb", e)
            time.sleep(0.5)
        raise Exception("Failed to connect to ADB.")
    
    # ============================================================
    # ⏱️ Task Execution
    # ============================================================
    
    def run(self):
        import time
        
        while True:
            try:
                if not running():
                    time.sleep(1)
                    continue
                
                if start_coc():
                    self.update_status("now")
                    
                    Task_Handler.get_exclusions()
                    exclude_home_base = Task_Handler.home_base_excluded(use_cached=True)
                    exclude_home_lab = Task_Handler.home_lab_excluded(use_cached=True)
                    skip_home_base_upgrades = exclude_home_base and exclude_home_lab
                    exclude_home_attacks = Task_Handler.home_attacks_excluded(use_cached=True)
                    
                    exclude_builder_base = Task_Handler.builder_base_excluded(use_cached=True)
                    exclude_builder_lab = Task_Handler.builder_lab_excluded(use_cached=True)
                    skip_builder_base_upgrades = exclude_builder_base and exclude_builder_lab
                    exclude_builder_attacks = Task_Handler.builder_attacks_excluded(use_cached=True)
                    
                    # Check home base
                    if not skip_home_base_upgrades or not exclude_home_attacks:
                        to_home_base()
                    
                    if not skip_home_base_upgrades:
                        self.upgrader.run_home_base(exclude_home_base, exclude_home_lab)
                    if not exclude_home_attacks:
                        self.attacker.run_home_base(restart=not skip_home_base_upgrades or not skip_builder_base_upgrades)
                    
                    # Check builder base
                    if not skip_builder_base_upgrades or not exclude_builder_attacks:
                        to_builder_base()
                    
                    if not skip_builder_base_upgrades:
                        self.upgrader.collect_builder_attack_elixir()
                        self.upgrader.run_builder_base(exclude_builder_base, exclude_builder_lab)
                    if not exclude_builder_attacks:
                        self.attacker.run_builder_base()
                    
                    to_home_base()
                    stop_coc()
                    self.update_status(time.time())
                
                time.sleep(CHECK_INTERVAL)
            
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                print(e)
                stop_coc()
                self.update_status("error")