import os
import sys
import shutil

packages = [
    "opencv-python",
    "easyocr",
    "requests",
    "numpy",
    "pure-python-adb",
    "pyminitouch",
    "psutil",
    "flask",
    "waitress",
]

os.system(f"{sys.executable} -m pip install " + " ".join(packages))

if not os.path.exists("src/configs.py"):
    shutil.copy("src/configs.template.py", "src/configs.py")
else:
    print(f"src/configs.py already exists, skipping creation.")