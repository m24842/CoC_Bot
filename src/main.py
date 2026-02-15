from log import enable_logging
from utils import parse_args
from coc_bot import CoC_Bot

if __name__ == "__main__":
    args = parse_args()
    enable_logging(args.id)
    bot = CoC_Bot()
    bot.run()