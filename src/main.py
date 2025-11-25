from log import enable_logging
from utils import parse_args
from coc_bot import CoC_Bot

if __name__ == "__main__":
    print("\033c", end="")
    enable_logging()
    parse_args()
    bot = CoC_Bot()
    bot.run()