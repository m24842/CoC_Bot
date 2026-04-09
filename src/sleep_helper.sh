#!/bin/bash

PARENT_PID="$1"

set_sleep() {
    pmset -a sleep "$1"
}

set_disablesleep() {
    pmset -a disablesleep "$1"
}

parent_alive() {
    kill -0 "$1" 2>/dev/null
}

cleanup() {
    set_sleep "$ORIGINAL_SLEEP"
    set_disablesleep 0
    exit 0
}

trap cleanup SIGTERM SIGINT

ORIGINAL_SLEEP=$(pmset -g | grep ' sleep ' | awk '{print $2}')

set_sleep 0
set_disablesleep 1

while kill -0 "$PARENT_PID" 2>/dev/null; do
    sleep 1
done

cleanup