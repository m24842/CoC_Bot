#!/bin/bash

set -e

source .venv/bin/activate
rm -rf build dist *.spec

pyinstaller \
  --name "CoC_Bot" \
  --windowed \
  --icon="media/CoC_Bot.icns" \
  --add-data "assets:assets" \
  --add-data "src/gui_server:gui_server" \
  --add-data "src/sleep_helper.sh:." \
  "src/main.py"