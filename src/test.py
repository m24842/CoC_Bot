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
    print(bot.upgrader.lab_upgrade())
    print(bot.upgrader.lab_available(1))
    # bot.attacker.run()