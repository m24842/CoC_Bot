import os
import re
import cv2
import time
import numpy as np
from utils import *
from configs import *

class Upgrader:
    def __init__(self, device, reader):
        self.device = device
        self.frame_handler = Frame_Handler(device)
        self.reader = reader
        self.assets = self.load_assets()

    # ============================================================
    # 📁 Asset & Image Processing
    # ============================================================

    def load_assets(self):
        assets = {}
        for file in os.listdir(UPGRADER_ASSETS_DIR):
            assets[file.replace('.png', '')] = cv2.imread(os.path.join(UPGRADER_ASSETS_DIR, file), cv2.IMREAD_COLOR)
        return assets

    # ============================================================
    # 📱 Screen Interaction
    # ============================================================
    
    def click_exit(self, n=1):
        click(self.device, 0.99, 0.01, n)
    
    def click_builders(self):
        click(self.device, 0.5, 0.05)
    
    def click_lab(self):
        click(self.device, 0.4, 0.05)

    # ============================================================
    # 💰 Resource & Builder Tracking
    # ============================================================

    def get_resources(self, timeout=60):
        start = time.time()
        while time.time() < start + timeout:
            try:
                section = self.frame_handler.get_frame_section(0.8, 0, 0.96, 0.30, high_contrast=True, thresh=240)
                if DEBUG: self.frame_handler.save_frame(section, "debug/resources.png")
                text = get_text(section, self.reader)
                if DEBUG: print(text)
                gold, elixir, dark_elixir = [int(fix_digits(s.replace(' ', ''))) for s in text]
                return {"gold": gold, "elixir": elixir, "dark_elixir": dark_elixir}
            except Exception as e:
                if DEBUG: print("get_resources", e)
            time.sleep(1)
        raise Exception("Failed to get resources")
    
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

    def lab_available(self, timeout=60):
        start = time.time()
        while time.time() < start + timeout:
            try:
                section = self.frame_handler.get_frame_section(0.368, 0.04, -0.59, 0.08, high_contrast=True)
                if DEBUG: self.frame_handler.save_frame(section, "debug/lab.png")
                
                slash = cv2.cvtColor(self.assets["slash"], cv2.COLOR_RGB2GRAY)
                res = cv2.matchTemplate(section, slash, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val < 0.9: continue
                
                text = fix_digits(''.join(get_text(section, self.reader)).replace(' ', '').replace('/', ''))
                available = int(text[0])
                return available > 0
            except Exception as e:
                if DEBUG: print("lab_available", e)
            time.sleep(1)
        raise Exception("Failed to get lab availability")

    def get_resource_type(self, frame):
        gold_template = self.assets["gold"]
        elixir_template = self.assets["elixir"]
        dark_elixir_template = self.assets["dark_elixir"]
        gold_score = cv2.minMaxLoc(cv2.matchTemplate(frame, gold_template, cv2.TM_CCOEFF_NORMED))[1]
        elixir_score = cv2.minMaxLoc(cv2.matchTemplate(frame, elixir_template, cv2.TM_CCOEFF_NORMED))[1]
        dark_elixir_score = cv2.minMaxLoc(cv2.matchTemplate(frame, dark_elixir_template, cv2.TM_CCOEFF_NORMED))[1]
        if DEBUG: print(f"gold={gold_score}, elixir={elixir_score}, dark_elixir={dark_elixir_score}")
        return ["gold", "elixir", "dark_elixir"][np.argmax([gold_score, elixir_score, dark_elixir_score])]

    def collect_resources(self):
        try:
            commands = []
            x_range = np.linspace(0.2, 0.8, 20)
            y_range = np.linspace(0.3, 0.8, 20)
            for x in x_range:
                for y in y_range:
                    commands.append(f"input tap {int(x*WINDOW_DIMS[0])} {int(y*WINDOW_DIMS[1])}")
                    commands.append(f"input tap {int(0.99*WINDOW_DIMS[0])} {int(0.01*WINDOW_DIMS[1])}")
            self.device.shell(" && ".join(commands) + ";")
        except Exception as e:
            if DEBUG: print("collect_resources", e)

    # ============================================================
    # 🧱 Upgrade Management
    # ============================================================

    def upgrade(self):
        try:
            self.click_builders()
            time.sleep(1)
            
            x, y = self.frame_handler.locate(self.assets["suggested_upgrades"], thresh=0.8)
            if x is None or y is None: return 0
            
            section = self.frame_handler.get_frame_section(x-0.13, y+0.02, x+0.03, y+0.08, high_contrast=True)
            if DEBUG: self.frame_handler.save_frame(section, "debug/upgrade_name.png")
            upgrade_name = re.sub(r"\s*x\d+$", "", get_text(section, self.reader)[0].lower())
            section = self.frame_handler.get_frame_section(x-0.13, y+0.02+0.055, x+0.03, y+0.08+0.055, high_contrast=True)
            alternative_upgrade = get_text(section, self.reader)
            
            if "town hall" in upgrade_name and len(alternative_upgrade) > 0:
                upgrade_name = re.sub(r"\s*x\d+$", "", alternative_upgrade[0].lower())
                click(self.device, x, y+0.07+0.055)
            else:
                click(self.device, x, y+0.07)
            time.sleep(1)
            
            self.click_builders()
            time.sleep(1)
            
            x, y = self.frame_handler.locate(self.assets["upgrade"], thresh=0.9)
            if x is None or y is None: return 0
            click(self.device, x, y)
            time.sleep(1)
            
            x, y = self.frame_handler.locate(self.assets["confirm"], grayscale=False, thresh=0.85)
            if x is None or y is None: return 0
            
            section = self.frame_handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, grayscale=False)
            if DEBUG: self.frame_handler.save_frame(section, "debug/upgrade_cost.png")
            if not check_color([255, 136, 127], section, tol=10):
                click(self.device, x, y+0.05)
                self.click_exit(5)
                return upgrade_name
            else:
                section = self.frame_handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, high_contrast=True)
                if DEBUG: self.frame_handler.save_frame(section, "debug/upgrade_cost.png")
                resource_type = self.get_resource_type(self.frame_handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, grayscale=False))
                send_notification(f"Insufficient {resource_type}!")
                self.click_exit(5)
                return None
        except Exception as e:
            if DEBUG: print("upgrade", e)
            return None
    
    def lab_upgrade(self):
        try:
            self.click_lab()
            time.sleep(1)
            
            x, y = self.frame_handler.locate(self.assets["suggested_upgrades"], thresh=0.8)
            if x is None or y is None: return 0
            
            section = self.frame_handler.get_frame_section(x-0.13, y+0.02, x+0.03, y+0.08, high_contrast=True)
            if DEBUG: self.frame_handler.save_frame(section, "debug/lab_upgrade_name.png")
            upgrade_name = re.sub(r"\s*x\d+$", "", get_text(section, self.reader)[0].lower())
            
            click(self.device, x, y+0.07)
            time.sleep(1)
            
            self.click_lab()
            time.sleep(1)
            
            x, y = self.frame_handler.locate(self.assets["confirm"], grayscale=False, thresh=0.85)
            if x is None or y is None: return 0
            
            section = self.frame_handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, grayscale=False)
            if DEBUG: self.frame_handler.save_frame(section, "debug/lab_upgrade_cost.png")
            if not check_color([255, 136, 127], section, tol=10):
                click(self.device, x, y+0.05)
                self.click_exit(5)
                return upgrade_name
            else:
                section = self.frame_handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, high_contrast=True)
                if DEBUG: self.frame_handler.save_frame(section, "debug/lab_upgrade_cost.png")
                resource_type = self.get_resource_type(self.frame_handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, grayscale=False))
                send_notification(f"Insufficient {resource_type}!")
                self.click_exit(5)
                return None
        except Exception as e:
            if DEBUG: print("lab_upgrade", e)
            return None

    # ============================================================
    # 📡 Upgrade Monitoring
    # ============================================================
    
    def run(self):
        # Collect resources
        self.collect_resources()
        
        # Building upgrades
        upgrades_started = []
        counter = 0
        while counter < MAX_UPGRADES_PER_CHECK:
            counter += 1
            try:
                initial_builders = self.get_builders(1)
                if initial_builders == 0: break
                upgraded = self.upgrade()
                time.sleep(1)
                final_builders = self.get_builders(1)
                if upgraded is not None and final_builders < initial_builders: upgrades_started.append(upgraded)
            except:
                pass
        
        # Lab upgrades
        lab_upgrades_started = []
        try:
            if self.lab_available(1):
                upgraded = self.lab_upgrade()
                time.sleep(1)
                final_lab_avail = self.lab_available(1)
                if upgraded is not None and not final_lab_avail: lab_upgrades_started.append(upgraded)
        except:
            pass
        
        for upgrade in upgrades_started + lab_upgrades_started:
            send_notification(f"Started upgrading {upgrade}")