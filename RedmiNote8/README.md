# Redmi Note 8

- Unlock Bootloader
    - https://new.c.mi.com/global/post/101245?utm_source=miui&utm_medium=official_web_faq&utm_campaign=official_web_miui
    - https://github.com/offici5l/MiUnlockTool
- Rooting
    - https://xdaforums.com/t/guide-all-about-unlocking-bootloader-twrp-and-rooting-redmi-note-8-8t.4031831/
    - https://twrp.me/xiaomi/xiaomiredminote8.html
    - TWRP downloads (all versions): https://dl.twrp.me/ginkgo/

## Flashing TWRP

Working procedure, verified on this device 2026-09-01. TWRP boots.

### Device facts (read off the device, not assumed)

| Property | Value | Why it matters |
|---|---|---|
| `ro.product.device` | `ginkgo` | Not `begonia` (Note 8 **Pro**) or `willow` (8T) — images are not interchangeable |
| `ro.build.version.release` | `9` (SDK 28) | Dictates which TWRP build to use |
| `ro.build.version.incremental` | `V11.0.7.0.PCOIDXM` | Indonesia ROM; needed to get the matching stock images |
| `ro.crypto.type` | `file` | FBE, so TWRP must match the Android version to decrypt `/data` |
| `ro.boot.slot_suffix` | *(empty)* | Non-A/B — there is a real `recovery` partition (`mmcblk0p76`) |
| `ro.boot.flash.locked` | `0` (`orange`) | Bootloader already unlocked |

Read them with:

```sh
./adb shell getprop ro.product.device
./adb shell ls -l /dev/block/bootdevice/by-name/   # confirm recovery/vbmeta exist
```

### Three things that make this fail

1. **TWRP build must match the phone's Android version.** `twrp-3.7.1_12-0-ginkgo.img` is the Android **12** tree; this phone is Android **9**. Use `twrp-3.6.2_9-0-ginkgo.img` (newest `_9-0` build). Wrong build → boots to a dead splash, or can't decrypt FBE `/data`.

2. **`fastboot boot` does not work on this bootloader.** It prints `Booting OKAY` and then does nothing — the device just sits in fastboot. Verified: the phone never left fastboot mode. Do not use it to test recovery images; it is a no-op, not a diagnostic.

3. **MIUI restores the stock recovery on every single system boot** (`/system/bin/install-recovery.sh`). If MIUI boots even once after flashing TWRP, TWRP is gone. This is the one that causes the "I flashed it but it's not there" loop — and it silently undoes the flash between attempts, so repeated tries all look like fresh failures.

Also: `vbmeta` chains verification of the `recovery` partition to Xiaomi's signing key, so AVB rejects TWRP even with the bootloader unlocked. Symptom is distinctive — the recovery splash appears and then **falls through to MIUI** rather than hanging. Confirm with:

```sh
python3 avb/avbtool.py info_image --image stock/vbmeta.img
# Chain Partition descriptor: Partition Name: recovery   <- this is the blocker
```

### Procedure

```sh
cd platform-tools

# 1. Get the Android 9 TWRP build (NOT the _12 one) and verify it
curl -sL -e "https://dl.twrp.me/ginkgo/" -A "Mozilla/5.0" \
  -o twrp-3.6.2_9-0-ginkgo.img "https://dl.twrp.me/ginkgo/twrp-3.6.2_9-0-ginkgo.img?d=1"
shasum -a 256 twrp-3.6.2_9-0-ginkgo.img
# expect 5dbcfb19076a88edea86c4b900b0ca71e3c8bf945fd617d77fe1abfc564cb65c

# 2. Disable AVB using the STOCK vbmeta (see note below), then flash TWRP
./adb reboot bootloader
./fastboot --disable-verity --disable-verification flash vbmeta ../RedmiNote8/stock/vbmeta.img
./fastboot flash recovery ../RedmiNote8/twrp-3.6.2_9-0-ginkgo.img
```

```
# 3. Enter TWRP by HARDWARE KEYS. Do not let MIUI boot.
#    `fastboot reboot recovery` is unreliable here and tends to land in MIUI,
#    which immediately wipes TWRP (see gotcha 3).
#
#    - unplug USB
#    - hold Power ~10-15s until the screen goes fully black
#    - immediately hold Volume Up + Power together
#    - at the splash, RELEASE POWER but KEEP HOLDING VOLUME UP until TWRP appears
```

Releasing Volume Up at the splash is the common mistake — it continues into MIUI and destroys the flash.

### On the vbmeta image

Use the **stock** `vbmeta.img` with the `--disable-verity --disable-verification` flags. Those flags make fastboot patch the disable bits into the real header (it prints `Rewriting vbmeta struct at offset: 0`) while preserving its descriptors: the `recovery` and `system` chain partitions, the `vendor` hashtree, and the `dtbo`/`boot` hashes.

Do **not** substitute a blank `avbtool make_vbmeta_image` output — it has no descriptors and throws all of that away.

Stock images come from the fastboot ROM matching `ro.build.version.incremental`:

