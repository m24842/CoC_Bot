from utils import *
try:
    from configs import *
except:
    from configs_build import *
from upgrader import Upgrader
from attacker import Attacker

class CoC_Bot:
    def __init__(self):
        if configs.AUTO_START_BLUESTACKS:
            BlueStacks_Manager.init()
            BlueStacks_Manager.restart()
        assert ADB_Manager.connect(60), "Failed to connect to ADB. Ensure BlueStacks is running and ADB is enabled."
        self.upgrader = Upgrader()
        self.attacker = Attacker()
    
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
                    update_status("now")
                    
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
                        to_home_base(ref_cache=True)
                    
                    if not skip_home_base_upgrades:
                        self.upgrader.run_home_base(exclude_home_base, exclude_home_lab)
                    if not exclude_home_attacks:
                        self.attacker.run_home_base(restart=not skip_home_base_upgrades or not skip_builder_base_upgrades)
                    
                    # Check builder base
                    if not skip_builder_base_upgrades or not exclude_builder_attacks:
                        to_builder_base(ref_cache=True)
                    
                    if not skip_builder_base_upgrades:
                        self.upgrader.collect_builder_attack_elixir()
                        self.upgrader.run_builder_base(exclude_builder_base, exclude_builder_lab)
                    if not exclude_builder_attacks:
                        self.attacker.run_builder_base()
                    
                    to_home_base()
                    stop_coc()
                    update_status(time.time())
                
                time.sleep(60 * CHECK_INTERVAL)
            
            except (KeyboardInterrupt, SystemExit): raise
            except Exception as e:
                import traceback
                traceback.print_exc()
                stop_coc()
                update_status("error")
