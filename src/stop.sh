#!/bin/bash

SESSION_NAME="CoC_Bot"

if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    tmux kill-session -t $SESSION_NAME
    echo "$SESSION_NAME session stopped."
else
    echo "$SESSION_NAME session does not exist."
fi