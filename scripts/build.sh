#!/bin/bash

set -e

source .venv/bin/activate
rm -rf build dist *.spec

pyinstaller \
    --name "CoC Bot" \
    --windowed \
    --icon "media/CoC_Bot.icns" \
    --add-data "assets:assets" \
    --add-data "src/gui_server:gui_server" \
    --add-data "src/sleep_helper.sh:." \
    --additional-hooks-dir "hooks" \
    "src/main.py"

if [[ "$(uname -s)" == "Darwin" ]]; then
    rm -rf "/Applications/CoC Bot.app"
    cp -R "dist/CoC Bot.app" "/Applications/"

    echo "Installed at:"
    echo "/Applications/CoC Bot.app"
    open "/Applications/CoC Bot.app"
fi
