import loguru
import warnings

loguru.logger.remove()
warnings.filterwarnings("ignore", category=UserWarning, module='torch')

from utils import *
from coc_bot import CoC_Bot

if __name__ == "__main__":
    parse_args(debug=True, id="alt")
    bot = CoC_Bot()
    # bot.frame_handler.screenshot()
    bot.start()
    # bot.run()
    bot.upgrader.run()
    # bot.attacker.run()
    # bot.upgrader.lab_upgrade()