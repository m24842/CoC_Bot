import os
import sys
import shutil
from pathlib import Path

dir_path = Path(__file__).parent.resolve()

bot_packages = dir_path / "src" / "requirements.txt"

web_app_packages = dir_path / "app" / "requirements.txt"

bot_setup = input("Install bot dependencies? (y/n): ").lower() == 'y'
web_app_setup = input("Install web app dependencies? (y/n): ").lower() == 'y'

if not Path.exists(dir_path / ".venv"): os.system(f"{sys.executable} -m venv {dir_path / '.venv'}")

if bot_setup:
    os.system(f"{sys.executable} -m pip install -r {bot_packages}")
if web_app_setup:
    os.system(f"{sys.executable} -m pip install -r {web_app_packages}")

if not Path.exists(dir_path / "src" / "configs.py"):
    shutil.copy(dir_path / "src" / "configs.template.py", dir_path / "src" / "configs.py")
else:
    print(f"src/configs.py already exists, skipping creation.")

if not Path.exists(dir_path / "scripts" / "start.sh"):
    shutil.copy(dir_path / "scripts" / "start.template.sh", dir_path / "scripts" / "start.sh")
else:
    print(f"scripts/start.sh already exists, skipping creation.")