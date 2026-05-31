#!/bin/bash

BASE_NAME="CoC_Bot"

echo "Existing sessions:"
tmux list-sessions 2>/dev/null | grep "^${BASE_NAME}_" | sed 's/^CoC_Bot_//; s/:.*//' | sed 's/^/- /'

echo
read -p "Enter instance ID to stop: " INSTANCE_ID

SESSION_NAME="${BASE_NAME}_${INSTANCE_ID}"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    tmux kill-session -t "$SESSION_NAME"
    echo "Session '$SESSION_NAME' stopped."
else
    echo "Session '$SESSION_NAME' does not exist."
fi
