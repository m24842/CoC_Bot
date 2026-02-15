#!/bin/bash

set -e

NAME="CoC_Bot" # Rename for each instance

source .venv/bin/activate
rm -rf build dist *.spec

pyinstaller \
  --name "${NAME}" \
  --onedir \
  --windowed \
  --icon="media/CoC_Bot.icns" \
  --add-data "assets:assets" \
  "src/main.py"