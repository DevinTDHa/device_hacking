#!/bin/bash
# Install capture.sh on the phone as `capture` on PATH.
cd "$(dirname "$0")/.."

TERMUX_BIN=/data/data/com.termux/files/usr/bin

rsync -vhPu capture.sh iot-redmi:$TERMUX_BIN/capture
ssh iot-redmi "chmod 755 $TERMUX_BIN/capture"
