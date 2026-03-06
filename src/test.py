import log
import utils
from utils import *
from coc_bot import CoC_Bot

if __name__ == "__main__":
    args = parse_args(debug=True, id="main")
    init_instance(args.id)
    bot = CoC_Bot(prevent_sleep=False)
    # Frame_Handler.screenshot()
    # start_coc()
    # bot.run()
    # to_home_base()
    # bot.upgrader.run_home_base()
    # bot.upgrader.home_upgrade()
    # bot.upgrader.home_random_upgrade()
    # bot.upgrader.home_specified_upgrade("Grand Warden")
    # bot.upgrader.home_specified_upgrade(HOME_BASE_UPGRADE_PRIORITY[0])
    # bot.upgrader.home_lab_upgrade()
    # bot.upgrader.home_lab_random_upgrade()
    # bot.upgrader.home_lab_specified_upgrade(HOME_LAB_UPGRADE_PRIORITY[0])
    # bot.upgrader.assign_builder_assistant()
    # bot.attacker.run_home_base()
    # bot.attacker.complete_attack(exclude_clan_troops=EXCLUDE_CLAN_TROOPS)
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