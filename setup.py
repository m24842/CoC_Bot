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

if not os.path.exists(".venv"): os.system(f"{sys.executable} -m venv .venv")
if len(packages): os.system(f"{sys.executable} -m pip install " + " ".join(packages))

if not os.path.exists("src/configs.py"):
    shutil.copy("src/configs.template.py", "src/configs.py")
else:
    print(f"src/configs.py already exists, skipping creation.")

if web_app_setup and not os.path.exists("/etc/systemd/system/coc_bot_web_app.service"):
    print("Setting up web app systemd service...")
    user = os.environ['USER']
    with open("app/coc_bot_web_app.template.service", "r") as f: content = f.read()
    content = content.replace("<user>", user)
    with open("app/coc_bot_web_app.service", "w") as f: f.write(content)
    
    os.system("sudo cp app/coc_bot_web_app.service /etc/systemd/system/coc_bot_web_app.service")
    os.system("sudo systemctl daemon-reload")
    os.system("sudo systemctl enable coc_bot_web_app.service")
    start_web_app = input("Start web app systemd service? (y/n): ").lower() == 'y'
    if start_web_app:
        os.system("sudo systemctl start coc_bot_web_app")
    else:
        print("Use 'sudo systemctl start coc_bot_web_app' to start web app service.")