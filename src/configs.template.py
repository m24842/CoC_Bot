######################
# == User Configs == #
######################

# OPTIONAL: Telegram notifications (enter empty string to disable)
TELEGRAM_BOT_TOKEN = "" # (e.g. 123456789:ABCdefGHIjkl-MNO_pqrSTUvwxYZ)

# OPTIONAL: Web app (enter empty string to disable)
WEB_APP_URL = "" # (e.g. 12.34.567.890:1234)
WEB_APP_PORT = 1234

# REQUIRED: General Settings
CHECK_INTERVAL = 5 * 60 # seconds

# REQUIRED: Upgrade settings
MAX_UPGRADES_PER_CHECK = 10

# REQUIRED: Attack Settings
MAX_ATTACKS_PER_CHECK = 1
MAX_ATTACK_DURATION = 3 * 60 # seconds
TROOP_DEPLOY_TIME = 3 # seconds
ATTACK_SLOT_RANGE = (0, 11) # inclusive first slot is index 0
EXCLUDE_ATTACK_SLOTS = [] # e.g. [2, 5, 7]
EXCLUDE_CLAN_TROOPS = True

########################
# == System Configs == #
########################
DEBUG = False
DISABLE_DEEVICE_SLEEP = True
WINDOW_DIMS = (1920, 1080) # width, height
ADB_ADDRESS = "127.0.0.1:5555"
UPGRADER_ASSETS_DIR = "assets/upgrader"
ATTACKER_ASSETS_DIR = "assets/attacker"
NOTIFICATIONS_DB_PATH = "notifications.db"