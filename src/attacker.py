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
        import time
        
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
        import time
        
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
    
    def detect_troop_positions(self, frame, clip_left=0.0, clip_right=1.0, type_gaps_seen=0, return_boundaries=False, return_types=False, return_counts=False):
        import cv2, scipy, numpy as np
        
        # Look for vertical card edges
        assert len(frame.shape) == 3 and frame.shape[2] == 3
        frame_color = frame.copy()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        orig_h, orig_w = frame_gray.shape
        frame_color = frame_color[:, max(0, int(orig_w*clip_left)-10):min(orig_w, int(orig_w*clip_right)+10)]
        frame_gray = frame_gray[:, max(0, int(orig_w*clip_left)-10):min(orig_w, int(orig_w*clip_right)+10)]
        frame_gray = cv2.equalizeHist(frame_gray)
        edges = cv2.convertScaleAbs(np.abs(cv2.Sobel(frame_gray, cv2.CV_64F, 1, 0, ksize=3)))
        profile = np.sum(edges, axis=0)
        profile = (profile - profile.min()) / (profile.max() - profile.min())
        peaks = scipy.signal.find_peaks(profile, height=0.8, distance=10)[0]
        peaks_norm =  peaks / orig_w + clip_left
        
        # Compute distances between edges and discretize
        dists = np.diff(peaks_norm)
        dist_categories = np.array([0.007, 0.015, 0.068]) # normal gap, type change gap, card width
        tol = 0.01
        diffs = np.abs(dists[:, None] - dist_categories)
        closest_idx = np.argmin(diffs, axis=1)
        closest_dist = diffs[np.arange(len(dists)), closest_idx]
        dists_discrete = dist_categories[closest_idx]
        dists_discrete[closest_dist > tol] = np.nan
        
        # Remove partially visible card edges
        remove_left = 0
        remove_right = len(dists_discrete) - 1
        while dists_discrete[remove_left] != dist_categories[2]: remove_left += 1
        while dists_discrete[remove_right] != dist_categories[2]: remove_right -= 1
        peaks = peaks[remove_left:remove_right+2]
        peaks_norm = peaks_norm[remove_left:remove_right+2]
        dists_discrete = dists_discrete[remove_left:remove_right+1]
        
        assert len(peaks) % 2 == 0, "Uneven number of troop slot edges detected"
        
        # Convert edge distances to card locations
        card_types = []
        card_centers = []
        card_boundaries = []
        card_counts = []
        for i in range(0, len(peaks_norm), 2):
            x = (peaks_norm[i] + peaks_norm[i+1]) / 2
            card_centers.append(x)
            card_boundaries.extend([peaks_norm[i], peaks_norm[i+1]])
            prev_gap = dists_discrete[i-1] if i-1 > 0 else dist_categories[0]
            next_gap = dists_discrete[i+1] if i+1 < len(dists_discrete) else dist_categories[0]
            if prev_gap == dist_categories[1]: type_gaps_seen += 1
            
            # Figure out whether card is a normal troop, clan troop, or hero
            card_section = frame_color[:, peaks[i]:peaks[i+1]]
            card_section_gray = frame_gray[:, peaks[i]:peaks[i+1]]
            h, w = card_section_gray.shape[:2]
            card_texture = cv2.Canny(card_section_gray, 50, 150) / 255
            x_asset = render_text("x", "SupercellMagic", 25)
            x_h, x_w = x_asset.shape[:2]
            x_sign_loc = Frame_Handler.locate(x_asset, card_section_gray, grayscale=True, thresh=0.8, ref="lc")
            if x_sign_loc[0] is not None and x_sign_loc[1] is not None: # Only troops, clan troops, or spells have multiplicity
                count_section = card_section_gray[:int(h*x_sign_loc[1]+0.5*x_h)+1, int(w*x_sign_loc[0]+x_w)-1:]
                number_locs = Frame_Handler.batch_locate([render_text(str(n), "SupercellMagic", 25) for n in range(0, 12)], frame=count_section, grayscale=True, thresh=0.8, ref="cc")
                
                count = 1
                for i in reversed(range(0, 12)):
                    loc = number_locs[i]
                    if loc[0] is not None and loc[1] is not None:
                        count = i
                        break
                
                # Clan troops either have a clan badge rather than a smooth background
                # or will have wider card edge gaps compared to typical troops
                if max(card_texture[int(h*x_sign_loc[1])-10:int(h*x_sign_loc[1])+10, :int(w*x_sign_loc[0]-1)].mean(1)) > 0.1:
                    card_type = "clan"
                    card_counts.append(1)
                elif prev_gap == dist_categories[1] and next_gap == dist_categories[1]:
                    card_type = "clan"
                    card_counts.append(1)
                elif type_gaps_seen > 0:
                    card_type = "spell"
                    card_counts.append(count)
                else:
                    card_type = "troop"
                    card_counts.append(-1)
            else:
                card_section_border = card_section.copy()
                card_section_border[int(h*0.1):int(h*0.9), int(w*0.1):int(w*0.9)] = 0
                mask = filter_color((68, 202, 222), card_section_border, tol=100, return_mask=True)[1]
                blue_pct = mask.mean()
                # Seige machine doesn't have multiplicity anymore
                if blue_pct > 0.1:
                    card_type = "clan"
                    card_counts.append(1)
                else:
                    card_type = "hero"
                    card_counts.append(1)
            card_types.append(card_type)
        
        card_centers = np.array(card_centers)
                
        if not return_boundaries and not return_types: return card_centers
        
        output = [card_centers]
        if return_boundaries: output.append(card_boundaries)
        if return_types: output.append(card_types)
        if return_counts: output.append(card_counts)
        output.append(type_gaps_seen)
        return output
    
    def deploy_troops(self, card_centers, available_slots=None, card_types=None, card_counts=None):
        import time, numpy as np
        
        def card_gray(card_center):
            section = Frame_Handler.get_frame_section(card_center-0.01, 0.89, card_center+0.01, 0.91, grayscale=False)
            return np.all(section[:, :, 0] == section[:, :, 1]) and np.all(section[:, :, 1] == section[:, :, 2])
        
        if available_slots is None: available_slots = [1] * len(card_centers)
        if card_types is None: card_types = [None] * len(card_centers)
        if card_counts is None: card_counts = [0] * len(card_centers)
        
        # Start holding deploy position w/ secondary touch pointer
        Input_Handler.down(0.5, 0.8, pointer=1)
        
        for i in range(len(card_centers)):
            if available_slots[i]:
                # Select slot
                Input_Handler.click(card_centers[i], 0.9)
                
                # Deploy selected slot
                if card_types[i] in ["hero", "clan"]:
                    Input_Handler.click(0.5, 0.8)
                elif card_types[i] == "troop":
                    Input_Handler.down(0.5, 0.8, pointer=0)
                    end_time = time.monotonic() + TROOP_DEPLOY_TIME
                    while time.monotonic() < end_time and not card_gray(card_centers[i]): time.sleep(0.01)
                    Input_Handler.up(pointer=0)
                elif card_types[i] == "spell":
                    n = card_counts[i]
                    rxs = np.random.uniform(0.35, 0.65, n)
                    rys = np.random.uniform(0.45, 0.55, n)
                    for coord in zip(rxs, rys):
                        Input_Handler.click(*coord)
                else:
                    Input_Handler.click(0.5, 0.8, n=card_counts[i])
        
        # Release secondary pointer
        Input_Handler.up(pointer=1)
        
        # Unselect last card
        Input_Handler.click(0.01, 0.9)
    
    def complete_normal_attack(self, restart=True, exclude_clan_troops=False):
        import time, numpy as np
        
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_up()
        
        type_gaps_seen = 0
        total_slots_seen = 0
        last_card_left = 0.0
        
        while total_slots_seen < ATTACK_SLOT_RANGE[1] - ATTACK_SLOT_RANGE[0] + 1:
            frame = Frame_Handler.get_frame_section(0.0, 0.82, 1.0, 1.0, grayscale=False)
            # Find troops to deploy
            card_centers, card_boundaries, card_types, card_counts, type_gaps_seen = self.detect_troop_positions(frame, clip_left=last_card_left, type_gaps_seen=type_gaps_seen, return_boundaries=True, return_types=True, return_counts=True)
            
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
            self.deploy_troops(card_centers[:-1], available_slots[:-1], card_types[:-1], card_counts[:-1])
            # Scroll over and look for the new position of the last card
            last_card_frame = frame[:, int(card_boundaries[-2] * frame.shape[1]):int(card_boundaries[-1] * frame.shape[1])]
            Input_Handler.swipe_left(x1=card_centers[-1], x2=0.038, y=0.9, hold_end_time=500)
            time.sleep(0.5)
            frame = Frame_Handler.get_frame_section(0.0, 0.82, 1.0, 1.0, grayscale=False)
            last_card_left = Frame_Handler.locate(last_card_frame, frame, thresh=0.9, grayscale=False, ref="lc")[0]
            # If the card didn't move then there are no more troops so it can be deployed
            if last_card_left is not None and abs(last_card_left - card_boundaries[-2]) < 0.01:
                self.deploy_troops(card_centers[-1:], available_slots[-1:], card_types[-1:], card_counts[-1:])
                break
            elif last_card_left is None:
                break
        
        # Close and reopen CoC to auto complete battle
        if restart:
            start_coc()
        else:
            stop_coc()
    
    def complete_builder_attack(self, restart=True):
        import numpy as np
        
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_up()
        
        card_centers = np.linspace(0.1, 0.9, 11)
        self.deploy_troops(card_centers, card_counts=[4]*len(card_centers))
        
        # Close and reopen CoC to auto complete battle
        if restart:
            start_coc()
        else:
            stop_coc()
    
    # ============================================================
    # ⚔️ Attack Management
    # ============================================================

    @require_exit()
    def run_home_base(self, timeout=60, restart=True):
        import time
        
        try:
            # Make sure in home base
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    get_home_builders(1)
                    break
                except (KeyboardInterrupt, SystemExit): raise
                except: pass
            if time.time() - start_time >= timeout: return
            
            # Complete an attack
            if self.start_normal_attack(timeout):
                self.complete_normal_attack(restart=restart, exclude_clan_troops=EXCLUDE_CLAN_TROOPS)
        
        except Exception as e:
            if configs.DEBUG: print("attack_home_base", e)

    @require_exit()
    def run_builder_base(self, timeout=60, restart=True):
        import time
        
        try:
            # Make sure in builder base
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    get_builder_builders(1)
                    break
                except (KeyboardInterrupt, SystemExit): raise
                except: pass
            if time.time() - start_time >= timeout: return
            
            # Complete an attack
            if self.start_builder_attack(timeout):
                self.complete_builder_attack(restart=restart)
        
        except Exception as e:
            if configs.DEBUG: print("attack_builder_base", e)