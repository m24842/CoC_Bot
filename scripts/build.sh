#!/bin/bash

set -e

source .venv/bin/activate
rm -rf build dist *.spec

pyinstaller \
  --name "CoC_Bot" \
  --onefile \
  --windowed \
  --icon="media/CoC_Bot.icns" \
  --add-data "assets:assets" \
  "src/main.py"