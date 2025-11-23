from log import enable_logging
from coc_bot import CoC_Bot

if __name__ == "__main__":
    enable_logging()
    bot = CoC_Bot()
    print("\033c", end="")
    bot.run()