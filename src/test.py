import warnings
from coc_bot import CoC_Bot

warnings.filterwarnings("ignore", category=UserWarning, module='torch')

if __name__ == "__main__":
    bot = CoC_Bot()
    bot.start()
    bot.attacker.run()