"""TC-17 (NFR-01): time from an entry event to the barrier opening, p95 <= 3000 ms.

python mocks/perf_tc17.py [--url http://localhost:8000] [--n 100]
Run it against a throwaway database, see docs/testing/tc17-results.md.
"""

import argparse
import json
import math
import os
import statistics
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

LIMIT_MS = 3000


def p95(values: list[float]) -> float:
    """Nearest-rank 95th percentile."""
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def entry_latency_ms(url: str, i: int) -> float:
    body = {
        "plate": f"30A-{100 + i:03d}.{i % 100:02d}",
        "confidence": 0.95,
        "gate_id": "IN-1",
        "timestamp": datetime.now(timezone(timedelta(hours=7))).isoformat(),
    }
    request = urllib.request.Request(
        f"{url}/api/lpr-events",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Device-Key": os.environ.get("SPMS_DEVICE_KEY", "dev-device-key"),
        },
    )
    start = time.perf_counter()
    with urllib.request.urlopen(request) as response:
        event = json.load(response)
    elapsed = (time.perf_counter() - start) * 1000
    if event["barrier_opened_at"] is None:
        raise SystemExit(f"event {i}: barrier did not open ({event['action']})")
    return elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--n", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.n <= 900:  # plates below carry a 3-digit counter
        parser.error("--n must be between 1 and 900")

    times = [entry_latency_ms(args.url, i) for i in range(args.n)]
    result = p95(times)
    print(
        f"count={len(times)} mean={statistics.mean(times):.1f} ms "
        f"p95={result:.1f} ms max={max(times):.1f} ms limit={LIMIT_MS} ms"
    )
    return 0 if result <= LIMIT_MS else 1


if __name__ == "__main__":
    sys.exit(main())
