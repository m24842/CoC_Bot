#!/bin/bash

PYTHON_ABS_PATH="" # Absolute path to python executable in CoC_Bot virtual environment
MAIN_ABS_PATH="" # Absolute path to CoC_Bot main.py

read -p "Enter instance ID: " INSTANCE_ID

BASE_NAME="CoC_Bot"
SESSION_NAME="${BASE_NAME}_${INSTANCE_ID}"

if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "$SESSION_NAME session already exists. Attaching..."
    tmux attach -t $SESSION_NAME
else
    echo "Starting new tmux session: $SESSION_NAME"
    tmux new-session -d -s $SESSION_NAME "sudo $PYTHON_ABS_PATH $MAIN_ABS_PATH --id $INSTANCE_ID"
    echo "$SESSION_NAME session started and detached."
fi