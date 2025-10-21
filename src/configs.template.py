######################
# == User Configs == #
######################
DEBUG = False

# OPTIONAL: Telegram notifications (enter empty strings to disable)
TELEGRAM_BOT_TOKEN = "" # (e.g. 123456789:ABCdefGHIjkl-MNO_pqrSTUvwxYZ)

# OPTIONAL: Web app (enter empty string to disable)
WEB_APP_IP = "73.54.141.189" # (e.g. 12.34.567.890)
WEB_APP_PORT = 1234

# REQUIRED: Upgrade settings
DISABLE_SLEEP = True
CHECK_INTERVAL = 5 * 60 # seconds
MAX_UPGRADES_PER_CHECK = 10
MAX_ATTACKS_PER_CHECK = 1
ATTACK_SLOT_RANGE = (0, 11) # inclusive (min=0, max=11)
MAX_ATTACK_DURATION = 3 * 60 # seconds
TROOP_DEPLOY_TIME = 3 # seconds

########################
# == System Configs == #
########################
WINDOW_DIMS = (1920, 1080) # width, height
UPGRADER_ASSETS_DIR = "assets/upgrader"
ATTACKER_ASSETS_DIR = "assets/attacker"
NOTIFICATIONS_DB_PATH = "notifications.db"