import os
import cv2
import time
import numpy as np
import utils
from utils import *
from configs import *

class Attacker:
    def __init__(self):
        self.frame_handler = Frame_Handler()
        self.assets = self.load_assets()

    # ============================================================
    # 📁 Asset & Image Processing
    # ============================================================

    def load_assets(self):
        assets = {}
        for file in os.listdir(ATTACKER_ASSETS_DIR):
            assets[file.replace('.png', '')] = cv2.imread(os.path.join(ATTACKER_ASSETS_DIR, file), cv2.IMREAD_COLOR)
        return assets

    # ============================================================
    # 📱 Screen Interaction
    # ============================================================
    
    def click_attack(self):
        click(0.07, 0.9)
    
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
    # ⚔️ Attack Management
    # ============================================================

    def run(self, timeout=MAX_ATTACK_DURATION):
        zoom("out")
        
        for _ in range(MAX_ATTACKS_PER_CHECK):
            try:
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try: 
                        self.get_builders(1)
                        break
                    except: pass
                if time.time() - start_time >= timeout: break
                
                self.click_attack()
                
                # Find a match
                for _ in range(20):
                    time.sleep(0.5)
                    x, y = self.frame_handler.locate(self.assets["find_a_match"], thresh=0.9)
                    if x is not None and y is not None: break
                if x is None or y is None: return False
                click(x, y)
                
                found_match = False
                start_time = time.time()
                while time.time() - start_time < timeout:
                    time.sleep(0.5)
                    x, y = self.frame_handler.locate(self.assets["end_battle"], thresh=0.9)
                    if x is not None and y is not None:
                        found_match = True
                        break
                
                if found_match:
                    start_time = time.time()
                    swipe_up()
                    
                    n = 13
                    available_x = np.ones(n)
                    x_range = np.linspace(0, 1, num=n)
                    if EXCLUDE_CLAN_TROOPS:
                        x, y = self.frame_handler.locate(self.assets["clan_castle_deploy"], thresh=0.9)
                        if x is not None and y is not None:
                            w = self.assets["clan_castle_deploy"].shape[1] / WINDOW_DIMS[0]
                            available_x = np.where((x_range < (x - w/2)) | (x_range > (x + w/2)), 1, 0)
                    available_x, x_range = available_x[1:-1], x_range[1:-1]
                    available_x[EXCLUDE_ATTACK_SLOTS] = 0
                    for i in range(max(ATTACK_SLOT_RANGE[0], 0), min(ATTACK_SLOT_RANGE[1] + 1, 11)):
                        if available_x[i]:
                            click(x_range[i], 0.9)
                            # swipe(0.5, 0.8, 0.5, 0.8, TROOP_DEPLOY_TIME * 1000)
                            multi_click(0.5, 0.8, 0.5, 0.8, duration=TROOP_DEPLOY_TIME * 1000)

                    elapsed = time.time() - start_time
                    start_time = time.time()
                    return_home_found = False
                    while time.time() - start_time + elapsed < MAX_ATTACK_DURATION:
                        time.sleep(1)
                        x, y = self.frame_handler.locate(self.assets["return_home"], thresh=0.9)
                        if x is not None and y is not None:
                            click(x, y)
                            return_home_found = True
                            break
                    if return_home_found: continue
                    
                    # Surrender / End battle
                    for _ in range(5):
                        time.sleep(0.5)
                        x, y = self.frame_handler.locate(self.assets["surrender"], thresh=0.9)
                        if x is not None and y is not None:
                            click(x, y)
                            break
                        x, y = self.frame_handler.locate(self.assets["end_battle"], thresh=0.9)
                        if x is not None and y is not None:
                            click(x, y)
                            break
                        x, y = self.frame_handler.locate(self.assets["return_home"], thresh=0.9)
                        if x is not None and y is not None:
                            click(x, y)
                            return_home_found = True
                            break
                    if return_home_found: continue
                    
                    # Press okay
                    for _ in range(5):
                        time.sleep(0.5)
                        x, y = self.frame_handler.locate(self.assets["okay"], thresh=0.9)
                        if x is not None and y is not None:
                            click(x, y)
                            break
                        x, y = self.frame_handler.locate(self.assets["return_home"], thresh=0.9)
                        if x is not None and y is not None:
                            click(x, y)
                            return_home_found = True
                            break
                    if return_home_found: continue
                    
                    # Return home
                    for _ in range(10):
                        time.sleep(0.5)
                        x, y = self.frame_handler.locate(self.assets["return_home"], thresh=0.9)
                        if x is not None and y is not None:
                            click(x, y)
                            break
            
            except Exception as e:
                if DEBUG: print("start_attack", e)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                click_exit(5, 0.1)
                self.get_builders(1)
                break
            except Exception as e:
                if DEBUG: print("end_attack", e)