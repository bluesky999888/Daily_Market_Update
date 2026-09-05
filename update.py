#!/usr/bin/env python3
"""
update.py
Master orchestrator script that runs the data fetch and commentary generation pipeline.
Usage:
    python update.py
    python update.py --market-only
    python update.py --commentary-only
"""

import argparse
import os
import sys
import time
from datetime import datetime

import fetch_market_data
import generate_commentary


def run_pipeline(market_only=False, commentary_only=False):
    start_time = time.time()
    print("=" * 65)
    print(f" Daily Market Summary Pipeline Starting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    if not commentary_only:
        print("\n--- [Step 1/2] Fetching Live Market Data ---")
        try:
            market_data = fetch_market_data.fetch_all()
            tiles_count = len(market_data.get("tiles", []))
            extras_count = len(market_data.get("extras", []))
            errors_count = len(market_data.get("errors", []))
            print(f"[OK] Market data complete: {tiles_count} tiles, {extras_count} extras, {errors_count} errors.")
        except Exception as e:
            print(f"[FAIL] Error fetching market data: {e}", file=sys.stderr)
            if not market_only:
                print("Aborting commentary generation due to market fetch failure.", file=sys.stderr)
            sys.exit(1)

    if not market_only:
        print("\n--- [Step 2/2] Generating AI Commentary & Grounded Sources ---")
        try:
            commentary = generate_commentary.generate_commentary()
            panels_count = len(commentary.get("panels", {}))
            sources_count = len(commentary.get("sources", []))
            print(f"[OK] Commentary complete: {panels_count} panels, {sources_count} sources.")
        except Exception as e:
            print(f"[FAIL] Error generating commentary: {e}", file=sys.stderr)
            sys.exit(1)

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(f" Daily Market Summary Pipeline Succeeded in {elapsed:.2f}s")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Update Daily Market Summary data and commentary.")
    parser.add_argument("--market-only", action="store_true", help="Only fetch market.json data")
    parser.add_argument("--commentary-only", action="store_true", help="Only generate commentary.json")
    args = parser.parse_args()

    run_pipeline(market_only=args.market_only, commentary_only=args.commentary_only)


if __name__ == "__main__":
    main()
