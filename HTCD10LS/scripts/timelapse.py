#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument("output_dir", help="Local directory to save images")
    p.add_argument("--ssh-host", default="iot-htc10")
    p.add_argument("--remote-cmd", default="sh /data/dha/camera_routine.sh")
    args = p.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    result = subprocess.run(
        ["ssh", args.ssh_host, args.remote_cmd],
        capture_output=True,
        text=True,
        check=True,
    )

    lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    if not lines:
        sys.exit("error: no output from remote command")
    image_path = lines[-1]
    print(f"captured: {image_path}")

    subprocess.run(
        ["scp", f"{args.ssh_host}:{image_path}", f"{args.output_dir}/"],
        check=True,
    )

    local_path = os.path.join(args.output_dir, os.path.basename(image_path))
    print(f"downloaded to: {local_path}")


if __name__ == "__main__":
    main()
