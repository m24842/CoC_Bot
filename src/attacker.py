import os
import cv2
import time
import scipy
import numpy as np
from utils import *
import configs
from configs import *

class Attacker:
    def __init__(self):
        self.assets = Asset_Manager.attacker_assets

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
    
    def click_okay(self):
        x, y = Frame_Handler.locate(self.assets["okay"], thresh=0.9)
        if x is not None and y is not None:
            Input_Handler.click(x, y)
            return True
        return False
    
    def click_surrender(self):
        x, y = Frame_Handler.locate(self.assets["surrender"], thresh=0.9)
        if x is not None and y is not None:
            Input_Handler.click(x, y)
            return True
        return False
    
    def click_end_battle(self):
        x, y = Frame_Handler.locate(self.assets["end_battle"], thresh=0.9)
        if x is not None and y is not None:
            Input_Handler.click(x, y)
            return True
        return False
    
    def click_return_home(self):
        x, y = Frame_Handler.locate(self.assets["return_home"], thresh=0.9)
        if x is not None and y is not None:
            Input_Handler.click(x, y)
            return True
        return False
    
    def start_normal_attack(self, timeout=60):
        # Click attack
        Input_Handler.click(0.07, 0.9)
        
        # Find a match
        for _ in range(20):
            time.sleep(0.5)
            xys = Frame_Handler.locate(self.assets["find_a_match"], thresh=0.9, return_all=True)
            if len(xys) > 0: break
        if len(xys) == 0: return False
        xys = sorted(xys, key=lambda xy: xy[0])
        x, y = xys[0]
        if x > 0.2: return False
        Input_Handler.click(x, y)
        
        # Confirm attack
        for _ in range(20):
            time.sleep(0.5)
            x, y = Frame_Handler.locate(self.assets["confirm_attack"], thresh=0.9)
            if x is not None and y is not None: break
        if x is None or y is None: return False
        Input_Handler.click(x, y)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(0.5)
            x, y = Frame_Handler.locate(self.assets["end_battle"], thresh=0.9)
            if x is not None and y is not None: return True
        return False
    
    def start_builder_attack(self, timeout=60):
        # Click attack
        Input_Handler.click(0.07, 0.9)
        
        # Find a match
        for _ in range(20):
            time.sleep(0.5)
            x, y = Frame_Handler.locate(self.assets["find_now"], thresh=0.9)
            if x is not None and y is not None: break
        if x is None or y is None: return False
        Input_Handler.click(x, y)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(0.5)
            section = Frame_Handler.get_frame_section(0, 0, 1, 0.1, grayscale=True, high_contrast=True, thresh=150)
            x, y = Frame_Handler.locate(self.assets["battle_starts_in"], section, thresh=0.9)
            if x is not None and y is not None: return True
        return False
    
    def detect_troop_positions(self, frame, clip_left=0.0, clip_right=1.0, return_boundaries=False):
        if len(frame.shape) == 3: frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        frame = cv2.equalizeHist(frame)
        sobelx = cv2.Sobel(frame, cv2.CV_64F, 1, 0, ksize=3)
        abs_sobelx = np.abs(sobelx)
        edges = cv2.convertScaleAbs(abs_sobelx)
        profile = np.sum(edges, axis=0)
        profile = (profile - profile.min()) / (profile.max() - profile.min())
        peaks = scipy.signal.find_peaks(profile, height=0.8, distance=10)[0] / frame.shape[1]
        
        if configs.DEBUG:
            debug_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            for x in (peaks * frame.shape[1]).astype(int):
                cv2.line(debug_frame, (x, 0), (x, frame.shape[0]), (0, 255, 0), 2)
            Frame_Handler.save_frame(debug_frame, "debug/troop_detection.png")
        
        dists = np.diff(peaks)
        min_dist = dists.min()
        max_dist = dists.max()
        
        if abs(dists[0] - min_dist) < abs(dists[0] - max_dist): peaks = peaks[1:]
        if abs(dists[-1] - min_dist) < abs(dists[-1] - max_dist): peaks = peaks[:-1]
        
        assert len(peaks) % 2 == 0, "Uneven number of troop slot edges detected"
        
        card_centers = []
        card_boundaries = []
        for i in range(0, len(peaks), 2):
            x = (peaks[i] + peaks[i+1]) / 2
            if x >= clip_left and x <= clip_right:
                card_centers.append(x)
                card_boundaries.extend([peaks[i], peaks[i+1]])
        
        card_centers = np.array(card_centers)
        
        if return_boundaries:
            return card_centers, card_boundaries
        return card_centers
    
    def deploy_troops(self, card_centers, available_slots):
        for i in range(len(card_centers)):
            if available_slots[i]:
                # Select troop
                Input_Handler.click(card_centers[i], 0.9)
                
                # Random deployment for spells
                n = 10
                rxs = np.random.uniform(0.35, 0.65, n)
                rys = np.random.uniform(0.45, 0.55, n)
                for coord in zip(rxs, rys): Input_Handler.click(*coord)
                
                # Deploy troop
                Input_Handler.multi_click(0.5, 0.8, 0.5, 0.8, duration=TROOP_DEPLOY_TIME * 1000)
        Input_Handler.click(0.01, 0.9)
    
    def complete_attack(self, timeout=10, restart=True):
        Input_Handler.swipe_up()
        
        total_slots_seen = 0
        no_more_slots = False
        last_card_left = 0.0
        
        while total_slots_seen < ATTACK_SLOT_RANGE[1] + 1 and not no_more_slots:
            frame = Frame_Handler.get_frame_section(0.0, 0.82, 1.0, 1.0, grayscale=False)
            card_centers, card_boundaries = self.detect_troop_positions(frame, clip_left=last_card_left, return_boundaries=True)

            # Determine troops to use
            available_slots = np.ones_like(card_centers)
            if EXCLUDE_CLAN_TROOPS:
                frame_gray = Frame_Handler.get_frame_section(0.0, 0.82, 1.0, 1.0, grayscale=True)
                x, y = Frame_Handler.locate(self.assets["clan_castle_deploy"], frame=frame_gray, thresh=0.9)
                if x is not None and y is not None:
                    diffs = np.abs(card_centers - x)
                    if min(diffs) < 0.01:
                        closest_idx = np.argmin(diffs)
                        available_slots[closest_idx] = 0
                locs = Frame_Handler.locate(self.assets["clan_castle_icon"], frame=frame_gray, thresh=0.9, return_all=True)
                for x, y in locs:
                    diffs = np.abs(card_centers - (x + 0.01))
                    if min(diffs) < 0.01:
                        closest_idx = np.argmin(diffs)
                        available_slots[closest_idx] = 0
            
            if len(EXCLUDE_ATTACK_SLOTS) and min(np.array(EXCLUDE_ATTACK_SLOTS) - total_slots_seen) >= 0 and max(np.array(EXCLUDE_ATTACK_SLOTS) - total_slots_seen) < len(available_slots):
                available_slots[np.array(EXCLUDE_ATTACK_SLOTS) - total_slots_seen] = 0
            available_slots[:ATTACK_SLOT_RANGE[0] - total_slots_seen] = 0
            available_slots[ATTACK_SLOT_RANGE[1] + 1 - total_slots_seen:] = 0
            
            # Deploy troops
            if len(card_centers) < 12:
                no_more_slots = True
                total_slots_seen += len(card_centers)
                self.deploy_troops(card_centers, available_slots)
            else:
                total_slots_seen += len(card_centers) - 1
                self.deploy_troops(card_centers[:-1], available_slots[:-1])
                last_card_frame = frame[:, int(card_boundaries[-2] * frame.shape[1]):int(card_boundaries[-1] * frame.shape[1])]
                Input_Handler.swipe_left(x1=card_centers[-1], x2=0.038, y=0.9, hold_end_time=500)
                time.sleep(0.5)
                frame = Frame_Handler.get_frame_section(0.0, 0.82, 1.0, 1.0, grayscale=False)
                last_card_left = Frame_Handler.locate(last_card_frame, frame, thresh=0.9, grayscale=False, ref="lc")[0]
                if abs(last_card_left - card_boundaries[-2]) < 0.01: no_more_slots = True
        
        # Close and reopen CoC to auto complete battle
        if restart:
            start_coc()

            start_time = time.time()
            while time.time() - start_time < timeout:
                Input_Handler.click_exit(5, 0.1)
                try:
                    get_home_builders(1)
                    break
                except Exception as e:
                    if configs.DEBUG: print("end_attack", e)
                
                try:
                    get_builder_builders(1)
                    break
                except Exception as e:
                    if configs.DEBUG: print("end_attack", e)
        else:
            stop_coc()
    
    # ============================================================
    # ⚔️ Attack Management
    # ============================================================

    @require_exit()
    def run_home_base(self, timeout=60, restart=True):
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_down()
        
        for _ in range(1):
            try:
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        get_home_builders(1)
                        break
                    except: pass
                if time.time() - start_time >= timeout: break
                
                found_match = self.start_normal_attack(timeout)
                
                if found_match: self.complete_attack(timeout, restart=restart)
            
            except Exception as e:
                if configs.DEBUG: print("start_attack", e)

    @require_exit()
    def run_builder_base(self, timeout=60, restart=True):
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_down()
        
        for _ in range(1):
            try:
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        get_builder_builders(1)
                        break
                    except: pass
                if time.time() - start_time >= timeout: break
                
                found_match = self.start_builder_attack(timeout)
                
                if found_match: self.complete_attack(timeout, restart=restart)
            
            except Exception as e:
                if configs.DEBUG: print("start_attack", e)