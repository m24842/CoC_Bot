#!/bin/bash

set -e

NAME="CoC_Bot" # Rename for each instance

source .venv/bin/activate
rm -rf build dist *.spec

pyinstaller \
  --name "${NAME}" \
  --onefile \
  --icon="media/CoC_Bot.icns" \
  --add-data "assets:assets" \
  --add-data "src/sleep_helper.sh:." \
  "src/main.py"