#!/system/bin/sh
# btw ls -1 does NOT exist on this phone. use ls instead, its sorted by name ascending
PHOTOS_FOLDER="/sdcard/DCIM/100MEDIA/"
MAX_IMAGES=100

# Unlock the screen
sh /data/dha/press_power.sh

# Trigger camera intent
am start -a android.media.action.STILL_IMAGE_CAMERA
sleep 2

# Trigger camera button press
input keyevent KEYCODE_CAMERA
# Should return after the photo was taken.

# Only keep the last 100 Images
total=$(ls $PHOTOS_FOLDER | wc -l)
[ $total -gt $MAX_IMAGES ] && ls $PHOTOS_FOLDER | head -n $((total - MAX_IMAGES)) | while read -r f; do rm "$PHOTOS_FOLDER/$f"; done

# echo the latest image
echo $PHOTOS_FOLDER/$(ls $PHOTOS_FOLDER | tail -n 1)

# Sleep after camera is done just to be sure.
sleep 2

# Lock the screen
input keyevent KEYCODE_POWER
