import loguru
import warnings

loguru.logger.remove()
warnings.filterwarnings("ignore", category=UserWarning, module='torch')

import utils
from utils import *
from coc_bot import CoC_Bot

if __name__ == "__main__":
    parse_args(debug=True, id="alt")
    bot = CoC_Bot()
    # Frame_Handler.screenshot()
    # start_coc()
    # bot.run()
    # to_home_base()
    # bot.upgrader.run_home_base()
    # bot.attacker.run_home_base()
    # bot.attacker.complete_attack(exclude_clan_troops=EXCLUDE_CLAN_TROOPS)
    # to_builder_base()
    # bot.upgrader.collect_builder_attack_elixir()
    bot.upgrader.run_builder_base()
    # bot.attacker.run_builder_base()