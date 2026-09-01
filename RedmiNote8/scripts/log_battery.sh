#!/bin/bash
mkdir -p ~/Logs
termux-battery-status | jq ". += { \"ts\": $(date +%s)}" -c >> ~/Logs/battery.jsonl
