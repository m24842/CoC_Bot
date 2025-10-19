import loguru
import warnings

loguru.logger.remove()
warnings.filterwarnings("ignore", category=UserWarning, module='torch')

import configs
configs.DEBUG = True
from coc_bot import CoC_Bot

if __name__ == "__main__":
    bot = CoC_Bot()
    bot.start()
    bot.upgrader.upgrade()
    # bot.attacker.run()