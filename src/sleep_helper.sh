#!/bin/bash

PARENT_PID="$1"

set_sleep() {
    pmset -a sleep "$1"
}

parent_alive() {
    kill -0 "$1" 2>/dev/null
}

cleanup() {
    set_sleep "$ORIGINAL_SLEEP"
    exit 0
}

trap cleanup SIGTERM SIGINT

ORIGINAL_SLEEP=$(pmset -g | grep ' sleep ' | awk '{print $2}')

set_sleep 0

if kill -0 "$PARENT_PID" 2>/dev/null; then
    wait "$PARENT_PID"
fi

cleanup