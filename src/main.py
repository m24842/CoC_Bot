import warnings
from log import enable_logging
from coc_bot import CoC_Bot

warnings.filterwarnings("ignore", category=UserWarning, module='torch')

enable_logging()

if __name__ == "__main__":
    bot = CoC_Bot()
    print("\033c", end="")
    bot.run()