#!/system/bin/sh

test -f /dev/acca || /data/adb/vr25/acc/service.sh
test -f /dev/acca && echo "acc initialized"

