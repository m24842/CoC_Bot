import os
import sys
import shutil

packages = [
    "opencv-python",
    "easyocr",
    "requests",
    "numpy",
    "pure-python-adb",
    "flask",
    "waitress",
]

if sys.platform == "darwin": packages.append("pyobjc")
elif sys.platform == "win32": packages.append("psutil pywin32")

os.system(f"{sys.executable} -m pip install " + " ".join(packages))

if not os.path.exists("src/configs.py"):
    shutil.copy("src/configs.template.py", "src/configs.py")
else:
    print(f"src/configs.py already exists, skipping creation.")