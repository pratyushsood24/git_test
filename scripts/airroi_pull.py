#!/usr/bin/env python3
"""
AirROI Airbnb Data API client — pulls Canberra / Higgins short-term-rental data
for the STR-vs-long-term decision on 54 Ashburner St, Higgins ACT 2615.

Usage
-----
    export AIRROI_API_KEY="your-key"          # never hard-code / commit the key
    python scripts/airroi_pull.py \
        --lat -35.2360 --lng 149.0330 \
        --radius-km 5 --bedrooms 3 --guests 6 \
        --market "north-canberra" --out data/

All raw responses are written to --out as JSON, plus a call log (provenance).

NOTE ON ENDPOINTS
-----------------
AirROI exposes ~22 REST endpoints (Listings / Markets / Calculator groups). The
exact paths below are set from the public docs at https://www.airroi.com/api/documentation
and are overridable via the ENDPOINTS dict so a doc change is a one-line fix.
On the first successful call we verify the response shape and adjust if needed.
Monetary values: AirROI returns AU market data; we record the currency field and
do NOT assume a unit — the model labels currency explicitly.
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

# Endpoint paths — verify against live docs on first call; override here if they differ.
ENDPOINTS = {
    "market_summary":   "/v1/markets/summary",       # occupancy, ADR, RevPAR, revenue, active listings
    "market_seasonality": "/v1/markets/seasonality", # monthly occupancy & ADR curve
    "listings_search":  "/v1/listings/search",       # search by radius / polygon
    "listing_analytics": "/v1/listings/analytics",   # per-listing occupancy/ADR/annual revenue
    "listing_comparables": "/v1/listings/comparables",
    "calculator":       "/v1/calculator/estimate",   # revenue projection from bd/guests/location
}

MAX_RETRIES = 4
BACKOFF_BASE = 2  # seconds: 2, 4, 8, 16


def _key() -> str:
    key = os.environ.get("AIRROI_API_KEY")
    if not key:
        sys.exit("ERROR: set AIRROI_API_KEY in the environment (do not hard-code it).")
    return key


def call(path: str, params: dict | None = None) -> dict:
    """GET an AirROI endpoint with retry/backoff. Returns parsed JSON."""
    url = BASE_URL.rstrip("/") + path
    if params:
        url += "?" + urlencode({k: v for k, v in params.items() if v is not None})
    headers = {
        "Authorization": f"Bearer {_key()}",
        "X-Api-Key": _key(),          # AirROI accepts key via header; send both common forms
        "Accept": "application/json",
        "User-Agent": "canberra-str-research/1.0",
    }
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            req = Request(url, headers=headers, method="GET")
            with urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
                return {"_status": resp.status, "_url": url, "data": json.loads(body)}
        except HTTPError as e:
            # 4xx (auth/quota/bad-param) won't fix on retry — surface immediately.
            detail = e.read().decode("utf-8", "replace")[:500]
            if 400 <= e.code < 500 and e.code not in (429,):
                return {"_status": e.code, "_url": url, "error": detail}
            last_err = f"HTTP {e.code}: {detail}"
        except (URLError, TimeoutError) as e:
            last_err = str(e)
        if attempt < MAX_RETRIES - 1:
            time.sleep(BACKOFF_BASE ** (attempt + 1))
    return {"_status": None, "_url": url, "error": f"failed after retries: {last_err}"}


def save(out_dir: Path, name: str, payload: dict, log: list) -> None:
    path = out_dir / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2))
    status = payload.get("_status")
    log.append({"name": name, "status": status, "url": payload.get("_url"),
                "ok": status == 200, "ts": datetime.now(timezone.utc).isoformat()})
    flag = "OK " if status == 200 else "ERR"
    print(f"[{flag}] {name:22} status={status}  -> {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Pull AirROI STR data for Canberra/Higgins.")
    ap.add_argument("--lat", type=float, default=-35.2360, help="property latitude")
    ap.add_argument("--lng", type=float, default=149.0330, help="property longitude")
    ap.add_argument("--radius-km", type=float, default=5.0)
    ap.add_argument("--bedrooms", type=int, default=3)
    ap.add_argument("--guests", type=int, default=6)
    ap.add_argument("--market", default="north-canberra",
                    help="AirROI market slug/id (Higgins sits in North Canberra)")
    ap.add_argument("--out", default="data", help="output directory")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    log: list = []

    # 1) Market-level metrics
    save(out_dir, "market_summary",
         call(ENDPOINTS["market_summary"], {"market": args.market}), log)
    save(out_dir, "market_seasonality",
         call(ENDPOINTS["market_seasonality"], {"market": args.market}), log)

    # 2) Comparable listings around the property
    save(out_dir, "listings_search",
         call(ENDPOINTS["listings_search"],
              {"lat": args.lat, "lng": args.lng, "radius": args.radius_km,
               "bedrooms": args.bedrooms}), log)

    # 3) AirROI's own revenue projection for this property config
    save(out_dir, "calculator",
         call(ENDPOINTS["calculator"],
              {"lat": args.lat, "lng": args.lng,
               "bedrooms": args.bedrooms, "guests": args.guests}), log)

    (out_dir / "call_log.json").write_text(json.dumps(log, indent=2))
    ok = sum(1 for r in log if r["ok"])
    print(f"\nDone: {ok}/{len(log)} calls succeeded. Log -> {out_dir/'call_log.json'}")
    if ok == 0:
        print("No calls succeeded — check the API key, that api.airroi.com is allowlisted, "
              "and confirm endpoint paths against https://www.airroi.com/api/documentation")


if __name__ == "__main__":
    main()
