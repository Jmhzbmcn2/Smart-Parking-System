"""Mock slot sensor: python mocks/sensor.py T1-A-05 --occupied   (or --free)"""

import argparse
import json
import os
import urllib.error
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("slot_id")
state = parser.add_mutually_exclusive_group(required=True)
state.add_argument("--occupied", action="store_true")
state.add_argument("--free", action="store_true")
parser.add_argument("--url", default="http://localhost:8000")
args = parser.parse_args()

request = urllib.request.Request(
    f"{args.url}/api/sensor-events",
    data=json.dumps({"slot_id": args.slot_id, "occupied": args.occupied}).encode(),
    headers={
        "Content-Type": "application/json",
        "X-Device-Key": os.environ.get("SPMS_DEVICE_KEY", "dev-device-key"),
    },
)
try:
    with urllib.request.urlopen(request) as response:
        print(response.status, response.read().decode())
except urllib.error.HTTPError as error:
    print(error.code, error.read().decode())
