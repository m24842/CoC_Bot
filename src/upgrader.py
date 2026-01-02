import os
import re
import cv2
import time
import numpy as np
from scipy.ndimage import gaussian_filter1d
import utils
from utils import *
import configs
from configs import *

class Upgrader:
    def __init__(self):
        self.assets = Asset_Manager.upgrader_assets

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
    
    def click_home_builders(self):
        Input_Handler.click(0.5, 0.05)
    
    def click_home_lab(self):
        Input_Handler.click(0.4, 0.05)

    def click_builder_builders(self):
        Input_Handler.click(0.6, 0.05)
    
    def click_builder_lab(self):
        Input_Handler.click(0.45, 0.05)

    # ============================================================
    # 💰 Resource & Builder Tracking
    # ============================================================

    def get_resources(self, timeout=60):
        start = time.time()
        while time.time() < start + timeout:
            try:
                section = Frame_Handler.get_frame_section(0.8, 0, 0.96, 0.30, high_contrast=True, thresh=240)
                if configs.DEBUG: Frame_Handler.save_frame(section, "debug/resources.png")
                text = get_text(section)
                if configs.DEBUG: print(text)
                gold, elixir, dark_elixir = [int(fix_digits(s.replace(' ', ''))) for s in text]
                return {"gold": gold, "elixir": elixir, "dark_elixir": dark_elixir}
            except Exception as e:
                if configs.DEBUG: print("get_resources", e)
            time.sleep(0.5)
        raise Exception("Failed to get resources")

    def home_lab_available(self, timeout=60):
        start = time.time()
        while time.time() < start + timeout:
            try:
                section = Frame_Handler.get_frame_section(0.368, 0.04, -0.59, 0.08, high_contrast=True)
                if configs.DEBUG: Frame_Handler.save_frame(section, "debug/home_lab.png")
                
                # Find the backslash
                slash = cv2.cvtColor(self.assets["slash"], cv2.COLOR_RGB2GRAY)
                res = cv2.matchTemplate(section, slash, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val < 0.9: continue
                
                # Extract text
                text = fix_digits(''.join(get_text(section)).replace(' ', '').replace('/', ''))
                available = int(text[0])
                return available > 0
            except Exception as e:
                if configs.DEBUG: print("home_lab_available", e)
            time.sleep(0.5)
        raise Exception("Failed to get home lab availability")

    def builder_lab_available(self, timeout=60):
        start = time.time()
        while time.time() < start + timeout:
            try:
                section = Frame_Handler.get_frame_section(0.448, 0.04, -0.515, 0.08, high_contrast=True)
                if configs.DEBUG: Frame_Handler.save_frame(section, "debug/builder_lab.png")
                
                # Find the backslash
                slash = cv2.cvtColor(self.assets["slash"], cv2.COLOR_RGB2GRAY)
                res = cv2.matchTemplate(section, slash, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
                if max_val < 0.9: continue
                
                # Extract text
                text = fix_digits(''.join(get_text(section)).replace(' ', '').replace('/', ''))
                available = int(text[0])
                return available > 0
            except Exception as e:
                if configs.DEBUG: print("builder_lab_available", e)
            time.sleep(0.5)
        raise Exception("Failed to get builder lab availability")

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

    def collect_builder_attack_elixir(self):
        # Align view to top right corner
        Input_Handler.zoom(dir="out")
        for _ in range(3):
            Input_Handler.swipe_up(
                y1=0.5,
                y2=1.0,
            )
        Input_Handler.swipe_up(
            y1=0.5,
            y2=1.0,
            hold_end_time=500,
        )
        for _ in range(3):
            Input_Handler.swipe_left(
                x1=1.0,
                x2=0.0,
            )
        Input_Handler.swipe_left(
            x1=1.0,
            x2=0.0,
            hold_end_time=500,
        )
        time.sleep(0.5)
        
        # Open elixir cart menu
        Input_Handler.click(0.61, 0.47)
        time.sleep(0.5)
        
        # Collect elixir
        x, y = Frame_Handler.locate(self.assets["collect"], grayscale=False, thresh=0.9)
        if x is not None and y is not None:
            Input_Handler.click(x, y)
            time.sleep(0.1)
        Input_Handler.click_exit(5, 0.1)

    # ============================================================
    # 🧱 Upgrade Management
    # ============================================================

    @require_exit()
    def home_upgrade(self):
        try:
            # Open upgrade list menu
            self.click_home_builders()
            time.sleep(0.5)
            
            # Find suggested upgrades label
            x_sug, y_sug = Frame_Handler.locate(self.assets["suggested_upgrades"], thresh=0.70)
            if x_sug is None or y_sug is None: return None
            
            # Find other upgrades label
            other_upgrades_avail = True
            x_other, y_other = Frame_Handler.locate(self.assets["other_upgrades"], thresh=0.70)
            if x_other is None or y_other is None: other_upgrades_avail = False
            
            # Determine amount of suggested upgrades
            # Make two random selections
            n_sug = 1
            idx = 0
            alt_idx = 1
            label_height = 0.055
            if other_upgrades_avail:
                y_diff = abs(y_sug - y_other)
                n_sug = round(y_diff / label_height) - 1
                if n_sug > 1: idx, alt_idx = np.random.choice(range(n_sug), size=2, replace=False)
                else: alt_idx = 0
            if configs.DEBUG: print(f"upgrade: n_sug={n_sug}, idx={idx}, alt_idx={alt_idx}")
            y_pot = y_sug + label_height * (idx + 1)
            y_alt = y_sug + label_height * (alt_idx + 1)
            
            # Get potential upgrade names
            pot_section = Frame_Handler.get_frame_section(x_sug-0.13, y_pot-0.035, x_sug+0.03, y_pot+0.025, high_contrast=True)
            if configs.DEBUG: Frame_Handler.save_frame(pot_section, "debug/upgrade_name.png")
            pot_upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", get_text(pot_section)[0].lower()))
            
            alt_section = Frame_Handler.get_frame_section(x_sug-0.13, y_alt-0.035, x_sug+0.03, y_alt+0.025, high_contrast=True)
            if configs.DEBUG: Frame_Handler.save_frame(alt_section, "debug/upgrade_name.png")
            alt_upgrade_text = get_text(alt_section)
            
            # Choose one upgrade from suggested and other upgrades
            alt_upgrade_options = ["none"]
            if len(alt_upgrade_text) > 0: alt_upgrade_options.append("suggested")
            if other_upgrades_avail: alt_upgrade_options.append("other")
            if "town hall" in pot_upgrade_name:
                if len(alt_upgrade_options) > 1: alt_upgrade = np.random.choice(alt_upgrade_options)
                else: alt_upgrade = "none"
            else:
                alt_upgrade = np.random.choice(alt_upgrade_options)
            if configs.DEBUG: print(f"alt_upgrade: {alt_upgrade}")
            
            # Click on the chosen upgrade
            if alt_upgrade == "none":
                Input_Handler.click(x_sug, y_pot)
            elif alt_upgrade == "suggested":
                Input_Handler.click(x_sug, y_alt)
            elif alt_upgrade == "other":
                Input_Handler.click(x_sug, y_other+0.055)
            time.sleep(0.5)
            
            # If suggested upgrades disappears, then there was a misclick, unless hero hall is found
            x_sug_test, y_sug_test = Frame_Handler.locate(self.assets["suggested_upgrades"], thresh=0.70)
            x_hero, y_hero = Frame_Handler.locate(self.assets["hero_hall"], thresh=0.8)
            if (x_sug_test is None or y_sug_test is None) and (x_hero is None or y_hero is None):
                # Look for upgrade button
                x_upgrade, y_upgrade = Frame_Handler.locate(self.assets["upgrade"], thresh=0.9)
                if x_upgrade is None and y_upgrade is None:
                    # If no upgrade button, build new building
                    building_section = Frame_Handler.get_frame_section(0.05, 0.5, 0.95, 0.51, grayscale=False)[0] / 255
                    grayscale = np.mean(building_section, axis=-1, keepdims=True)
                    gray_dist = np.sqrt(((building_section - grayscale)**2).sum(-1))
                    thresh = 0.1
                    gray_dist = np.where(gray_dist < thresh, 0, 1)
                    centers = []
                    start, prev = 0, 0
                    for i in range(len(gray_dist)):
                        if gray_dist[i] == 1 and prev == 0:
                            start = i
                        if gray_dist[i] == 0 and prev == 1:
                            centers.append((start + i) // 2)
                        prev = gray_dist[i]
                    if gray_dist[-1] == 1: centers.append((start + len(gray_dist)) // 2)
                    rand_center = np.random.choice(centers)
                    Input_Handler.click(0.05 + rand_center / WINDOW_DIMS[0], 0.6) # click new building
                    x, y = Frame_Handler.locate(self.assets["checkmark"], thresh=0.85)
                    if x is None or y is None: return None
                    Input_Handler.click(x, y)
                    time.sleep(0.5)
                    return None
                
                # Otherwise default to the first suggested upgrade
                self.click_home_builders()
                Input_Handler.click(x_sug, y_sug + label_height)
            else:
                # Close the upgrade list menu
                try:
                    get_home_builders(1)
                    self.click_home_builders()
                except: pass
                time.sleep(0.5)
            
            # Find upgrade button
            x, y = Frame_Handler.locate(self.assets["upgrade"], thresh=0.9)
            xy_hero = Frame_Handler.locate(self.assets["hero_upgrade"], thresh=0.97, grayscale=False, return_all=True)
            if len(xy_hero) > 0:
                idx = np.random.randint(0, len(xy_hero))
                x, y = xy_hero[idx]
            if x is None or y is None: return None
            
            # Click upgrade
            Input_Handler.click(x, y)
            time.sleep(0.5)
            
            # Get upgrade name
            x, y = Frame_Handler.locate(self.assets["upgrade_name"], ref="lc", thresh=0.9)
            section = Frame_Handler.get_frame_section(x+0.122, y-0.04, 1-x, y+0.035, high_contrast=True)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/upgrade_name.png")
            upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", get_text(section)[0].lower()[:-3]))
            
            # Find confirm button
            x, y = Frame_Handler.locate(self.assets["confirm"], grayscale=False, thresh=0.85)
            if x is None or y is None: return None
            
            # Ensure sufficient resources for upgrade and confirm upgrade
            section = Frame_Handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, grayscale=False)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/upgrade_cost.png")
            if not check_color([255, 136, 127], section, tol=10):
                Input_Handler.click(x, y+0.05)
                time.sleep(0.5)
                return upgrade_name
            return None
        except Exception as e:
            if configs.DEBUG: print("home_upgrade", e)
            return None
    
    @require_exit()
    def home_lab_upgrade(self):
        try:
            # Open lab upgrade list menu
            self.click_home_lab()
            time.sleep(0.5)
            
            # Find suggested upgrades label
            x_sug, y_sug = Frame_Handler.locate(self.assets["suggested_upgrades"], thresh=0.70)
            if x_sug is None or y_sug is None: return None
            
            # Find other upgrades label
            other_upgrades_avail = True
            x_other, y_other = Frame_Handler.locate(self.assets["other_upgrades"], thresh=0.70)
            if x_other is None or y_other is None: other_upgrades_avail = False
            
            # Choose a random suggested upgrade
            label_height = 0.055
            if other_upgrades_avail:
                y_diff = abs(y_sug - y_other)
                n_sug = round(y_diff / label_height) - 1
                idx = np.random.randint(0, n_sug) if n_sug > 0 else 0
                if configs.DEBUG: print(f"lab_upgrade: n_sug={n_sug}, idx={idx}")
                y_pot = y_sug + label_height * (idx + 1)
            else:
                y_pot = y_sug + label_height

            # Click on the chosen upgrade
            Input_Handler.click(x_sug, y_pot)
            time.sleep(0.5)
            
            # Get upgrade name
            x, y = Frame_Handler.locate(self.assets["upgrade_name"], ref="lc", thresh=0.9)
            section = Frame_Handler.get_frame_section(x+0.122, y-0.04, 1-x, y+0.035, high_contrast=True)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/lab_upgrade_name.png")
            upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", get_text(section)[0].lower()[:-3]))
            
            # Find confirm button
            x, y = Frame_Handler.locate(self.assets["confirm"], grayscale=False, thresh=0.85)
            if x is None or y is None: return None
            
            # Ensure sufficient resources for upgrade and confirm upgrade
            section = Frame_Handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, grayscale=False)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/lab_upgrade_cost.png")
            if not check_color([255, 136, 127], section, tol=10):
                Input_Handler.click(x, y+0.05)
                time.sleep(0.5)
                return upgrade_name
            return None
        except Exception as e:
            if configs.DEBUG: print("home_lab_upgrade", e)
            return None

    @require_exit()
    def builder_upgrade(self):
        try:
            # Open upgrade list menu
            self.click_builder_builders()
            time.sleep(0.5)
            
            # Find suggested upgrades label
            x_sug, y_sug = Frame_Handler.locate(self.assets["suggested_upgrades"], thresh=0.70)
            if x_sug is None or y_sug is None: return None
            
            # Find other upgrades label
            other_upgrades_avail = True
            x_other, y_other = Frame_Handler.locate(self.assets["other_upgrades"], thresh=0.70)
            if x_other is None or y_other is None: other_upgrades_avail = False
            
            # Determine amount of suggested upgrades
            # Make two random selections
            n_sug = 1
            idx = 0
            alt_idx = 1
            label_height = 0.055
            if other_upgrades_avail:
                y_diff = abs(y_sug - y_other)
                n_sug = round(y_diff / label_height) - 1
                if n_sug > 1: idx, alt_idx = np.random.choice(range(n_sug), size=2, replace=False)
                else: alt_idx = 0
            if configs.DEBUG: print(f"upgrade: n_sug={n_sug}, idx={idx}, alt_idx={alt_idx}")
            y_pot = y_sug + label_height * (idx + 1)
            y_alt = y_sug + label_height * (alt_idx + 1)
            
            # Get alternative upgrade name
            name_section = Frame_Handler.get_frame_section(x_sug-0.13, y_alt-0.035, x_sug+0.03, y_alt+0.025, high_contrast=True)
            if configs.DEBUG: Frame_Handler.save_frame(name_section, "debug/upgrade_name.png")
            alt_upgrade_text = get_text(name_section)
            
            # Choose one upgrade from suggested and other upgrades
            alt_upgrade_options = ["none"]
            if len(alt_upgrade_text) > 0: alt_upgrade_options.append("suggested")
            if other_upgrades_avail: alt_upgrade_options.append("other")
            alt_upgrade = np.random.choice(alt_upgrade_options)
            if configs.DEBUG: print(f"alt_upgrade: {alt_upgrade}")
            
            # Click on the chosen upgrade and get upgrade name
            if alt_upgrade == "none":
                name_section = Frame_Handler.get_frame_section(x_sug-0.13, y_pot-0.035, x_sug+0.03, y_pot+0.025, high_contrast=True)
                upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", get_text(name_section)[0].lower()))
                Input_Handler.click(x_sug, y_pot)
            elif alt_upgrade == "suggested":
                upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", alt_upgrade_text[0].lower()))
                Input_Handler.click(x_sug, y_alt)
            elif alt_upgrade == "other":
                name_section = Frame_Handler.get_frame_section(x_sug-0.13, y_other+0.055-0.035, x_sug+0.03, y_other+0.055+0.025, high_contrast=True)
                upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", get_text(name_section)[0].lower()))
                Input_Handler.click(x_sug, y_other+0.055)
            time.sleep(0.5)
                        
            # If suggested upgrades disappears, then there was a misclick
            x_sug, y_sug = Frame_Handler.locate(self.assets["suggested_upgrades"], thresh=0.70)
            if x_sug is None or y_sug is None:
                # Look for upgrade button
                x_upgrade, y_upgrade = Frame_Handler.locate(self.assets["upgrade"], thresh=0.9)
                if x_upgrade is None and y_upgrade is None:
                    # If no upgrade button, build new building
                    Input_Handler.click(0.5, 0.6) # click new building
                    x, y = Frame_Handler.locate(self.assets["checkmark"], thresh=0.85)
                    if x is None or y is None: return None
                    Input_Handler.click(x, y)
                    time.sleep(0.5)
                    return None
                
                # Otherwise default to the first suggested upgrade
                self.click_builder_builders()
                Input_Handler.click(x_sug, y_sug + label_height)
            else:
                # Close the upgrade list menu
                try:
                    get_builder_builders(1)
                    self.click_builder_builders()
                except: pass
                time.sleep(0.5)
            
            # Find upgrade button
            x, y = Frame_Handler.locate(self.assets["upgrade"], thresh=0.9)
            if x is None or y is None: return None
            
            # Click upgrade
            Input_Handler.click(x, y)
            time.sleep(0.5)
            
            # # Get upgrade name
            # section = Frame_Handler.get_frame_section(0.15, 0.1, 0.43, 0.35, high_contrast=True, thresh=240)
            # if configs.DEBUG: Frame_Handler.save_frame(section, "debug/upgrade_name.png")
            # upgrade_name = spell_check("".join(get_text(section)).lower())
            
            # Find confirm button
            thresh = 0.2
            section = Frame_Handler.get_frame_section(0.0, 0.9, 1.0, 0.92, grayscale=False)
            section = cv2.cvtColor(section, cv2.COLOR_BGR2LAB)
            avg_color = cv2.mean(cv2.cvtColor(self.assets["blank_green_button"], cv2.COLOR_BGR2LAB))[:3]
            diff = np.linalg.norm((section - avg_color)/255, axis=2).mean(0)
            diff = gaussian_filter1d(diff, sigma=10)
            min_loc = np.argmin(diff)
            x = min_loc / section.shape[1]
            if diff[min_loc] > thresh: return None
            x1 = x
            i = min_loc
            while i > 0 and diff[i] < thresh:
                x1 = i / section.shape[1]
                i -= 1
            x2 = x
            i = min_loc
            while i < section.shape[1]-1 and diff[i] < thresh:
                x2 = i / section.shape[1]
                i += 1
            x = (x1 + x2) / 2
            y = 0.85
            
            # Ensure sufficient resources for upgrade and confirm upgrade
            section = Frame_Handler.get_frame_section(x1-0.02, y-0.05, x2+0.05, y+0.09, grayscale=False)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/upgrade_cost.png")
            if not check_color([255, 136, 127], section, tol=10):
                Input_Handler.click(x, y)
                time.sleep(0.5)
                return upgrade_name
            return None
        except Exception as e:
            if configs.DEBUG: print("builder_upgrade", e)
            return None
    
    @require_exit()
    def builder_lab_upgrade(self):
        try:
            # Open lab upgrade list menu
            self.click_builder_lab()
            time.sleep(0.5)
            
            # Find suggested upgrades label
            x_sug, y_sug = Frame_Handler.locate(self.assets["suggested_upgrades"], thresh=0.70)
            if x_sug is None or y_sug is None: return None
            
            # Find other upgrades label
            other_upgrades_avail = True
            x_other, y_other = Frame_Handler.locate(self.assets["other_upgrades"], thresh=0.70)
            if x_other is None or y_other is None: other_upgrades_avail = False
            
            # Choose a random suggested upgrade
            label_height = 0.055
            if other_upgrades_avail:
                y_diff = abs(y_sug - y_other)
                n_sug = round(y_diff / label_height) - 1
                idx = np.random.randint(0, n_sug) if n_sug > 0 else 0
                if configs.DEBUG: print(f"lab_upgrade: n_sug={n_sug}, idx={idx}")
                y_pot = y_sug + label_height * (idx + 1)
            else:
                y_pot = y_sug + label_height

            # Get upgrade name
            pot_section = Frame_Handler.get_frame_section(x_sug-0.13, y_pot-0.035, x_sug+0.03, y_pot+0.025, high_contrast=True)
            if configs.DEBUG: Frame_Handler.save_frame(pot_section, "debug/lab_upgrade_name.png")
            upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", get_text(pot_section)[0].lower()))

            # Click on the chosen upgrade
            Input_Handler.click(x_sug, y_pot)
            time.sleep(0.5)
            
            # Find confirm button
            thresh = 0.2
            section = Frame_Handler.get_frame_section(0.0, 0.9, 1.0, 0.92, grayscale=False)
            section = cv2.cvtColor(section, cv2.COLOR_BGR2LAB)
            avg_color = cv2.mean(cv2.cvtColor(self.assets["blank_green_button"], cv2.COLOR_BGR2LAB))[:3]
            diff = np.linalg.norm((section - avg_color)/255, axis=2).mean(0)
            diff = gaussian_filter1d(diff, sigma=10)
            min_loc = np.argmin(diff)
            x = min_loc / section.shape[1]
            if diff[min_loc] > thresh: return None
            x1 = x
            i = min_loc
            while i > 0 and diff[i] < thresh:
                x1 = i / section.shape[1]
                i -= 1
            x2 = x
            i = min_loc
            while i < section.shape[1]-1 and diff[i] < thresh:
                x2 = i / section.shape[1]
                i += 1
            x = (x1 + x2) / 2
            y = 0.85
            
            # Ensure sufficient resources for upgrade and confirm upgrade
            section = Frame_Handler.get_frame_section(x1-0.02, y-0.05, x2+0.05, y+0.09, grayscale=False)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/lab_upgrade_cost.png")
            if not check_color([255, 136, 127], section, tol=10):
                Input_Handler.click(x, y)
                time.sleep(0.5)
                return upgrade_name
            return None
        except Exception as e:
            if configs.DEBUG: print("home_lab_upgrade", e)
            return None
    
    # ============================================================
    # 📡 Upgrade Monitoring
    # ============================================================
    
    def run_home_base(self):
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_down()
        
        # Building upgrades
        upgrades_started = []
        counter = 0
        while counter < MAX_UPGRADES_PER_CHECK:
            counter += 1
            try:
                initial_builders = get_home_builders(1)
                if initial_builders == 0: break
                upgraded = self.home_upgrade()
                time.sleep(0.5)
                final_builders = get_home_builders(1)
                if upgraded is not None:
                    if final_builders < initial_builders: upgrades_started.append(upgraded)
                    elif final_builders == initial_builders and upgraded != "wall": break
                else: break
            except:
                pass
        
        # Lab upgrades
        lab_upgrades_started = []
        try:
            if self.home_lab_available(1):
                upgraded = self.home_lab_upgrade()
                time.sleep(0.5)
                final_lab_avail = self.home_lab_available(1)
                if upgraded is not None and not final_lab_avail: lab_upgrades_started.append(upgraded)
        except:
            pass
        
        for upgrade in upgrades_started + lab_upgrades_started:
            send_notification(f"Started upgrading {upgrade}")
    
    def run_builder_base(self):
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_down()
        
        # Building upgrades
        upgrades_started = []
        counter = 0
        while counter < MAX_UPGRADES_PER_CHECK:
            counter += 1
            try:
                initial_builders = get_builder_builders(1)
                if initial_builders == 0: break
                upgraded = self.builder_upgrade()
                time.sleep(0.5)
                final_builders = get_builder_builders(1)
                if upgraded is not None:
                    if final_builders < initial_builders: upgrades_started.append(upgraded)
                    elif final_builders == initial_builders and upgraded != "wall": break
                else: break
            except:
                pass
        
        # Lab upgrades
        lab_upgrades_started = []
        try:
            if self.builder_lab_available(1):
                upgraded = self.builder_lab_upgrade()
                time.sleep(0.5)
                final_lab_avail = self.builder_lab_available(1)
                if upgraded is not None and not final_lab_avail: lab_upgrades_started.append(upgraded)
        except:
            pass
        
        for upgrade in upgrades_started + lab_upgrades_started:
            send_notification(f"Started upgrading {upgrade}")