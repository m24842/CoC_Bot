import os
import re
import cv2
import time
import numpy as np
import utils
from utils import *
import configs
from configs import *

class Upgrader:
    def __init__(self):
        self.frame_handler = Frame_Handler()
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
    
    def click_builders(self):
        click(0.5, 0.05)
    
    def click_lab(self):
        click(0.4, 0.05)

    # ============================================================
    # 💰 Resource & Builder Tracking
    # ============================================================

    def get_resources(self, timeout=60):
        start = time.time()
        while time.time() < start + timeout:
            try:
                section = self.frame_handler.get_frame_section(0.8, 0, 0.96, 0.30, high_contrast=True, thresh=240)
                if configs.DEBUG: self.frame_handler.save_frame(section, "debug/resources.png")
                text = get_text(section)
                if configs.DEBUG: print(text)
                gold, elixir, dark_elixir = [int(fix_digits(s.replace(' ', ''))) for s in text]
                return {"gold": gold, "elixir": elixir, "dark_elixir": dark_elixir}
            except Exception as e:
                if configs.DEBUG: print("get_resources", e)
            time.sleep(0.5)
        raise Exception("Failed to get resources")
    
    def get_builders(self, timeout=60):
        start = time.time()
        while time.time() < start + timeout:
            try:
                section = self.frame_handler.get_frame_section(0.49, 0.04, -0.455, 0.08, high_contrast=True)
                if configs.DEBUG: self.frame_handler.save_frame(section, "debug/builders.png")
                
                slash = cv2.cvtColor(self.assets["slash"], cv2.COLOR_RGB2GRAY)
                res = cv2.matchTemplate(section, slash, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val < 0.9: continue
                
                text = fix_digits(''.join(get_text(section)).replace(' ', '').replace('/', ''))
                available = int(text[0])
                return available
            except Exception as e:
                if configs.DEBUG: print("get_builders", e)
            time.sleep(0.5)
        raise Exception("Failed to get builders")

    def lab_available(self, timeout=60):
        start = time.time()
        while time.time() < start + timeout:
            try:
                section = self.frame_handler.get_frame_section(0.368, 0.04, -0.59, 0.08, high_contrast=True)
                if configs.DEBUG: self.frame_handler.save_frame(section, "debug/lab.png")
                
                slash = cv2.cvtColor(self.assets["slash"], cv2.COLOR_RGB2GRAY)
                res = cv2.matchTemplate(section, slash, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val < 0.9: continue
                
                text = fix_digits(''.join(get_text(section)).replace(' ', '').replace('/', ''))
                available = int(text[0])
                return available > 0
            except Exception as e:
                if configs.DEBUG: print("lab_available", e)
            time.sleep(0.5)
        raise Exception("Failed to get lab availability")

    def get_resource_type(self, frame):
        gold_template = self.assets["gold"]
        elixir_template = self.assets["elixir"]
        dark_elixir_template = self.assets["dark_elixir"]
        gold_score = cv2.minMaxLoc(cv2.matchTemplate(frame, gold_template, cv2.TM_CCOEFF_NORMED))[1]
        elixir_score = cv2.minMaxLoc(cv2.matchTemplate(frame, elixir_template, cv2.TM_CCOEFF_NORMED))[1]
        dark_elixir_score = cv2.minMaxLoc(cv2.matchTemplate(frame, dark_elixir_template, cv2.TM_CCOEFF_NORMED))[1]
        if configs.DEBUG: print(f"gold={gold_score}, elixir={elixir_score}, dark_elixir={dark_elixir_score}")
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
            utils.ADB_DEVICE.shell(" && ".join(commands) + ";")
        except Exception as e:
            if configs.DEBUG: print("collect_resources", e)

    # ============================================================
    # 🧱 Upgrade Management
    # ============================================================

    def upgrade(self):
        try:
            self.click_builders()
            time.sleep(0.5)
            
            # Find suggested upgrades label
            x_sug, y_sug = self.frame_handler.locate(self.assets["suggested_upgrades"], thresh=0.70)
            if x_sug is None or y_sug is None: return None
            
            # Find other upgrades label
            other_upgrades_avail = True
            x_other, y_other = self.frame_handler.locate(self.assets["other_upgrades"], thresh=0.70)
            if x_other is None or y_other is None: other_upgrades_avail = False
            
            n_sug = 1
            idx = 0
            alt_idx = 1
            if other_upgrades_avail:
                y_diff = abs(y_sug - y_other)
                label_height = 0.055
                n_sug = round(y_diff / label_height) - 1
                if n_sug > 1: idx, alt_idx = np.random.choice(range(n_sug), size=2, replace=False)
                else: alt_idx = 0
            if configs.DEBUG: print(f"upgrade: n_sug={n_sug}, idx={idx}, alt_idx={alt_idx}")
            y_pot = y_sug + label_height * (idx + 1)
            y_alt = y_sug + label_height * (alt_idx + 1)
            
            # Get potential upgrade names
            pot_section = self.frame_handler.get_frame_section(x_sug-0.13, y_pot-0.035, x_sug+0.03, y_pot+0.025, high_contrast=True)
            if configs.DEBUG: self.frame_handler.save_frame(pot_section, "debug/upgrade_name.png")
            pot_upgrade_name = re.sub(r"\s*x\d+$", "", get_text(pot_section)[0].lower())
            
            alt_section = self.frame_handler.get_frame_section(x_sug-0.13, y_alt-0.035, x_sug+0.03, y_alt+0.025, high_contrast=True)
            if configs.DEBUG: self.frame_handler.save_frame(alt_section, "debug/upgrade_name.png")
            alt_upgrade_text = get_text(alt_section)
            
            alt_upgrade_options = ["none"]
            if len(alt_upgrade_text) > 0: alt_upgrade_options.append("suggested")
            if other_upgrades_avail: alt_upgrade_options.append("other")
            if "town hall" in pot_upgrade_name:
                if len(alt_upgrade_options) > 1: alt_upgrade = np.random.choice(alt_upgrade_options)
                else: alt_upgrade = "none"
            else:
                alt_upgrade = np.random.choice(alt_upgrade_options)
            if configs.DEBUG: print(f"alt_upgrade: {alt_upgrade}")
            
            if alt_upgrade == "none":
                click(x_sug, y_pot)
            elif alt_upgrade == "suggested":
                click(x_sug, y_alt)
            elif alt_upgrade == "other":
                click(x_sug, y_other+0.055)
            time.sleep(0.5)
            
            # If suggested upgrades disappears, then there was a misclick, unless hero hall is found
            x_sug, y_sug = self.frame_handler.locate(self.assets["suggested_upgrades"], thresh=0.70)
            x_hero, y_hero = self.frame_handler.locate(self.assets["hero_hall"], thresh=0.8)
            if (x_sug is None or y_sug is None) and (x_hero is None or y_hero is None):
                self.click_builders()
                alt_upgrade = "none"
                click(x_sug, y_pot)
            
            try:
                self.get_builders(1)
                self.click_builders()
            except: pass
            time.sleep(0.5)
            
            # Find upgrade button
            x, y, c = self.frame_handler.locate(self.assets["upgrade"], thresh=0.9, return_confidence=True)
            xyc_hero = self.frame_handler.locate(self.assets["hero_upgrade"], thresh=0.9, return_confidence=True, return_all=True)
            if len(xyc_hero) > 0:
                idx = np.random.randint(0, len(xyc_hero)-1)
                x, y = xyc_hero[idx][:2]
            if x is None or y is None: return None
            click(x, y)
            time.sleep(0.5)
            
            # Get upgrade name
            x, y = self.frame_handler.locate(self.assets["upgrade_name"], ref="lc", thresh=0.9)
            section = self.frame_handler.get_frame_section(x+0.122, y-0.04, 1-x, y+0.035, high_contrast=True)
            if configs.DEBUG: self.frame_handler.save_frame(section, "debug/upgrade_name.png")
            upgrade_name = re.sub(r"\s*x\d+$", "", get_text(section)[0].lower()[:-3])
            
            # Complete upgrade
            x, y = self.frame_handler.locate(self.assets["confirm"], grayscale=False, thresh=0.85)
            if x is None or y is None: return None
            
            section = self.frame_handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, grayscale=False)
            if configs.DEBUG: self.frame_handler.save_frame(section, "debug/upgrade_cost.png")
            if not check_color([255, 136, 127], section, tol=10):
                click(x, y+0.05)
                time.sleep(0.5)
                click_exit(5, 0.1)
                return upgrade_name
            else:
                section = self.frame_handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, high_contrast=True)
                if configs.DEBUG: self.frame_handler.save_frame(section, "debug/upgrade_cost.png")
                resource_type = self.get_resource_type(self.frame_handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, grayscale=False))
                # send_notification(f"Insufficient {resource_type}!")
                click_exit(5, 0.1)
                return None
        except Exception as e:
            if configs.DEBUG: print("upgrade", e)
            return None
    
    def lab_upgrade(self):
        try:
            self.click_lab()
            time.sleep(0.5)
            
            # Find suggested upgrades label
            x_sug, y_sug = self.frame_handler.locate(self.assets["suggested_upgrades"], thresh=0.70)
            if x_sug is None or y_sug is None: return None
            
            # Find other upgrades label
            other_upgrades_avail = True
            x_other, y_other = self.frame_handler.locate(self.assets["other_upgrades"], thresh=0.70)
            if x_other is None or y_other is None: other_upgrades_avail = False
            
            if other_upgrades_avail:
                y_diff = abs(y_sug - y_other)
                label_height = 0.055
                n_sug = round(y_diff / label_height) - 1
                idx = np.random.randint(0, n_sug) if n_sug > 0 else 0
                if configs.DEBUG: print(f"lab_upgrade: n_sug={n_sug}, idx={idx}")
                y_pot = y_sug + label_height * (idx + 1)
            else:
                y_pot = y_sug + 0.055

            click(x_sug, y_pot)
            time.sleep(0.5)
            
            # Get upgrade name
            x, y = self.frame_handler.locate(self.assets["upgrade_name"], ref="lc", thresh=0.9)
            section = self.frame_handler.get_frame_section(x+0.122, y-0.04, 1-x, y+0.035, high_contrast=True)
            if configs.DEBUG: self.frame_handler.save_frame(section, "debug/lab_upgrade_name.png")
            upgrade_name = re.sub(r"\s*x\d+$", "", get_text(section)[0].lower()[:-3])
            
            # Complete upgrade
            x, y = self.frame_handler.locate(self.assets["confirm"], grayscale=False, thresh=0.85)
            if x is None or y is None: return None
            
            section = self.frame_handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, grayscale=False)
            if configs.DEBUG: self.frame_handler.save_frame(section, "debug/lab_upgrade_cost.png")
            if not check_color([255, 136, 127], section, tol=10):
                click(x, y+0.05)
                time.sleep(0.5)
                click_exit(5, 0.1)
                return upgrade_name
            else:
                section = self.frame_handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, high_contrast=True)
                if configs.DEBUG: self.frame_handler.save_frame(section, "debug/lab_upgrade_cost.png")
                resource_type = self.get_resource_type(self.frame_handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, grayscale=False))
                # send_notification(f"Insufficient {resource_type}!")
                click_exit(5, 0.1)
                return None
        except Exception as e:
            if configs.DEBUG: print("lab_upgrade", e)
            return None

    # ============================================================
    # 📡 Upgrade Monitoring
    # ============================================================
    
    def run(self):
        zoom(dir="out")
        swipe_down()
        
        # Collect resources
        if COLLECT_RESOURCES:
            self.collect_resources()
            time.sleep(5)
        
        # Building upgrades
        upgrades_started = []
        counter = 0
        while counter < MAX_UPGRADES_PER_CHECK:
            counter += 1
            try:
                initial_builders = self.get_builders(1)
                if initial_builders == 0: break
                upgraded = self.upgrade()
                click_exit(5, 0.1)
                time.sleep(0.5)
                final_builders = self.get_builders(1)
                if upgraded is not None:
                    if final_builders < initial_builders: upgrades_started.append(upgraded)
                    elif final_builders == initial_builders and upgraded != "wall": break
            except:
                pass
        
        # Lab upgrades
        lab_upgrades_started = []
        try:
            if self.lab_available(1):
                upgraded = self.lab_upgrade()
                click_exit(5, 0.1)
                time.sleep(0.5)
                final_lab_avail = self.lab_available(1)
                if upgraded is not None and not final_lab_avail: lab_upgrades_started.append(upgraded)
        except:
            pass
        
        for upgrade in upgrades_started + lab_upgrades_started:
            send_notification(f"Started upgrading {upgrade}")