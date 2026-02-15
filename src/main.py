from utils import parse_args
from coc_bot import CoC_Bot

if __name__ == "__main__":
    print("\033c", end="")
    args = parse_args()
    bot = CoC_Bot()
    bot.run()