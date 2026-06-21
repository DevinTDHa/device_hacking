#!/usr/bin/env python3
import argparse
import logging
import os
import subprocess
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("timelapse")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("output_dir", help="Local directory to save images")
    p.add_argument("--ssh-host", default="iot-htc10")
    p.add_argument("--remote-cmd", default="sh /data/dha/camera_routine.sh")
    args = p.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    log.info("Sending command to phone.")
    result = subprocess.run(
        ["ssh", args.ssh_host, args.remote_cmd],
        capture_output=True,
        text=True,
        check=True,
    )

    lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    if not lines:
        log.error("no output from remote command")
        sys.exit(1)
    image_path = lines[-1]
    log.info("captured: %s", image_path)

    ext = os.path.splitext(os.path.basename(image_path))[1]
    local_path = os.path.join(args.output_dir, f"{int(time.time())}{ext}")

    subprocess.run(
        ["scp", f"{args.ssh_host}:{image_path}", local_path],
        check=True,
    )

    log.info("downloaded to: %s", local_path)


if __name__ == "__main__":
    main()
