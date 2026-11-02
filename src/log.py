import sys
import warnings
from pathlib import Path
from loguru import logger

if getattr(sys, "frozen", False):
    APP_DATA_DIR = Path.home() / ".CoC_Bot"
    APP_DATA_DIR.mkdir(exist_ok=True)
    LOG_DIR = APP_DATA_DIR / "debug"
else:
    LOG_DIR = Path("debug")

logger.remove()
warnings.filterwarnings("ignore", category=UserWarning, module='torch')

def enable_logging(id):
    LOG_DIR.mkdir(exist_ok=True)
    LOG_PATH = LOG_DIR / f"{id}.log"

    exclude_modules = [
        "pyminitouch",
    ]

    def is_included(record):
        return not any(record["name"].startswith(mod) for mod in exclude_modules)

    logger.add(
        LOG_PATH,
        rotation="10 MB",
        retention=5,
        compression="zip",
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        filter=lambda record: is_included(record),
    )

    if sys.stdout is not None:
        logger.add(
            sys.stdout,
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | <level>{level: <8}</level> | {message}",
            filter=lambda record: is_included(record) and record["level"].no < 30
        )

    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | <level>{level: <8}</level> | {message}",
            filter=lambda record: is_included(record) and record["level"].no >= 30
        )

