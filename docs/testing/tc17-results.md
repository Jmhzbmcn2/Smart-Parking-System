# TC-17 results: gate latency (NFR-01)

NFR-01: from a valid entry event to the barrier opening, p95 <= 3 seconds.

`mocks/perf_tc17.py` sends 100 entry events one after another (plates `30A-100.00` to `30A-199.99`). For each event it measures the client-side time from sending the request to receiving a response whose `barrier_opened_at` is set. It prints the count, mean, p95 (nearest rank) and max, and exits non-zero when p95 is above 3000 ms.

## How to run

Run against a throwaway database, so the demo database stays clean. Run both commands from the repository root. Start the backend (terminal 1), then run the script (terminal 2).

PowerShell:

```text
$env:SPMS_DATABASE_URL = "sqlite:///perf.db"
uv run --directory backend fastapi run app/main.py --port 8002
```

```text
uv run --directory backend python mocks/perf_tc17.py --url http://127.0.0.1:8002 --n 100
```

Git Bash:

```text
SPMS_DATABASE_URL=sqlite:///perf.db uv run --directory backend fastapi run app/main.py --port 8002
```

```text
uv run --directory backend python mocks/perf_tc17.py --url http://127.0.0.1:8002 --n 100
```

Stop the backend afterwards and delete `backend/perf.db` (it is git-ignored).

Use `127.0.0.1`, not `localhost`. On this Windows machine `localhost` resolves to IPv6 first and each request waits about 2 seconds for the fallback to IPv4. That is a client connection delay, not gate latency.

## Result

| Item | Value |
|---|---|
| Date | 2026-10-17 |
| Machine | 12th Gen Intel Core i5-12500H, 15.7 GB RAM, Windows 11 Home |
| Software | Python 3.13 (uv), FastAPI `fastapi run`, SQLite file database, one worker |
| Events | 100 entry events, sequential, distinct plates |

Output of the run:

```text
count=100 mean=10.0 ms p95=11.8 ms max=95.1 ms limit=3000 ms
```

Exit code 0. p95 = 11.8 ms, far below the 3000 ms target, so **TC-17 passes for the software path** (HTTP request, plate handling, database writes, barrier mock).

## Scope and limits

- The barrier is a mock and the camera is a script. The measurement covers the software only; real camera capture and barrier hardware time are outside it.
- Load is one request at a time on one machine. NFR-06 (1000 slots) is assessed by analysis, not by this test.
