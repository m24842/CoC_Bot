import os
import sys
import shutil

bot_packages = [
    "opencv-python",
    "easyocr",
    "requests",
    "numpy",
    "pure-python-adb",
    "pyminitouch",
    "psutil",
]

web_app_packages = [
    "flask",
    "waitress",
]

bot_setup = input("Install bot dependencies? (y/n): ").lower() == 'y'
web_app_setup = input("Install web app dependencies? (y/n): ").lower() == 'y'

packages = []
if bot_setup: packages += bot_packages
if web_app_setup: packages += web_app_packages

os.system(f"{sys.executable} -m pip install " + " ".join(packages))

if not os.path.exists("src/configs.py"):
    shutil.copy("src/configs.template.py", "src/configs.py")
else:
    print(f"src/configs.py already exists, skipping creation.")