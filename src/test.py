import log
import configs
import utils
from utils import *
from coc_bot import CoC_Bot
import cv2

if __name__ == "__main__":
    configs.AUTO_START_EMULATOR = False
    args = parse_args(debug=True, id="main")
    init_instance(args.id)
    bot = CoC_Bot()
    Frame_Handler.screenshot()
    # frame = Frame_Handler.cached_frame
    # menu = Frame_Handler.crop(frame, 0.775, 0.06, 1.0, -0.1)
    # frame = cv2.imread("debug/main_pet_house.png")
    # Dev_Tools.optimal_template_font_size(
    #     frame,
    #     text="Available",
    #     font="CCBackBeat",
    #     font_size_range=(10, 100),
    #     # color=(195, 172, 166),
    #     # color=(180, 247, 86),
    #     grayscale=True,
    #     prefilter=False,
    #     plot_results=True
    # )
    # Dev_Tools.optimal_template_scale(
    #     frame,
    #     template=Asset_Manager.upgrader_assets["upgrade"],
    #     scale_range=(0.8, 1.0),
    #     step=0.01,
    #     grayscale=False,
    #     prefilter=False,
    #     plot_results=True
    # )
    # template = Asset_Manager.upgrader_assets["builder_gold"]
    # x, y, c = Frame_Handler.locate(
    #     template,
    #     frame,
    #     grayscale=False,
    #     prefilter=True,
    #     return_confidence=True,
    # )
    # print(f"Located template at ({x}, {y}) with confidence {c:.2f}")
    # print(bot.upgrader.pet_house_available())
    
    # start_coc()
    # bot.run()
    # to_home_base()
    # bot.upgrader.run_home_base()
    # bot.upgrader.home_upgrade()
    bot.upgrader.home_random_upgrade()
    # bot.upgrader.home_specified_upgrade(HOME_BASE_UPGRADE_PRIORITY[0])
    # bot.upgrader.home_lab_upgrade()
    # bot.upgrader.home_lab_random_upgrade()
    # bot.upgrader.home_lab_specified_upgrade(HOME_LAB_UPGRADE_PRIORITY[0])
    # bot.upgrader.assign_builder_apprentice()
    # bot.attacker.run_home_base()
    # bot.attacker.complete_normal_attack(exclude_clan_troops=EXCLUDE_CLAN_TROOPS)
    # bot.attacker.complete_builder_attack()
    # to_builder_base()
    # bot.upgrader.collect_builder_attack_elixir()
    # bot.upgrader.run_builder_base()
    # bot.upgrader.builder_upgrade()
    # bot.upgrader.builder_random_upgrade()
    # bot.upgrader.builder_specified_upgrade(BUILDER_BASE_UPGRADE_PRIORITY[0])
    # bot.upgrader.builder_lab_upgrade()
    # bot.upgrader.builder_lab_random_upgrade()
    # bot.upgrader.builder_lab_specified_upgrade(BUILDER_LAB_UPGRADE_PRIORITY[0])
    # bot.attacker.run_builder_base()
