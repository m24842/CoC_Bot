import sys
import venv
import shutil
import subprocess
from pathlib import Path

assert sys.version_info >= (3, 11), "Python 3.11 or higher is required!"

dir_path = Path(__file__).parent.resolve()
venv_path = dir_path / '.venv'
if sys.platform == "win32":
    venv_python = venv_path / "Scripts" / "python.exe"
else:
    venv_python = venv_path / "bin" / "python"

bot_packages = dir_path / "src" / "requirements.txt"
web_app_packages = dir_path / "app" / "requirements.txt"

bot_setup = input("Install bot dependencies? (y/n): ").lower() == 'y'
web_app_setup = input("Install web app dependencies? (y/n): ").lower() == 'y'

if not Path.exists(dir_path / ".venv"): venv.create(venv_path, system_site_packages=False, with_pip=True)

if bot_setup:
    subprocess.run([venv_python, "-m", "pip", "install", "-r", bot_packages])
if web_app_setup:
    subprocess.run([venv_python, "-m", "pip", "install", "-r", web_app_packages])

if not Path.exists(dir_path / "src" / "configs.py"):
    shutil.copy(dir_path / "src" / "configs.template.py", dir_path / "src" / "configs.py")
else:
    print(f"src/configs.py already exists, skipping creation.")

if not Path.exists(dir_path / "scripts" / "start.sh"):
    shutil.copy(dir_path / "scripts" / "start.template.sh", dir_path / "scripts" / "start.sh")
else:
    print(f"scripts/start.sh already exists, skipping creation.")