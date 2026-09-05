#!/usr/bin/env python3
"""
fetch_market_data.py
Fetches global market index, yield, FX, and commodity data from Yahoo Finance
and writes public/market.json according to the reference schema.
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

TILES_CONFIG = [
    {"name": "S&P 500", "symbol": "^GSPC", "decimals": 2, "currency": "USD"},
    {"name": "Nasdaq Composite", "symbol": "^IXIC", "decimals": 2, "currency": "USD"},
    {"name": "Dow Jones", "symbol": "^DJI", "decimals": 2, "currency": "USD"},
    {"name": "FTSE 100", "symbol": "^FTSE", "decimals": 1, "currency": "GBP"},
    {"name": "DAX", "symbol": "^GDAXI", "decimals": 1, "currency": "EUR"},
    {"name": "Nikkei 225", "symbol": "^N225", "decimals": 1, "currency": "JPY"},
    {"name": "Hang Seng", "symbol": "^HSI", "decimals": 1, "currency": "HKD"},
    {"name": "ASX 200", "symbol": "^AXJO", "decimals": 1, "currency": "AUD"},
]

EXTRAS_CONFIG = [
    {"name": "CAC 40", "symbol": "^FCHI", "decimals": 1, "group": "europe", "currency": "EUR"},
    {"name": "10Y yield", "symbol": "^TNX", "decimals": 2, "group": "us", "unit": "%", "currency": "USD"},
    {"name": "30Y yield", "symbol": "^TYX", "decimals": 2, "group": "us", "unit": "%", "currency": "USD"},
    {"name": "DXY", "symbol": "DX-Y.NYB", "decimals": 2, "group": "fx", "currency": "USD"},
    {"name": "USD/JPY", "symbol": "JPY=X", "decimals": 2, "group": "fx", "currency": "JPY"},
    {"name": "EUR/USD", "symbol": "EURUSD=X", "decimals": 4, "group": "fx", "currency": "USD"},
    {"name": "AUD/USD", "symbol": "AUDUSD=X", "decimals": 4, "group": "fx", "currency": "USD"},
    {"name": "WTI Crude", "symbol": "CL=F", "decimals": 2, "group": "commodities", "unit": "$", "currency": "USD"},
    {"name": "Brent Crude", "symbol": "BZ=F", "decimals": 2, "group": "commodities", "unit": "$", "currency": "USD"},
    {"name": "Gold", "symbol": "GC=F", "decimals": 2, "group": "commodities", "unit": "$", "currency": "USD"},
    {"name": "Bitcoin", "symbol": "BTC-USD", "decimals": 0, "group": "commodities", "unit": "$", "currency": "USD"},
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
]


def fetch_quote(cfg, max_retries=3):
    symbol = cfg["symbol"]
    encoded_sym = urllib.parse.quote(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded_sym}?interval=1d&range=5d"

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENTS[attempt % len(USER_AGENTS)],
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                result = data.get("chart", {}).get("result", [])
                if not result:
                    raise ValueError(f"No chart result in payload: {data.get('chart', {}).get('error')}")

                meta = result[0].get("meta", {})
                price = meta.get("regularMarketPrice")

                # Fallback to last close in indicators if regularMarketPrice is missing
                if price is None:
                    indicators = result[0].get("indicators", {}).get("quote", [{}])[0]
                    closes = [c for c in indicators.get("close", []) if c is not None]
                    if closes:
                        price = closes[-1]

                if price is None:
                    raise ValueError("Price not found")

                prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
                if not prev_close:
                    indicators = result[0].get("indicators", {}).get("quote", [{}])[0]
                    closes = [c for c in indicators.get("close", []) if c is not None]
                    if len(closes) >= 2:
                        prev_close = closes[-2]
                    elif closes:
                        prev_close = closes[0]
                    else:
                        prev_close = price

                change = price - prev_close
                pct = ((price - prev_close) / prev_close) * 100.0 if prev_close else 0.0

                # Session date formatting
                market_time = meta.get("regularMarketTime")
                if market_time:
                    session_date = datetime.fromtimestamp(market_time, tz=timezone.utc).strftime("%Y-%m-%d")
                else:
                    session_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                row = {
                    "name": cfg["name"],
                    "symbol": cfg["symbol"],
                    "decimals": cfg.get("decimals", 2),
                    "level": float(price),
                    "change": float(change),
                    "pct": float(pct),
                    "session_date": session_date,
                    "currency": meta.get("currency") or cfg.get("currency", "USD"),
                }

                if "group" in cfg:
                    row["group"] = cfg["group"]
                if "unit" in cfg:
                    row["unit"] = cfg["unit"]

                return row, None
        except Exception as e:
            if attempt == max_retries - 1:
                return None, f"{symbol}: {e}"
            time.sleep(1.0)

    return None, f"{symbol}: Unknown failure"


def fetch_all():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching market data...")
    tiles = []
    extras = []
    errors = []

    # Fetch tiles
    for cfg in TILES_CONFIG:
        row, err = fetch_quote(cfg)
        if row:
            tiles.append(row)
            pct_sign = "+" if row["pct"] >= 0 else ""
            print(f"  [Tile]  {row['name']:18} : {row['level']:.2f} ({pct_sign}{row['pct']:.2f}%)")
        else:
            errors.append(err)
            print(f"  [Tile]  {cfg['name']:18} : ERROR ({err})")

    # Fetch extras
    for cfg in EXTRAS_CONFIG:
        row, err = fetch_quote(cfg)
        if row:
            extras.append(row)
            pct_sign = "+" if row["pct"] >= 0 else ""
            print(f"  [Extra] {row['name']:18} : {row['level']:.4f} ({pct_sign}{row['pct']:.2f}%)")
        else:
            errors.append(err)
            print(f"  [Extra] {cfg['name']:18} : ERROR ({err})")

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    market_data = {
        "updated": now_iso,
        "tiles": tiles,
        "extras": extras,
        "errors": errors,
    }

    # Save to public/market.json
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "market.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(market_data, f, indent=2)

    print(f"Saved market data to {out_path} ({len(tiles)} tiles, {len(extras)} extras, {len(errors)} errors)")
    return market_data


if __name__ == "__main__":
    fetch_all()
