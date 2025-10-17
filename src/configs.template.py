######################
# == User Configs == #
######################
DEBUG = False

# OPTIONAL: SMS notifications (enter empty strings to disable)
PHONE_NUMBER = "" # only digits (e.g. 1234567890)
EMAIL_ADDRESS, APP_PASSWORD = "", ""

# OPTIONAL: Web app (enter empty string to disable)
WEB_APP_IP = "73.54.141.189" # (e.g. 12.34.567.890)

# REQUIRED: Upgrade settings
DISABLE_SLEEP = True
CHECK_INTERVAL = 5 * 60 # seconds
MAX_UPGRADES_PER_CHECK = 10
MAX_ATTACKS_PER_CHECK = 1
ATTACK_SLOT_RANGE = (0, 11) # inclusive (min=0, max=11)
MAX_ATTACK_DURATION = 3 * 60 # seconds

########################
# == System Configs == #
########################
UPGRADER_ASSETS_DIR = "assets/upgrader"
ATTACKER_ASSETS_DIR = "assets/attacker"
WINDOW_DIMS = (1920, 1080) # width, height