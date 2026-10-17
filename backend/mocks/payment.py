"""Mock payment gateway callback: python mocks/payment.py 1 --success   (or --fail)"""

import argparse
import json
import urllib.error
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("payment_id", type=int)
result = parser.add_mutually_exclusive_group(required=True)
result.add_argument("--success", action="store_true")
result.add_argument("--fail", action="store_true")
parser.add_argument("--url", default="http://localhost:8000")
args = parser.parse_args()

request = urllib.request.Request(
    f"{args.url}/api/payments/{args.payment_id}/mock",
    data=json.dumps({"success": args.success}).encode(),
    headers={"Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(request) as response:
        print(response.status, response.read().decode())
except urllib.error.HTTPError as error:
    print(error.code, error.read().decode())
