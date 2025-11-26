import sys
import os

PYTHONANYWHERE_USERNAME = ""

project_home = f'/home/{PYTHONANYWHERE_USERNAME}/CoC_Bot'
app_dir = os.path.join(project_home, 'app')
src_dir = os.path.join(project_home, 'src')

for path in [project_home, app_dir, src_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ['FLASK_APP'] = 'app/app.py'

from app import app as application