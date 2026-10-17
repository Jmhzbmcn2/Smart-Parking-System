"""Mock LPR camera: python mocks/lpr.py 30A-123.45 --gate IN-1 --confidence 0.95"""

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("plate")
parser.add_argument("--gate", default="IN-1")
parser.add_argument("--confidence", type=float, default=0.95)
parser.add_argument("--url", default="http://localhost:8000")
args = parser.parse_args()

body = {
    "plate": args.plate,
    "confidence": args.confidence,
    "gate_id": args.gate,
    "timestamp": datetime.now(timezone(timedelta(hours=7))).isoformat(),
}
request = urllib.request.Request(
    f"{args.url}/api/lpr-events",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(request) as response:
        print(response.status, response.read().decode())
except urllib.error.HTTPError as error:
    print(error.code, error.read().decode())
