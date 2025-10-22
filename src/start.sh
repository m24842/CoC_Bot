#!/bin/bash

SESSION_NAME="CoC_Bot"

if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "$SESSION_NAME session already exists. Attaching..."
    tmux attach -t $SESSION_NAME
else
    echo "Starting new tmux session: $SESSION_NAME"
    tmux new-session -d -s $SESSION_NAME "sudo /Users/madison/CoC_Bot/.venv/bin/python /Users/madison/CoC_Bot/src/main.py"
    echo "$SESSION_NAME session started and detached."
fi