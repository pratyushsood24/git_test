#!/usr/bin/env python3
"""
AirROI Airbnb Data API client — pulls Canberra / Higgins short-term-rental data
for the STR-vs-long-term decision on 54 Ashburner St, Higgins ACT 2615.

Verified against the live API (api.airroi.com) on 2026-08-08.

Usage
-----
    export AIRROI_API_KEY="your-key"        # never hard-code / commit the key
    python scripts/airroi_pull.py --lat -35.2360 --lng 149.0330 \
        --bedrooms 4 --baths 2 --guests 8 --radius-miles 3 --out data/

Auth: the key goes in the `x-api-key` header. Do NOT send an Authorization
header — API Gateway parses it as AWS SigV4 and rejects the request.
Money is returned in the market's native currency (AUD here) when currency=native.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = os.environ.get("AIRROI_BASE_URL", "https://api.airroi.com")
MAX_RETRIES = 4
BACKOFF_BASE = 2  # 2, 4, 8, 16s

# The property's markets (from GET /markets/lookup?lat&lng and /markets/search).
MARKETS = {
    "higgins": {"country": "Australia", "region": "Australian Capital Territory",
                "locality": "District of Belconnen", "district": "Higgins"},
    "belconnen": {"country": "Australia", "region": "Australian Capital Territory",
                  "locality": "District of Belconnen", "district": ""},
    "north_canberra": {"country": "Australia", "region": "Australian Capital Territory",
                       "locality": "North Canberra", "district": ""},
    "canberra": {"country": "Australia", "region": "Australian Capital Territory",
                 "locality": "Canberra", "district": ""},
}


def _key() -> str:
    key = os.environ.get("AIRROI_API_KEY")
    if not key:
        sys.exit("ERROR: set AIRROI_API_KEY in the environment (do not hard-code it).")
    return key


def _request(method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
    url = BASE_URL.rstrip("/") + path
    if params:
        url += "?" + urlencode({k: v for k, v in params.items() if v is not None})
    data = json.dumps(body).encode() if body is not None else None
    headers = {"x-api-key": _key(), "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            req = Request(url, data=data, headers=headers, method=method)
            with urlopen(req, timeout=60) as resp:
                return {"_status": resp.status, "_url": url, "data": json.loads(resp.read().decode())}
        except HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            if 400 <= e.code < 500 and e.code != 429:
                return {"_status": e.code, "_url": url, "error": detail}
            last_err = f"HTTP {e.code}: {detail}"
        except (URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = str(e)
        if attempt < MAX_RETRIES - 1:
            time.sleep(BACKOFF_BASE ** (attempt + 1))
    return {"_status": None, "_url": url, "error": f"failed after retries: {last_err}"}


def get(path, params=None):
    return _request("GET", path, params=params)


def post(path, body):
    return _request("POST", path, body=body)


def save(out_dir: Path, name: str, payload: dict, log: list) -> None:
    (out_dir / f"{name}.json").write_text(json.dumps(payload.get("data", payload), indent=2))
    status = payload.get("_status")
    log.append({"name": name, "status": status, "ok": status == 200,
                "url": payload.get("_url"), "error": payload.get("error"),
                "ts": datetime.now(timezone.utc).isoformat()})
    print(f"[{'OK ' if status == 200 else 'ERR'}] {name:28} status={status}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Pull AirROI STR data for Higgins/Canberra.")
    ap.add_argument("--lat", type=float, default=-35.2360)
    ap.add_argument("--lng", type=float, default=149.0330)
    ap.add_argument("--bedrooms", type=int, default=4)
    ap.add_argument("--baths", type=float, default=2)
    ap.add_argument("--guests", type=int, default=8)
    ap.add_argument("--radius-miles", type=float, default=3.0)
    ap.add_argument("--num-months", type=int, default=12)
    ap.add_argument("--currency", default="native", choices=["native", "usd"])
    ap.add_argument("--out", default="data")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    log: list = []
    cur = args.currency

    # 1) Confirm the market for the coordinates
    save(out, "market_lookup", get("/markets/lookup", {"lat": args.lat, "lng": args.lng}), log)

    # 2) Market summaries + full metrics
    for name, mkt in MARKETS.items():
        save(out, f"market_summary_{name}",
             post("/markets/summary", {"market": mkt, "currency": cur, "num_months": args.num_months}), log)
    save(out, "market_metrics_belconnen",
         post("/markets/metrics/all",
              {"market": MARKETS["belconnen"], "currency": cur, "num_months": args.num_months}), log)

    # 3) Property-specific revenue projection + comparables (bedrooms/baths/guests required)
    est_params = {"lat": args.lat, "lng": args.lng, "bedrooms": args.bedrooms,
                  "baths": args.baths, "guests": args.guests, "currency": cur}
    save(out, "calculator_estimate", get("/calculator/estimate", est_params), log)
    save(out, "comparables",
         get("/listings/comparables",
             {"latitude": args.lat, "longitude": args.lng, "bedrooms": args.bedrooms,
              "baths": args.baths, "guests": args.guests, "currency": cur}), log)

    # 4) Comparable active listings within a radius
    save(out, "listings_search_radius",
         post("/listings/search/radius",
              {"latitude": args.lat, "longitude": args.lng, "radius_miles": args.radius_miles}), log)

    (out / "call_log.json").write_text(json.dumps(log, indent=2))
    ok = sum(1 for r in log if r["ok"])
    print(f"\nDone: {ok}/{len(log)} calls succeeded -> {out}/call_log.json")
    if ok < len(log):
        print("Some calls failed — check the key, that api.airroi.com is allowlisted, and the call_log.")


if __name__ == "__main__":
    main()