```sh
# 3.5GB; md5 c827ec74de631cad987ec879243ff505 (matches the hash in the filename)
F=ginkgo_id_global_images_V11.0.7.0.PCOIDXM_20201010.0000.00_9.0_global_c827ec74de.tgz
curl -o "roms/$F" "https://cdnorg.d.miui.com/V11.0.7.0.PCOIDXM/$F"
tar -xzv --fast-read -C RedmiNote8/stock --strip-components=2 -f "roms/$F" \
  '*/images/vbmeta.img' '*/images/boot.img' '*/images/recovery.img'
```

`stock/recovery.img` and `stock/boot.img` are kept as the restore path.

Confirming AVB actually got disabled — these go **empty** afterwards (they read `enforcing` / a digest / `5568` beforehand):

```sh
./adb shell getprop ro.boot.veritymode
./adb shell getprop ro.boot.vbmeta.digest
./adb shell getprop ro.boot.vbmeta.size
```

Flashing vbmeta did **not** wipe `/data` on this device, despite the theoretical keymaster/FBE risk.

> [!WARNING]
> **Never relock the bootloader** while vbmeta has verification disabled or TWRP is
> flashed. That combination will not boot and normal fastboot recovery won't save it —
> it needs EDL mode + MiFlash. Restore `stock/vbmeta.img` (no disable flags) and
> `stock/recovery.img` first if relocking is ever wanted.

> [!TODO]
> - Root: flash Magisk (`Magisk-v30.7.apk`, minSdk 23 so Android 9 is fine) from TWRP.
>   Doing this from TWRP also neutralises `install-recovery.sh`, which is what makes
>   TWRP finally persist across reboots.

## Remote capture

`capture` drives the stock MIUI camera and prints the absolute path of the
resulting JPEG on stdout — one line, nothing else. It **must be run as root**
(see gotcha 1), and `su` does not have Termux's `bin` on its `PATH`, so it needs
the full path:

```sh
ssh iot-redmi 'su -c $PREFIX/bin/capture'
# /storage/emulated/0/DCIM/Camera/IMG_20260901_210104.jpg

scp iot-redmi:"$(ssh iot-redmi 'su -c $PREFIX/bin/capture')" .   # shoot and pull
```

`$PREFIX` is expanded by the Termux login shell before `su` runs, so the single
quotes are what makes that work.

Install (verified working 2026-09-01, from screen-off and locked):

```sh
scp capture iot-redmi:/data/data/com.termux/files/usr/bin/capture
ssh iot-redmi 'chmod 755 /data/data/com.termux/files/usr/bin/capture'
```

One-time device setup — Termux ships with the storage permissions declared but
**not granted**, so the SSH user gets `Permission denied` on the returned path
even though the capture itself succeeded:

```sh
ssh iot-redmi 'su -c "pm grant com.termux android.permission.READ_EXTERNAL_STORAGE"'
ssh iot-redmi 'su -c "pm grant com.termux android.permission.WRITE_EXTERNAL_STORAGE"'
```

### Three things that make this fail

1. **SSH lands as an untrusted app, not root.** `ssh iot-redmi id` gives
   `u0_a183 … context=u:r:untrusted_app:s0`, and from there `dumpsys window`
   returns *nothing at all* rather than an error. `input`, `am` and `wm` are the
   same. Hence `su -c`. Magisk grants it non-interactively — no prompt on the
   device.

2. **The keyguard steals the shutter.** After waking, the camera can already be
   `ResumedActivity` while `mCurrentFocus` is still `StatusBar`. `input keyevent
   27` then goes to the lockscreen and does nothing at all — no photo, no error.
   `wm dismiss-keyguard` is what actually hands focus over. The script then waits
   for `mCurrentFocus` to name `com.android.camera` rather than sleeping a fixed
   time. (This device has no PIN/pattern; a secure lock would block this.)

3. **The JPEG is written in two stages, and the first one looks complete.** A
   ~130 KB EXIF/thumbnail header lands first, then the full ~2.5 MB image
   arrives in one jump ~100 ms later. Returning as soon as the file appears
   hands back a truncated image. Worse, the embedded EXIF thumbnail carries its
   own `ff d9` end-of-image marker, so even "the size is steady *and* it ends in
   EOI" reports success at a twentieth of the real size. What actually works is
   just waiting for the size to stop changing, sampled a second apart — the stub
   plateau is far too short to survive that.

The newest shot is found with `ls "$DIR"/IMG_* | tail -1`: these filenames are
`IMG_<date>_<time>.jpg`, so lexical order is chronological. The `IMG_*` glob is
load-bearing — a `VID_*` file would sort last forever and hang the wait loop.
The script blanks the screen when it is done.

## Power Management

> [!ai] Gemini on ACC
> If the Redmi Note 8’s charging hardware (PMIC) supports it, ACC can enable "Battery Idle." This tells the phone to cut off power to the battery entirely and run the motherboard directly off the USB cable's electricity. The battery just sits there completely idle at whatever percentage you chose.
