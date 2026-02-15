#!/bin/bash

PARENT_PID="$1"

displaysleep() {
    pmset -a displaysleep "$1"
}

parent_alive() {
    if kill -0 "$1" 2>/dev/null; then
        return 0  # true
    else
        return 1  # false
    fi
}

cleanup() {
    displaysleep 0
    exit 0
}

trap cleanup SIGTERM SIGINT

displaysleep 1

while parent_alive "$PARENT_PID"; do
    sleep 60
done

cleanup
