import loguru
import warnings

loguru.logger.remove()
warnings.filterwarnings("ignore", category=UserWarning, module='torch')

import configs
configs.DEBUG = True
from utils import *
from coc_bot import CoC_Bot

if __name__ == "__main__":
    bot = CoC_Bot()
    # bot.frame_handler.get_frame(grayscale=False)
    bot.start()
    # bot.run()
    # bot.upgrader.run()
    bot.attacker.run()