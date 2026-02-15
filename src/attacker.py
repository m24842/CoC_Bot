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
        
        # Wait until "end battle" button is found
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
        
        # Wait until "battle starts in" test is found
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(0.5)
            section = Frame_Handler.get_frame_section(0, 0, 1, 0.1, grayscale=True, high_contrast=True, thresh=150)
            x, y = Frame_Handler.locate(self.assets["battle_starts_in"], section, thresh=0.9)
            if x is not None and y is not None: return True
        return False
    
    def detect_troop_positions(self, frame, clip_left=0.0, clip_right=1.0, return_boundaries=False, return_types=False):
        # Look for vertical card edges
        if len(frame.shape) == 3: frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        frame = cv2.equalizeHist(frame)
        edges = cv2.convertScaleAbs(np.abs(cv2.Sobel(frame, cv2.CV_64F, 1, 0, ksize=3)))
        profile = np.sum(edges, axis=0)
        profile = (profile - profile.min()) / (profile.max() - profile.min())
        peaks = scipy.signal.find_peaks(profile, height=0.8, distance=10)[0]
        peaks_norm =  peaks / frame.shape[1]
        
        # Compute distances between edges and discretize
        dists = np.diff(peaks_norm)
        min_dist = dists.min()
        max_dist = dists.max()
        dist_categories = np.array([0.007, 0.015, 0.068])
        dists_discrete = dist_categories[np.argmin(np.abs(dists[:, None] - dist_categories), axis=1)]
        
        # Remove partially visible card edges
        if abs(dists[0] - min_dist) < abs(dists[0] - max_dist):
            peaks = peaks[1:]
            peaks_norm = peaks_norm[1:]
        if abs(dists[-1] - min_dist) < abs(dists[-1] - max_dist):
            peaks = peaks[:-1]
            peaks_norm = peaks_norm[:-1]
        
        assert len(peaks) % 2 == 0, "Uneven number of troop slot edges detected"
        
        # Convert edge distances to card locations
        card_types = []
        card_centers = []
        card_boundaries = []
        for i in range(0, len(peaks_norm), 2):
            x = (peaks_norm[i] + peaks_norm[i+1]) / 2
            if x >= clip_left and x <= clip_right:
                card_centers.append(x)
                card_boundaries.extend([peaks_norm[i], peaks_norm[i+1]])
                
                # Figure out whether card is a normal troop, clan troop, or hero
                card_section = frame[:, peaks[i]:peaks[i+1]]
                h, w = card_section.shape[:2]
                card_texture = cv2.Canny(card_section, 50, 150) / 255
                x_sign_loc = Frame_Handler.locate(self.assets["x"], card_section, grayscale=True, thresh=0.9, ref="lc")
                if x_sign_loc[0] is not None and x_sign_loc[1] is not None: # Only troops have multiplicity
                    prev_gap = dists_discrete[i-1] if i-1 > 0 else dist_categories[0]
                    next_gap = dists_discrete[i+1] if i+1 < len(dists_discrete) else dist_categories[0]
                    # Clan troops either have a clan badge rather than a smooth background
                    # or will have wider card edge gaps compared to typical troops
                    if max(card_texture[int(h*x_sign_loc[1])-10:int(h*x_sign_loc[1])+10, :int(w*x_sign_loc[0]-1)].mean(1)) > 0.1:
                        card_type = "clan"
                    elif prev_gap == dist_categories[1] and next_gap == dist_categories[1]:
                        card_type = "clan"
                    else: card_type = "troop"
                else:
                    card_type = "hero"
                card_types.append(card_type)
        
        card_centers = np.array(card_centers)
        
        if not return_boundaries and not return_types: return card_centers
        
        output = [card_centers]
        if return_boundaries: output.append(card_boundaries)
        if return_types: output.append(card_types)
        return output
    
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
    
    def complete_attack(self, timeout=10, restart=True, exclude_clan_troops=False):
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_up()
        
        total_slots_seen = 0
        last_card_left = 0.0
        
        while total_slots_seen < ATTACK_SLOT_RANGE[1] - ATTACK_SLOT_RANGE[0] + 1:
            frame = Frame_Handler.get_frame_section(0.0, 0.82, 1.0, 1.0, grayscale=False)
            # Find troops to deploy
            card_centers, card_boundaries, card_types = self.detect_troop_positions(frame, clip_left=last_card_left, return_boundaries=True, return_types=True)

            if len(card_centers) == 0: break

            # Exclude clan troops if specified
            available_slots = np.ones_like(card_centers)
            if exclude_clan_troops:
                for i, card_type in enumerate(card_types):
                    if card_type == "clan": available_slots[i] = 0
            
            # Exclude troops outside of specified slot range
            available_slots[:max(0, ATTACK_SLOT_RANGE[0] - total_slots_seen)] = 0
            available_slots[max(0, ATTACK_SLOT_RANGE[1] + 1 - total_slots_seen):] = 0
            
            # Deploy troops up until the last one visible
            total_slots_seen += len(card_centers) - 1
            self.deploy_troops(card_centers[:-1], available_slots[:-1])
            # Scroll over and look for the new position of the last card
            last_card_frame = frame[:, int(card_boundaries[-2] * frame.shape[1]):int(card_boundaries[-1] * frame.shape[1])]
            Input_Handler.swipe_left(x1=card_centers[-1], x2=0.038, y=0.9, hold_end_time=500)
            time.sleep(0.5)
            frame = Frame_Handler.get_frame_section(0.0, 0.82, 1.0, 1.0, grayscale=False)
            last_card_left = Frame_Handler.locate(last_card_frame, frame, thresh=0.9, grayscale=False, ref="lc")[0]
            # If the card didn't move then there are no more troops so it can be deployed
            if last_card_left is not None and abs(last_card_left - card_boundaries[-2]) < 0.01:
                self.deploy_troops(card_centers[-1:], available_slots[-1:])
                break
            elif last_card_left is None:
                break
        
        # Close and reopen CoC to auto complete battle
        if restart:
            start_coc()

            # Wait until back in one of the villages before returning
            start_time = time.time()
            while time.time() - start_time < timeout:
                Input_Handler.click_exit(5, 0.1)
                try:
                    get_home_builders(1)
                    return
                except Exception as e:
                    if configs.DEBUG: print("end_attack", e)
                
                try:
                    get_builder_builders(1)
                    return
                except Exception as e:
                    if configs.DEBUG: print("end_attack", e)
        else:
            stop_coc()
    
    # ============================================================
    # ⚔️ Attack Management
    # ============================================================

    @require_exit()
    def run_home_base(self, timeout=60, restart=True):
        try:
            # Make sure in home base
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    get_home_builders(1)
                    break
                except: pass
            if time.time() - start_time >= timeout: return
            
            # Complete an attack
            if self.start_normal_attack(timeout):
                self.complete_attack(timeout, restart=restart, exclude_clan_troops=EXCLUDE_CLAN_TROOPS)
        
        except Exception as e:
            if configs.DEBUG: print("attack_home_base", e)

    @require_exit()
    def run_builder_base(self, timeout=60, restart=True):
        try:
            # Make sure in builder base
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    get_builder_builders(1)
                    break
                except: pass
            if time.time() - start_time >= timeout: return
            
            # Complete an attack
            if self.start_builder_attack(timeout):
                self.complete_attack(timeout, restart=restart, exclude_clan_troops=False)
        
        except Exception as e:
            if configs.DEBUG: print("attack_builder_base", e)