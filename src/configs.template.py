######################
# == User Configs == #
######################

# OPTIONAL: Telegram notifications (enter empty string to disable)
TELEGRAM_BOT_TOKEN = "" # (e.g. 123456789:ABCdefGHIjkl-MNO_pqrSTUvwxYZ)

# OPTIONAL: Web app (enter empty string to disable)
WEB_APP_URL = "" # (e.g. 12.34.567.890:1234)
WEB_APP_PORT = 1234
WEB_APP_AUTH_USERNAME, WEB_APP_AUTH_PASSWORD = "", "" # (leave empty if not applicable)
INSTANCE_IDS = ["main"]
DEFAULT_INSTANCE_ID = INSTANCE_IDS[0] # change appropriately for app build

# REQUIRED: General Settings
CHECK_INTERVAL = 5 * 60 # seconds

# REQUIRED: Upgrade settings
MAX_UPGRADES_PER_CHECK = 10 # applies to both home and builder base
PRIORITIZE_HEROS = False # will always upgrade heros when possible over buildings if true
UPGRADE_HEROS = True # can be overridden on web app
UPGRADE_HOME_BASE = True # can be overridden on web app
UPGRADE_BUILDER_BASE = True # can be overridden on web app
UPGRADE_HOME_LAB = True # can be overridden on web app
UPGRADE_BUILDER_LAB = True # can be overridden on web app

# REQUIRED: Attack Settings
TROOP_DEPLOY_TIME = 3 # seconds
ATTACK_SLOT_RANGE = (0, 100) # inclusive first slot is index 0
EXCLUDE_CLAN_TROOPS = True
ATTACK_HOME_BASE = True # can be overridden on web app
ATTACK_BUILDER_BASE = True # can be overridden on web app

########################
# == System Configs == #
########################
DEBUG = False
DISABLE_DEVICE_SLEEP = True
WINDOW_DIMS = (1920, 1080) # width, height
ADB_ADDRESSES = ["127.0.0.1:5555"] # Bluestacks ADB addresses in order of instance IDs
ADB_ABS_DIR = "" # absolute path to dir with adb executable, leave empty to use system PATH (required for app build)