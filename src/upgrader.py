from utils import *
import configs
from configs import *

class Upgrader:
    
    hero_names = [
        "Barbarian King",
        "Archer Queen",
        "Minion Prince",
        "Grand Warden",
        "Royal Champion",
        "Dragon Duke"
    ]
    
    def __init__(self):
        self.assets = Asset_Manager.upgrader_assets

    # ============================================================
    # 📱 Screen Interaction
    # ============================================================
    
    def _click_home_builders(self):
        Input_Handler.click(0.5, 0.05)
    
    def _click_home_lab(self):
        Input_Handler.click(0.4, 0.05)

    def _click_builder_builders(self):
        Input_Handler.click(0.6, 0.05)
    
    def _click_builder_lab(self):
        Input_Handler.click(0.45, 0.05)

    # ============================================================
    # 💰 Resource & Builder Tracking
    # ============================================================

    def get_resources(self, timeout=60):
        import time
        
        start = time.time()
        while time.time() < start + timeout:
            try:
                section = Frame_Handler.get_frame_section(0.8, 0, 0.96, 0.30, high_contrast=True, thresh=240)
                if configs.DEBUG: Frame_Handler.save_frame(section, "debug/resources.png")
                text = OCR_Handler.get_text(section)
                if configs.DEBUG: print(text)
                gold, elixir, dark_elixir = [int(fix_digits(s.replace(' ', ''))) for s in text]
                return {"gold": gold, "elixir": elixir, "dark_elixir": dark_elixir}
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                if configs.DEBUG: print("get_resources", e)
            time.sleep(0.5)
        raise Exception("Failed to get resources")

    def home_lab_available(self, timeout=60):
        import time, cv2
        
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
                text = fix_digits(''.join(OCR_Handler.get_text(section)).replace(' ', '').replace('/', ''))
                available = int(text[0])
                return available > 0
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                if configs.DEBUG: print("home_lab_available", e)
            time.sleep(0.5)
        raise Exception("Failed to get home lab availability")

    def builder_lab_available(self, timeout=60):
        import time, cv2
        
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
                text = fix_digits(''.join(OCR_Handler.get_text(section)).replace(' ', '').replace('/', ''))
                available = int(text[0])
                return available > 0
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                if configs.DEBUG: print("builder_lab_available", e)
            time.sleep(0.5)
        raise Exception("Failed to get builder lab availability")

    def collect_resources(self):
        import numpy as np
        try:
            x_range = np.linspace(0.2, 0.8, 20)
            y_range = np.linspace(0.3, 0.8, 20)
            for x in x_range:
                for y in y_range:
                    Input_Handler.click(x, y)
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("collect_resources", e)

    def collect_builder_attack_elixir(self):
        import time
        
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

    def _get_suggested_upgrade_template(self):
        template = render_text("Suggested upgrades:", "CCBackBeat", 27, color=(211, 253, 127))
        h, w = template.shape[:2]
        return template, w / WINDOW_DIMS[0], h / WINDOW_DIMS[1]

    def _get_other_upgrade_template(self):
        template = render_text("Other upgrades:", "CCBackBeat", 27, color=(211, 253, 127))
        h, w = template.shape[:2]
        return template, w / WINDOW_DIMS[0], h / WINDOW_DIMS[1]

    def _get_upgrade_menu(self, frame, sug_loc, sug_width, return_bounds=False):
        x_sug, y_sug = sug_loc
        menu_top = 0.15
        menu_left = x_sug - 0.5*sug_width
        menu_right = x_sug + 0.5*sug_width + 0.11
        menu = Frame_Handler.crop(frame, menu_left, y_sug, menu_right, 1.0)
        menu_high_contrast = Frame_Handler.high_contrast(menu, thresh=255) / 255
        menu_bottom = y_sug + menu_high_contrast.mean(axis=1).argmax() / WINDOW_DIMS[1]
        menu = Frame_Handler.crop(frame, menu_left, menu_top, menu_right, menu_bottom)
        if return_bounds: return menu, menu_left, menu_top, menu_right, menu_bottom
        return menu

    def _get_potential_upgrade_locs(self, menu):
        import numpy as np
        
        def filter_color(frame, color, tol=10):
            color = np.array(color).reshape((1, 1, 3))
            mask = (np.abs(frame - color).sum(axis=2) <= tol)
            frame = np.where(mask, 255, 0)
            return frame
        
        def profile_bounds(profile):
            bounds = []
            prev_val = 0
            for i, val in enumerate(profile):
                if prev_val == 0 and val == 1:
                    bounds.append(i)
                if prev_val == 1 and val == 0:
                    bounds.append(i)
                prev_val = val
            if prev_val == 1:
                bounds.append(len(profile))
            bounds = np.array(bounds).reshape((-1, 2))
            centers = (bounds[:, 0] + bounds[:, 1]) / 2
            return bounds, centers
        
        menu_white = filter_color(menu, [255, 255, 255], tol=0) / 255
        menu_red = filter_color(menu, (255, 136, 127), tol=10) / 255
        white_profile = np.where(menu_white.mean(axis=1) > 0.01, 1, 0)
        red_profile = np.where(menu_red.mean(axis=1) > 0.01, 1, 0)
        white_bounds, white_centers = profile_bounds(white_profile)
        red_bounds, red_centers = profile_bounds(red_profile)
        potential_y_locs = [] # in pixels
        for wc in white_centers:
            if len(red_centers) == 0 or abs(red_centers - wc).min() > 12.5:
                potential_y_locs.append(wc)
        return potential_y_locs

    def _find_builder_confirm(self):
        import cv2, numpy as np
        from scipy.ndimage import gaussian_filter1d
        thresh = 0.2
        section = Frame_Handler.get_frame_section(0.0, 0.9, 1.0, 0.92, grayscale=False)
        section = cv2.cvtColor(section, cv2.COLOR_RGB2LAB).astype(np.float32)
        btn_color = cv2.cvtColor(np.array([[[189, 230, 76]]], dtype=np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
        diff = np.linalg.norm((section - btn_color)/255, axis=2).mean(0)
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
        return x, y
    
    def _scroll_locate_upgrade(self, locate_template_func, menu_left, menu_right, menu_top, menu_bottom, dir="down"):
        # First two return values of locate_template_func should be x and y of located template
        import time, numpy as np
        menu_center = (menu_left + menu_right) / 2
        res = locate_template_func()
        if res[0] is None or res[1] is None:
            prev_section = Frame_Handler.get_frame_section(menu_left, menu_top, menu_right, menu_bottom, high_contrast=True, thresh=255)
            for _ in range(20):
                if dir == "down":
                    y1, y2 = menu_bottom-0.05, menu_top+0.05
                elif dir == "up":
                    y1, y2 = menu_top+0.05, menu_bottom-0.05
                Input_Handler.swipe(x1=menu_center, y1=y1, x2=menu_center, y2=y2, duration=0, hold_end_time=100, inter_points=10)
                time.sleep(0.1)
                
                # Check if at end of upgrade menu
                section = Frame_Handler.get_frame_section(menu_left, menu_top, menu_right, menu_bottom, high_contrast=True, thresh=255)
                diff = np.abs(section - prev_section).mean() / 255
                if diff < 0.01: break
                prev_section = section
                
                res = locate_template_func()
                if res[0] is not None and res[1] is not None: break
        return res
    
    @require_exit()
    def home_random_upgrade(self):
        import time, re, numpy as np

        try:
            # Open upgrade list menu
            self._click_home_builders()
            time.sleep(0.5)
            
            # Locate menu boundaries
            sug_template, sug_width, sug_height = self._get_suggested_upgrade_template()
            x_sug, y_sug = Frame_Handler.locate(sug_template, thresh=0.70, grayscale=False)
            if x_sug is None or y_sug is None: return None
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=True)
            menu, menu_left, menu_top, menu_right, menu_bottom = self._get_upgrade_menu(frame, (x_sug, y_sug), sug_width, return_bounds=True)
            menu_center = (menu_left + menu_right) / 2
            if configs.START_FROM_MENU_TOP:
                Input_Handler.swipe_up(x=x_sug, y1=y_sug, y2=0.15, duration=0, hold_end_time=100, inter_points=10)
            else:
                for _ in range(5): Input_Handler.swipe_up(x=x_sug, y1=menu_bottom-0.05, y2=0.15, duration=0, hold_end_time=0, inter_points=10)
            menu = Frame_Handler.get_frame_section(menu_left, menu_top, menu_right, menu_bottom, grayscale=False)
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=True)
            
            # Find a valid upgrade
            potential_y_locs = self._get_potential_upgrade_locs(menu)
            town_hall_template = [render_text("Town Hall", "CCBackBeat", 27)]
            hero_templates = [render_text(hero, "SupercellMagic", 19) for hero in self.hero_names]
            locs = Frame_Handler.batch_locate(town_hall_template + hero_templates, thresh=0.80, ref="lc", null_val=-1)
            town_hall_loc = locs[0:1]
            hero_locs = locs[1:]
            invalid_locs = town_hall_loc
            if Task_Handler.heroes_excluded():
                invalid_locs += hero_locs
            invalid_y_locs = np.array(invalid_locs)[:, 1]
            hero_y_locs = np.array(hero_locs)[:, 1]
            
            # Choose an upgrade
            chosen_upgrade = None
            x_upgrade, y_upgrade = None, None
            for y_loc in np.random.permutation(potential_y_locs):
                y = menu_top + y_loc / WINDOW_DIMS[1]
                if min(abs(invalid_y_locs - y)) > 0.02:
                    x_upgrade = menu_center
                    y_upgrade = y
                    hero_dists = abs(hero_y_locs - y)
                    if min(hero_dists) < 0.02:
                        chosen_upgrade = self.hero_names[hero_dists.argmin()]
                    break
            if x_upgrade is None or y_upgrade is None:
                # If no valid upgrades found but town hall is found, then upgrade it
                if invalid_y_locs[0] != -1:
                    x_upgrade, y_upgrade = menu_center, invalid_y_locs[0]
                else: return None
            Input_Handler.click(x_upgrade, y_upgrade)
            time.sleep(0.5)
            
            in_hero_hall = Frame_Handler.locate(render_text("Hero Hall", "SupercellMagic", 28), thresh=0.80)[0] is not None
            if in_hero_hall:
                if Task_Handler.heroes_excluded(): return None
            else:
                self._click_home_builders()
            time.sleep(0.5)
            
            # Find upgrade button
            upgrade_template = self.assets["upgrade"]
            x, y = Frame_Handler.locate(upgrade_template, thresh=0.90, grayscale=False)
            if in_hero_hall:
                # chosen_upgrade should be a hero
                if chosen_upgrade is None: return None
                hero_name_template = render_text(chosen_upgrade, "SupercellMagic", 19)
                xy_hero = Frame_Handler.locate(hero_name_template, thresh=0.60)
                if xy_hero[0] is None or xy_hero[1] is None:
                    Input_Handler.swipe_left(y=0.5)
                    time.sleep(0.5)
                    xy_hero = Frame_Handler.locate(hero_name_template, thresh=0.60)
                if xy_hero[0] is None or xy_hero[1] is None: return None
                
                hero_upgrade_template = render_text("Upgrade", "SupercellMagic", 17)
                xy_hero_upgrade = Frame_Handler.locate(hero_upgrade_template, thresh=0.70, return_all=True, use_cached=True)
                xy_hero_upgrade = sorted(xy_hero_upgrade, key=lambda pair: abs(pair[0] - xy_hero[0]))
                if len(xy_hero_upgrade) > 0: x, y = xy_hero_upgrade[0]
            if x is None or y is None: return None
            
            # Click upgrade
            Input_Handler.click(x, y)
            time.sleep(0.5)
            
            # Get upgrade name
            x, y = Frame_Handler.locate(self.assets["upgrade_name"], ref="lc", thresh=0.9)
            section = Frame_Handler.get_frame_section(x+0.122, y-0.04, 1-x, y+0.035, high_contrast=True, thresh=255, use_cached=True)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/upgrade_name.png")
            upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", OCR_Handler.get_text(section)[0].lower()[:-3]))
            
            # Click confirm button
            x, y = Frame_Handler.locate(self.assets["confirm"], grayscale=False, thresh=0.85, use_cached=True)
            if x is None or y is None: return None
            Input_Handler.click(x, y+0.05)
            time.sleep(0.5)
            return upgrade_name
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("home_random_upgrade", e)
            return None

    @require_exit()
    def home_specified_upgrade(self, upgrade_text):
        import time, re, numpy as np
        
        try:
            # Open upgrade list menu
            self._click_home_builders()
            time.sleep(0.5)
            
            # Find suggested upgrades label
            sug_template, sug_width, sug_height = self._get_suggested_upgrade_template()
            x_sug, y_sug = Frame_Handler.locate(sug_template, thresh=0.70, grayscale=False)
            if x_sug is None or y_sug is None: return None
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=True)
            menu, menu_left, menu_top, menu_right, menu_bottom = self._get_upgrade_menu(frame, (x_sug, y_sug), sug_width, return_bounds=True)
            
            # Find other upgrades label
            other_template = self._get_other_upgrade_template()[0]
            x_other, y_other = Frame_Handler.locate(other_template, thresh=0.70, grayscale=False)
            
            # Move ongoing upgrades out of view
            if configs.START_FROM_MENU_TOP:
                Input_Handler.swipe_up(x=x_sug, y1=y_sug, y2=0.15, duration=0, hold_end_time=100, inter_points=10)
            else:
                for _ in range(5): Input_Handler.swipe_up(x=x_sug, y1=menu_bottom-0.05, y2=0.15, duration=0, hold_end_time=0, inter_points=10)
            
            # Find upgrade text
            if type(upgrade_text) == str: upgrade_text = [upgrade_text]
            if Task_Handler.heroes_excluded():
                upgrade_text = list(set(upgrade_text) - set(self.hero_names))
            templates = [render_text(text, "CCBackBeat", 27) for text in upgrade_text]
            combined = list(zip(templates, upgrade_text))
            np.random.shuffle(combined)
            templates, upgrade_text = zip(*combined)
            
            def locate_template(templates, names):
                frame = Frame_Handler.get_frame(grayscale=False)
                frame_gray = Frame_Handler.grayscale(frame)
                x_sug, y_sug = Frame_Handler.locate(sug_template, frame, thresh=0.70, grayscale=False)
                res = Frame_Handler.batch_locate(templates, frame_gray, thresh=0.80, ref="lc", return_all=True)
                for items, name in zip(res, names):
                    for x, y in items:
                        if x is not None and y is not None and (y_sug is None or (y_sug is not None and y > y_sug)):
                            section = Frame_Handler.crop(frame, menu_left, y-0.02, menu_right, y+0.02)
                            sufficient_resources = not check_color((255, 136, 127), section, tol=10)
                            if sufficient_resources:
                                # Check that located upgrade name is left aligned
                                if abs(x - menu_left) < 0.01:
                                    return x, y, name
                                # Or if it is left aligned to "New" label
                                new_x, new_y = Frame_Handler.locate(render_text("New", "CCBackBeat", 27, color=(13, 255, 13)), filter_color((13, 255, 13), section), thresh=0.70, grayscale=False, ref="rc")
                                if new_x is not None and new_y is not None and abs(x - (menu_left + new_x/section.shape[1])) < 0.05:
                                    return x, y, name
                return None, None, None
            
            x, y, upgrade_name = self._scroll_locate_upgrade(
                lambda: locate_template(templates, upgrade_text),
                menu_left,
                menu_right,
                menu_top,
                menu_bottom,
                dir="down" if configs.START_FROM_MENU_TOP else "up",
            )
            
            if x is None or y is None: return None
            Input_Handler.click(x_sug, y)
            time.sleep(0.5)
            
            in_hero_hall = Frame_Handler.locate(render_text("Hero Hall", "SupercellMagic", 28), thresh=0.80)[0] is not None
            if in_hero_hall:
                if Task_Handler.heroes_excluded(): return None
            else:
                self._click_home_builders()
            time.sleep(0.5)
            
            # Find upgrade button
            upgrade_template = self.assets["upgrade"]
            x, y = Frame_Handler.locate(upgrade_template, thresh=0.90, grayscale=False)
            if in_hero_hall:
                hero_name_template = render_text(upgrade_name, "SupercellMagic", 19)
                xy_hero = Frame_Handler.locate(hero_name_template, thresh=0.60)
                if xy_hero[0] is None or xy_hero[1] is None:
                    Input_Handler.swipe_left(y=0.5)
                    time.sleep(0.5)
                    xy_hero = Frame_Handler.locate(hero_name_template, thresh=0.60)
                if xy_hero[0] is None or xy_hero[1] is None: return None
                
                hero_upgrade_template = render_text("Upgrade", "SupercellMagic", 17)
                xy_hero_upgrade = Frame_Handler.locate(hero_upgrade_template, thresh=0.70, return_all=True)
                xy_hero_upgrade = sorted(xy_hero_upgrade, key=lambda pair: abs(pair[0] - xy_hero[0]))
                if len(xy_hero_upgrade) > 0: x, y = xy_hero_upgrade[0]
            if x is None or y is None: return None
            
            # Click upgrade
            Input_Handler.click(x, y)
            time.sleep(0.5)
            
            # Get upgrade name
            x, y = Frame_Handler.locate(self.assets["upgrade_name"], ref="lc", thresh=0.9)
            section = Frame_Handler.get_frame_section(x+0.122, y-0.04, 1-x, y+0.035, high_contrast=True, thresh=255, use_cached=True)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/upgrade_name.png")
            upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", OCR_Handler.get_text(section)[0].lower()[:-3]))
            
            # Click confirm button
            x, y = Frame_Handler.locate(self.assets["confirm"], grayscale=False, thresh=0.85, use_cached=True)
            if x is None or y is None: return None
            Input_Handler.click(x, y+0.05)
            time.sleep(0.5)
            return upgrade_name
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("home_specified_upgrade", e)
            return None
    
    @require_exit()
    def home_upgrade(self):
        if not Task_Handler.home_base_priority_excluded():
            for priority_level in configs.HOME_BASE_UPGRADE_PRIORITY:
                upgrade_name = self.home_specified_upgrade(priority_level)
                if upgrade_name is not None: return upgrade_name
        return self.home_random_upgrade()
    
    @require_exit()
    def assign_builder_apprentice(self):
        import time
        
        try:
            # Open upgrade list menu
            self._click_home_builders()
            time.sleep(0.5)
            
            # Find assistant available label
            xys = Frame_Handler.locate(self.assets["assistant_available"], thresh=0.8, return_all=True)
            xys = sorted(xys, key=lambda pair: pair[1])
            if len(xys) == 0: return
            x, y = xys[0]

            Input_Handler.click(x, y)
            time.sleep(0.5)
            
            # Find assign assistant label
            xys = Frame_Handler.locate(self.assets["assign_assistant"], thresh=0.9, grayscale=False, return_all=True)
            if xys is None: return
            
            x, y = sorted(xys, key=lambda pair: pair[1])[0]
            
            Input_Handler.click(x, y)
            time.sleep(0.5)
            
            # Find confirm button
            x, y = Frame_Handler.locate(self.assets["confirm_assistant"], grayscale=False, thresh=0.9)
            if x is None or y is None: return
            
            Input_Handler.click(x, y)
            time.sleep(0.5)
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("assign_builder_apprentice", e)
    
    @require_exit()
    def home_lab_random_upgrade(self):
        import time, re, numpy as np
        
        try:
            # Open lab upgrade list menu
            self._click_home_lab()
            time.sleep(0.5)
            
            # Locate menu boundaries
            sug_template, sug_width, sug_height = self._get_suggested_upgrade_template()
            x_sug, y_sug = Frame_Handler.locate(sug_template, thresh=0.70, grayscale=False)
            if x_sug is None or y_sug is None: return None
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=True)
            menu, menu_left, menu_top, menu_right, menu_bottom = self._get_upgrade_menu(frame, (x_sug, y_sug), sug_width, return_bounds=True)
            menu_center = (menu_left + menu_right) / 2
            if configs.START_FROM_MENU_TOP:
                Input_Handler.swipe_up(x=x_sug, y1=y_sug, y2=0.15, duration=0, hold_end_time=100, inter_points=10)
            else:
                for _ in range(5): Input_Handler.swipe_up(x=x_sug, y1=menu_bottom-0.05, y2=0.15, duration=0, hold_end_time=0, inter_points=10)
            menu = Frame_Handler.get_frame_section(menu_left, menu_top, menu_right, menu_bottom, grayscale=False)
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=True)
            
            # Find a valid upgrade
            potential_y_locs = self._get_potential_upgrade_locs(menu)

            # Choose an upgrade
            if len(potential_y_locs) == 0: return None
            x_upgrade, y_upgrade = menu_center, menu_top + np.random.choice(potential_y_locs) / WINDOW_DIMS[1]
            Input_Handler.click(x_upgrade, y_upgrade)
            time.sleep(0.5)
            
            # Get upgrade name
            x, y = Frame_Handler.locate(self.assets["upgrade_name"], ref="lc", thresh=0.9)
            section = Frame_Handler.get_frame_section(x+0.122, y-0.04, 1-x, y+0.035, high_contrast=True, thresh=255, use_cached=True)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/lab_upgrade_name.png")
            upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", OCR_Handler.get_text(section)[0].lower()[:-3]))
            
            # Click confirm button
            x, y = Frame_Handler.locate(self.assets["confirm"], grayscale=False, thresh=0.85, use_cached=True)
            if x is None or y is None: return None
            Input_Handler.click(x, y+0.05)
            time.sleep(0.5)
            return upgrade_name
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("home_lab_upgrade", e)
            return None
    
    @require_exit()
    def home_lab_specified_upgrade(self, upgrade_text):
        import time, re, numpy as np
        
        try:
            # Open lab upgrade list menu
            self._click_home_lab()
            time.sleep(0.5)
            
            # Find suggested upgrades label
            sug_template, sug_width, sug_height = self._get_suggested_upgrade_template()
            x_sug, y_sug = Frame_Handler.locate(sug_template, thresh=0.70, grayscale=False)
            if x_sug is None or y_sug is None: return None
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=True)
            menu, menu_left, menu_top, menu_right, menu_bottom = self._get_upgrade_menu(frame, (x_sug, y_sug), sug_width, return_bounds=True)
            
            # Find other upgrades label
            other_template = self._get_other_upgrade_template()[0]
            x_other, y_other = Frame_Handler.locate(other_template, thresh=0.70, grayscale=False)
            if y_other is not None: menu_ref_pos = y_other
            else: menu_ref_pos = y_sug
            
            # Move ongoing upgrades out of view
            if configs.START_FROM_MENU_TOP:
                Input_Handler.swipe_up(x=x_sug, y1=y_sug, y2=0.15, duration=0, hold_end_time=100, inter_points=10)
            else:
                for _ in range(5): Input_Handler.swipe_up(x=x_sug, y1=menu_bottom-0.05, y2=0.15, duration=0, hold_end_time=0, inter_points=10)
            
            # Find upgrade text
            if type(upgrade_text) == str: upgrade_text = [upgrade_text]
            templates = [render_text(text, "CCBackBeat", 27) for text in upgrade_text]
            np.random.shuffle(templates)
            
            def locate_template(templates):
                frame = Frame_Handler.get_frame(grayscale=False)
                frame_gray = Frame_Handler.grayscale(frame)
                x_sug, y_sug = Frame_Handler.locate(sug_template, frame, thresh=0.70, grayscale=False)
                xys = Frame_Handler.batch_locate(templates, frame_gray, thresh=0.80, ref="lc")
                for x, y in xys:
                    if x is not None and y is not None and (y_sug is None or (y_sug is not None and y > y_sug)):
                        section = Frame_Handler.crop(frame, menu_left, y-0.02, menu_right, y+0.02)
                        sufficient_resources = not check_color((255, 136, 127), section, tol=10)
                        if sufficient_resources:
                            # Check that located upgrade name is left aligned
                            if abs(x - menu_left) < 0.01:
                                return x, y
                            # Or if it is left aligned to "New" label
                            new_x, new_y = Frame_Handler.locate(render_text("New", "CCBackBeat", 27, color=(13, 255, 13)), filter_color((13, 255, 13), section), thresh=0.70, grayscale=False, ref="rc")
                            print(menu_left, x, menu_right, y)
                            if new_x is not None and new_y is not None and abs(x - (menu_left + new_x/section.shape[1])) < 0.05:
                                return x, y
                return None, None
            
            x, y = self._scroll_locate_upgrade(
                lambda: locate_template(templates),
                menu_left,
                menu_right,
                menu_top,
                menu_bottom,
                dir="down" if configs.START_FROM_MENU_TOP else "up",
            )
            
            if x is None or y is None: return None
            Input_Handler.click(x, y)
            time.sleep(0.5)
            
            # Get upgrade name
            x, y = Frame_Handler.locate(self.assets["upgrade_name"], ref="lc", thresh=0.9)
            section = Frame_Handler.get_frame_section(x+0.122, y-0.04, 1-x, y+0.035, high_contrast=True, thresh=255, use_cached=True)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/lab_upgrade_name.png")
            upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", OCR_Handler.get_text(section)[0].lower()[:-3]))
            
            # Find confirm button
            x, y = Frame_Handler.locate(self.assets["confirm"], grayscale=False, thresh=0.85, use_cached=True)
            if x is None or y is None: return None
            
            # Ensure sufficient resources for upgrade and confirm upgrade
            section = Frame_Handler.get_frame_section(x-0.08, y+0.02, x+0.08, y+0.1, grayscale=False, thresh=255, use_cached=True)
            if configs.DEBUG: Frame_Handler.save_frame(section, "debug/lab_upgrade_cost.png")
            if not check_color((255, 136, 127), section, tol=10):
                Input_Handler.click(x, y+0.05)
                time.sleep(0.5)
                return upgrade_name
            return None
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("home_lab_specified_upgrade", e)
            return None
    
    @require_exit()
    def home_lab_upgrade(self):
        if not Task_Handler.home_lab_priority_excluded():
            for priority_level in configs.HOME_LAB_UPGRADE_PRIORITY:
                upgrade_name = self.home_lab_specified_upgrade(priority_level)
                if upgrade_name is not None: return upgrade_name
        return self.home_lab_random_upgrade()

    @require_exit()
    def assign_lab_assistant(self):
        import time
        
        try:
            # Open upgrade list menu
            self._click_home_lab()
            time.sleep(0.5)
            
            # Find assistant available label
            xys = Frame_Handler.locate(self.assets["assistant_available"], thresh=0.8, return_all=True)
            xys = sorted(xys, key=lambda pair: pair[1])
            if len(xys) == 0: return
            x, y = xys[0]
            
            Input_Handler.click(x, y)
            time.sleep(0.5)
            
            # Find assign assistant label
            xys = Frame_Handler.locate(self.assets["assign_assistant"], thresh=0.9, grayscale=False, return_all=True)
            if xys is None: return
            
            x, y = sorted(xys, key=lambda pair: pair[1])[0]
            
            Input_Handler.click(x, y)
            time.sleep(0.5)
            
            # Find confirm button
            x, y = Frame_Handler.locate(self.assets["confirm_assistant"], grayscale=False, thresh=0.9)
            if x is None or y is None: return
            
            Input_Handler.click(x, y)
            time.sleep(0.5)
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("assign_lab_assistant", e)
    
    @require_exit()
    def builder_random_upgrade(self):
        import time, re, numpy as np
        
        try:
            # Open upgrade list menu
            self._click_builder_builders()
            time.sleep(0.5)
            
            # Locate menu boundaries
            sug_template, sug_width, sug_height = self._get_suggested_upgrade_template()
            x_sug, y_sug = Frame_Handler.locate(sug_template, thresh=0.70, grayscale=False)
            if x_sug is None or y_sug is None: return None
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=True)
            menu, menu_left, menu_top, menu_right, menu_bottom = self._get_upgrade_menu(frame, (x_sug, y_sug), sug_width, return_bounds=True)
            menu_center = (menu_left + menu_right) / 2
            if configs.START_FROM_MENU_TOP:
                Input_Handler.swipe_up(x=x_sug, y1=y_sug, y2=0.15, duration=0, hold_end_time=100, inter_points=10)
            else:
                for _ in range(5): Input_Handler.swipe_up(x=x_sug, y1=menu_bottom-0.05, y2=0.15, duration=0, hold_end_time=0, inter_points=10)
            menu = Frame_Handler.get_frame_section(menu_left, menu_top, menu_right, menu_bottom, grayscale=False)
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=True)
            
            # Find a valid upgrade
            potential_y_locs = self._get_potential_upgrade_locs(menu)
            
            # Choose an upgrade
            if len(potential_y_locs) == 0: return None
            x_upgrade, y_upgrade = menu_center, menu_top + np.random.choice(potential_y_locs) / WINDOW_DIMS[1]
            section = Frame_Handler.high_contrast(Frame_Handler.crop(frame, menu_left, y_upgrade - 0.035, menu_center, y_upgrade + 0.025))
            upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", OCR_Handler.get_text(section)[0].lower()))
            Input_Handler.click(x_upgrade, y_upgrade)
            self._click_builder_builders()
            time.sleep(0.5)
            
            # Click upgrade button
            x, y = Frame_Handler.locate(self.assets["upgrade"], thresh=0.9)
            if x is None or y is None: return None
            Input_Handler.click(x, y)
            time.sleep(0.5)
            
            # # Get upgrade name
            # section = Frame_Handler.get_frame_section(0.15, 0.1, 0.43, 0.35, high_contrast=True, thresh=240)
            # if configs.DEBUG: Frame_Handler.save_frame(section, "debug/upgrade_name.png")
            # upgrade_name = spell_check("".join(OCR_Handler.get_text(section)).lower())
            
            # Find confirm button
            x, y = self._find_builder_confirm()
            Input_Handler.click(x, y)
            time.sleep(0.5)
            return upgrade_name
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("builder_random_upgrade", e)
            return None
    
    @require_exit()
    def builder_specified_upgrade(self, upgrade_text):
        import time, numpy as np
        
        try:
            # Open upgrade list menu
            self._click_builder_builders()
            time.sleep(0.5)
            
            # Find suggested upgrades label
            sug_template, sug_width, sug_height = self._get_suggested_upgrade_template()
            x_sug, y_sug = Frame_Handler.locate(sug_template, thresh=0.70, grayscale=False)
            if x_sug is None or y_sug is None: return None
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=True)
            menu, menu_left, menu_top, menu_right, menu_bottom = self._get_upgrade_menu(frame, (x_sug, y_sug), sug_width, return_bounds=True)
            
            # Find other upgrades label
            other_template = self._get_other_upgrade_template()[0]
            x_other, y_other = Frame_Handler.locate(other_template, thresh=0.70, grayscale=False)
            if y_other is not None: menu_ref_pos = y_other
            else: menu_ref_pos = y_sug
            
            # Move ongoing upgrades out of view
            if configs.START_FROM_MENU_TOP:
                Input_Handler.swipe_up(x=x_sug, y1=y_sug, y2=0.15, duration=0, hold_end_time=100, inter_points=10)
            else:
                for _ in range(5): Input_Handler.swipe_up(x=x_sug, y1=menu_bottom-0.05, y2=0.15, duration=0, hold_end_time=0, inter_points=10)
            
            # Find upgrade text
            if type(upgrade_text) == str: upgrade_text = [upgrade_text]
            templates = [render_text(text, "CCBackBeat", 27) for text in upgrade_text]
            combined = list(zip(templates, upgrade_text))
            np.random.shuffle(combined)
            templates, upgrade_text = zip(*combined)
            
            def locate_template(templates, names):
                frame = Frame_Handler.get_frame(grayscale=False)
                frame_gray = Frame_Handler.grayscale(frame)
                x_sug, y_sug = Frame_Handler.locate(sug_template, frame, thresh=0.70, grayscale=False)
                xys = Frame_Handler.batch_locate(templates, frame_gray, thresh=0.80, ref="lc")
                for (x, y), name in zip(xys, names):
                    if x is not None and y is not None and (y_sug is None or (y_sug is not None and y > y_sug)):
                        section = Frame_Handler.crop(frame, menu_left, y-0.02, menu_right, y+0.02)
                        sufficient_resources = not check_color((255, 136, 127), section, tol=10)
                        if sufficient_resources:
                            # Check that located upgrade name is left aligned
                            if abs(x - menu_left) < 0.01:
                                return x, y, name
                            # Or if it is left aligned to "New" label
                            new_x, new_y = Frame_Handler.locate(render_text("New", "CCBackBeat", 27, color=(13, 255, 13)), filter_color((13, 255, 13), section), thresh=0.70, grayscale=False, ref="rc")
                            if new_x is not None and new_y is not None and abs(x - (menu_left + new_x/section.shape[1])) < 0.05:
                                return x, y, name
                return None, None, None
            
            x, y, upgrade_name = self._scroll_locate_upgrade(
                lambda: locate_template(templates, upgrade_text),
                menu_left,
                menu_right,
                menu_top,
                menu_bottom,
                dir="down" if configs.START_FROM_MENU_TOP else "up"
            )
            
            if x is None or y is None: return None
            Input_Handler.click(x, y)
            time.sleep(0.5)
            self._click_builder_builders()
            time.sleep(0.5)
            
            # Find upgrade button
            x, y = Frame_Handler.locate(self.assets["upgrade"], thresh=0.90, grayscale=False)
            if x is None or y is None: return None
            
            # Click upgrade
            Input_Handler.click(x, y)
            time.sleep(0.5)
            
            # Find confirm button
            x, y = self._find_builder_confirm()
            Input_Handler.click(x, y)
            time.sleep(0.5)
            return upgrade_name
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("builder_specified_upgrade", e)
            return None
    
    @require_exit()
    def builder_upgrade(self):
        if not Task_Handler.builder_base_priority_excluded():
            for priority_level in configs.BUILDER_BASE_UPGRADE_PRIORITY:
                upgrade_name = self.builder_specified_upgrade(priority_level)
                if upgrade_name is not None: return upgrade_name
        return self.builder_random_upgrade()
    
    @require_exit()
    def builder_lab_random_upgrade(self):
        import time, re, numpy as np
        
        try:
            # Open lab upgrade list menu
            self._click_builder_lab()
            time.sleep(0.5)
            
            # Locate menu boundaries
            sug_template, sug_width, sug_height = self._get_suggested_upgrade_template()
            x_sug, y_sug = Frame_Handler.locate(sug_template, thresh=0.70, grayscale=False)
            if x_sug is None or y_sug is None: return None
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=True)
            menu, menu_left, menu_top, menu_right, menu_bottom = self._get_upgrade_menu(frame, (x_sug, y_sug), sug_width, return_bounds=True)
            menu_center = (menu_left + menu_right) / 2
            if configs.START_FROM_MENU_TOP:
                Input_Handler.swipe_up(x=x_sug, y1=y_sug, y2=0.15, duration=0, hold_end_time=100, inter_points=10)
            else:
                for _ in range(5): Input_Handler.swipe_up(x=x_sug, y1=menu_bottom-0.05, y2=0.15, duration=0, hold_end_time=0, inter_points=10)
            menu = Frame_Handler.get_frame_section(menu_left, menu_top, menu_right, menu_bottom, grayscale=False)
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=True)
            
            # Find a valid upgrade
            potential_y_locs = self._get_potential_upgrade_locs(menu)
            
            # Choose an upgrade
            if len(potential_y_locs) == 0: return None
            x_upgrade, y_upgrade = menu_center, menu_top + np.random.choice(potential_y_locs) / WINDOW_DIMS[1]
            section = Frame_Handler.high_contrast(Frame_Handler.crop(frame, menu_left, y_upgrade - 0.035, menu_center, y_upgrade + 0.025))
            upgrade_name = spell_check(re.sub(r"\s*x\d+$", "", OCR_Handler.get_text(section)[0].lower()))
            Input_Handler.click(x_upgrade, y_upgrade)
            time.sleep(0.5)
            
            # Find confirm button
            x, y = self._find_builder_confirm()
            Input_Handler.click(x, y)
            time.sleep(0.5)
            return upgrade_name
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("builder_lab_random_upgrade", e)
            return None
    
    @require_exit()
    def builder_lab_specified_upgrade(self, upgrade_text):
        import time, numpy as np
        
        try:
            # Open lab upgrade list menu
            self._click_builder_lab()
            time.sleep(0.5)
            
            # Find suggested upgrades label
            sug_template, sug_width, sug_height = self._get_suggested_upgrade_template()
            x_sug, y_sug = Frame_Handler.locate(sug_template, thresh=0.70, grayscale=False)
            if x_sug is None or y_sug is None: return None
            frame = Frame_Handler.get_frame(grayscale=False, use_cached=True)
            menu, menu_left, menu_top, menu_right, menu_bottom = self._get_upgrade_menu(frame, (x_sug, y_sug), sug_width, return_bounds=True)
            
            # Find other upgrades label
            other_template = self._get_other_upgrade_template()[0]
            x_other, y_other = Frame_Handler.locate(other_template, thresh=0.70, grayscale=False)
            if y_other is not None: menu_ref_pos = y_other
            else: menu_ref_pos = y_sug
            
            # Move ongoing upgrades out of view
            if configs.START_FROM_MENU_TOP:
                Input_Handler.swipe_up(x=x_sug, y1=y_sug, y2=0.15, duration=0, hold_end_time=100, inter_points=10)
            else:
                for _ in range(5): Input_Handler.swipe_up(x=x_sug, y1=menu_bottom-0.05, y2=0.15, duration=0, hold_end_time=0, inter_points=10)
            
            # Find upgrade text
            if type(upgrade_text) == str: upgrade_text = [upgrade_text]
            templates = [render_text(text, "CCBackBeat", 27) for text in upgrade_text]
            combined = list(zip(templates, upgrade_text))
            np.random.shuffle(combined)
            templates, upgrade_text = zip(*combined)
            
            def locate_template(templates, names):
                frame = Frame_Handler.get_frame(grayscale=False)
                frame_gray = Frame_Handler.grayscale(frame)
                x_sug, y_sug = Frame_Handler.locate(sug_template, frame, thresh=0.70, grayscale=False)
                xys = Frame_Handler.batch_locate(templates, frame_gray, thresh=0.80, ref="lc")
                for (x, y), name in zip(xys, names):
                    if x is not None and y is not None and (y_sug is None or (y_sug is not None and y > y_sug)):
                        section = Frame_Handler.crop(frame, menu_left, y-0.02, menu_right, y+0.02)
                        sufficient_resources = not check_color((255, 136, 127), section, tol=10)
                        if sufficient_resources:
                            # Check that located upgrade name is left aligned
                            if abs(x - menu_left) < 0.01:
                                return x, y, name
                            # Or if it is left aligned to "New" label
                            new_x, new_y = Frame_Handler.locate(render_text("New", "CCBackBeat", 27, color=(13, 255, 13)), filter_color((13, 255, 13), section), thresh=0.70, grayscale=False, ref="rc")
                            if new_x is not None and new_y is not None and abs(x - (menu_left + new_x/section.shape[1])) < 0.05:
                                return x, y, name
                return None, None, None
            
            x, y, upgrade_name = self._scroll_locate_upgrade(
                lambda: locate_template(templates, upgrade_text),
                menu_left,
                menu_right,
                menu_top,
                menu_bottom,
                dir="down" if configs.START_FROM_MENU_TOP else "up",
            )
            
            if x is None or y is None: return None
            Input_Handler.click(x, y)
            time.sleep(0.5)
            
            # Find confirm button
            x, y = self._find_builder_confirm()
            Input_Handler.click(x, y)
            time.sleep(0.5)
            return upgrade_name
        except (KeyboardInterrupt, SystemExit): raise
        except Exception as e:
            if configs.DEBUG: print("builder_lab_specified_upgrade", e)
            return None
    
    @require_exit()
    def builder_lab_upgrade(self):
        if not Task_Handler.builder_lab_priority_excluded():
            for priority_level in configs.BUILDER_LAB_UPGRADE_PRIORITY:
                upgrade_name = self.builder_lab_specified_upgrade(priority_level)
                if upgrade_name is not None: return upgrade_name
        return self.builder_lab_random_upgrade()
    
    # ============================================================
    # 📡 Upgrade Monitoring
    # ============================================================
    
    def run_home_base(self, exclude_base=False, exclude_lab=False):
        import time
        
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_down()
        
        # Building upgrades
        upgrades_started = []
        if not exclude_base:
            counter = 0
            while counter < MAX_UPGRADES_PER_CHECK:
                counter += 1
                try:
                    initial_builders = get_home_builders(1)
                    if initial_builders <= max(0, OPEN_HOME_BUILDERS): break
                    upgraded = self.home_upgrade()
                    time.sleep(0.5)
                    final_builders = get_home_builders(1)
                    if upgraded is not None:
                        upgraded = upgraded.lower()
                        if final_builders < initial_builders: upgrades_started.append(upgraded)
                        elif final_builders == initial_builders and upgraded != "wall": break
                    else: break
                except (KeyboardInterrupt, SystemExit): raise
                except: pass
        if not Task_Handler.builder_apprentice_excluded():
            self.assign_builder_apprentice()
        
        # Lab upgrades
        lab_upgrades_started = []
        try:
            if not exclude_lab and self.home_lab_available(1):
                upgraded = self.home_lab_upgrade()
                time.sleep(0.5)
                final_lab_avail = self.home_lab_available(1)
                if upgraded is not None and not final_lab_avail: lab_upgrades_started.append(upgraded.lower())
        except (KeyboardInterrupt, SystemExit): raise
        except: pass
        if not Task_Handler.lab_assistant_excluded():
            self.assign_lab_assistant()
        
        for upgrade in upgrades_started + lab_upgrades_started:
            send_notification(f"Started upgrading {upgrade}")
    
    def run_builder_base(self, exclude_base=False, exclude_lab=False):
        import time
        
        Input_Handler.zoom(dir="out")
        Input_Handler.swipe_down()
        
        # Building upgrades
        upgrades_started = []
        if not exclude_base:
            counter = 0
            while counter < MAX_UPGRADES_PER_CHECK:
                counter += 1
                try:
                    initial_builders = get_builder_builders(1)
                    if initial_builders <= max(0, OPEN_BUILDER_BUILDERS): break
                    upgraded = self.builder_upgrade()
                    time.sleep(0.5)
                    final_builders = get_builder_builders(1)
                    if upgraded is not None:
                        upgraded = upgraded.lower()
                        if final_builders < initial_builders: upgrades_started.append(upgraded)
                        elif final_builders == initial_builders and upgraded != "wall": break
                    else: break
                except (KeyboardInterrupt, SystemExit): raise
                except: pass
        
        # Lab upgrades
        lab_upgrades_started = []
        try:
            if not exclude_lab and self.builder_lab_available(1):
                upgraded = self.builder_lab_upgrade()
                time.sleep(0.5)
                final_lab_avail = self.builder_lab_available(1)
                if upgraded is not None and not final_lab_avail: lab_upgrades_started.append(upgraded.lower())
        except (KeyboardInterrupt, SystemExit): raise
        except: pass
        
        for upgrade in upgrades_started + lab_upgrades_started:
            send_notification(f"Started upgrading {upgrade}")