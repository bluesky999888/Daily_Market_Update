#!/usr/bin/env python3
"""
generate_commentary.py
Fetches market context from financial news RSS feeds, reads public/market.json,
and prompts Google Gemini (gemini-3.6-flash) to generate analytical commentary
and news sources according to the reference schema.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


def fetch_rss_news(max_items=15):
    news_items = []
    feeds = [
        ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ]

    for source_name, url in feeds:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                root = ET.fromstring(resp.read())
                items = root.findall("./channel/item")
                for it in items[:max_items]:
                    title_elem = it.find("title")
                    link_elem = it.find("link")
                    if title_elem is not None and title_elem.text:
                        title = title_elem.text.strip()
                        link = link_elem.text.strip() if link_elem is not None else ""
                        news_items.append({"title": title, "link": link, "source": source_name})
        except Exception as e:
            print(f"Warning: Failed to fetch RSS feed {source_name}: {e}", file=sys.stderr)

    return news_items


def build_market_summary_text(market_data):
    lines = []
    lines.append(f"Market Data Timestamp: {market_data.get('updated')}")
    lines.append("\n--- Major Global Indices (Tiles) ---")
    for t in market_data.get("tiles", []):
        pct = t.get("pct", 0.0)
        sign = "+" if pct >= 0 else ""
        lines.append(f"- {t['name']}: {t['level']:.2f} ({sign}{pct:.2f}%) [Session: {t.get('session_date')}]")

    lines.append("\n--- Additional Key Assets (Rates, FX, Commodities, Crypto) ---")
    for e in market_data.get("extras", []):
        pct = e.get("pct", 0.0)
        sign = "+" if pct >= 0 else ""
        lines.append(f"- [{e.get('group', 'other').upper()}] {e['name']}: {e['level']:.4f} ({sign}{pct:.2f}%)")

    return "\n".join(lines)


def generate_commentary():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    market_path = os.path.join(base_dir, "public", "market.json")
    commentary_path = os.path.join(base_dir, "public", "commentary.json")

    if not os.path.exists(market_path):
        print(f"Error: {market_path} does not exist. Run fetch_market_data.py first.", file=sys.stderr)
        sys.exit(1)

    with open(market_path, "r", encoding="utf-8") as f:
        market_data = json.load(f)

    api_key = (
        os.environ.get("GOOGLE_AI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or ""
    ).strip()

    if not api_key:
        print("Error: Neither GOOGLE_AI_API_KEY nor GEMINI_API_KEY is set in environment.", file=sys.stderr)
        sys.exit(1)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching financial news context...")
    news_items = fetch_rss_news()
    news_text = "\n".join([f"- {it['title']} ({it['source']}: {it['link']})" for it in news_items[:18]])

    market_summary = build_market_summary_text(market_data)

    # Determine default session label from tiles
    dates = [t.get("session_date") for t in market_data.get("tiles", []) if t.get("session_date")]
    latest_date = sorted(dates)[-1] if dates else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        dt = datetime.strptime(latest_date, "%Y-%m-%d")
        default_label = f"{dt.strftime('%a')}, {dt.day} {dt.strftime('%b %Y')} session"
    except Exception:
        default_label = f"{latest_date} session"

    system_instructions = (
        "You are a Senior Global Macro & Financial Markets Editor for a premier institutional daily market briefing.\n"
        "Your task is to produce the daily market summary commentary matching this exact schema and editorial tone.\n\n"
        "EDITORIAL GUIDELINES:\n"
        "1. Numbers live in market.json and MUST NEVER be repeated or duplicated in prose! (Do NOT state 'rose 0.5%' or 'closed at 5,000').\n"
        "2. Use prose strictly to explain the DRIVERS, macro context, sector performance, central bank expectations, and investor sentiment.\n"
        "3. Emphasize key entities, indices, commodities, currencies, and institutions with <strong> HTML tags.\n"
        "   Examples: <strong>S&P 500</strong>, <strong>Nasdaq</strong>, <strong>Treasury yields</strong>, <strong>Brent crude</strong>, <strong>yen</strong>, <strong>Federal Reserve</strong>.\n"
        "4. Tone: Objective, concise, sophisticated, Financial Times / Bloomberg caliber.\n"
        "5. Panels to provide:\n"
        "   - 'us': 2 bullets on US equities, tech/cyclical rotation, Treasury yields influence, risk appetite.\n"
        "   - 'europe': 2 bullets on European markets (DAX, CAC 40, FTSE 100) and regional macro/geopolitics.\n"
        "   - 'asia': 2 bullets on Asia-Pacific (Nikkei 225, Hang Seng, ASX 200) and regional central banks/economic trends.\n"
        "   - 'fx': 2 bullets on US Dollar (DXY), Japanese yen, Euro, Australian dollar.\n"
        "   - 'commodities': 2 bullets on Crude oil (WTI/Brent, supply/geopolitics), Gold, and Bitcoin.\n"
        "   - 'central_banks': 2-3 bullets on Fed policy outlook, rate hike/cut bets, inflation/jobs prints, global central banks.\n"
        "6. Sources: 5-8 relevant financial news sources with valid 'name' and 'url' (from provided news or reputable financial publications like Yahoo Finance, Bloomberg, Reuters, CNBC, Financial Times).\n"
        "7. Format: Output MUST be pure JSON with keys: session_label, panels, sources.\n"
    )

    user_prompt = (
        f"TODAY'S MARKET MOVEMENTS:\n{market_summary}\n\n"
        f"LATEST HEADLINES AND NEWS CONTEXT:\n{news_text}\n\n"
        f"Default session label to use or adapt: '{default_label}'.\n\n"
        "Generate the structured JSON commentary."
    )

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Generating commentary with Gemini 3.6 Flash...")

    model_name = "gemini-3.6-flash"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_instructions}\n\n{user_prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.4,
        },
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidate = data.get("candidates", [{}])[0]
            content = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
            commentary_json = json.loads(content)

            # Add metadata comment and updated timestamp
            commentary_json["_comment"] = "Prose authored by Gemini 3.6 Flash. Numbers live in market.json."
            commentary_json["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if "session_label" not in commentary_json:
                commentary_json["session_label"] = default_label

            with open(commentary_path, "w", encoding="utf-8") as f:
                json.dump(commentary_json, f, indent=2)

            print(f"Successfully generated and saved commentary to {commentary_path}")
            print(f"Session: {commentary_json.get('session_label')}")
            print(f"Panels populated: {list(commentary_json.get('panels', {}).keys())}")
            print(f"Sources listed: {len(commentary_json.get('sources', []))}")
            return commentary_json
    except Exception as e:
        print(f"Error calling Gemini API: {e}", file=sys.stderr)
        if hasattr(e, "read"):
            print(f"API Details: {e.read().decode('utf-8')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    generate_commentary()
