#!/system/bin/sh

# Simulates a power button press
sendevent /dev/input/event2 1 116 1
sleep 0.1
sendevent /dev/input/event2 0 0 0
sleep 0.1
sendevent /dev/input/event2 1 116 0
