# Daily Market Summary PWA

A daily financial market briefing web application replicating the layout, data points, and editorial coverage of [market-summary-12550.web.app](https://market-summary-12550.web.app/).

The application is built as an installable **Progressive Web App (PWA)** for Google Chrome and mobile browsers, automated to update every weekday **30 minutes after the US market close** (16:30 US Eastern Time).

- **Live Web App**: [https://bluesky999888.github.io/Daily_Market_Update/](https://bluesky999888.github.io/Daily_Market_Update/)
- **GitHub Repository**: [https://github.com/bluesky999888/Daily_Market_Update](https://github.com/bluesky999888/Daily_Market_Update)

---

## Features

- **8 Core Market Tiles**: S&P 500, Nasdaq Composite, Dow Jones, FTSE 100, DAX, Nikkei 225, Hang Seng, ASX 200.
- **Key Macro Badges**: US 10Y Yield, 30Y Yield, CAC 40, DXY (Dollar Index), USD/JPY, EUR/USD, AUD/USD, WTI Crude, Brent Crude, Gold, and Bitcoin.
- **6 Structured Commentary Panels**:
  - **US Equities**: Sector rotation, Big Tech vs cyclicals, yield curve pressure.
  - **Europe**: DAX, CAC 40, FTSE 100 movements and regional macro factors.
  - **Asia-Pacific**: Nikkei, Hang Seng, ASX sessions, currencies and central banks.
  - **FX**: US Dollar dynamics, Yen moves/intervention watch, Euro/Aussie trends.
  - **Commodities**: Crude oil supply & geopolitics, safe-haven Gold, Bitcoin.
  - **Central Banks & Economic Data**: Fed rate expectations, jobs/CPI prints, BoJ/ECB policies.
- **AI-Powered Synthesis**: Powered by Google Gemini (`gemini-3.6-flash`), adhering strictly to institutional standards: narrative drivers in prose with key entities bolded, numbers strictly isolated to badges.
- **PWA Ready**: Web App Manifest, Service Worker offline caching, and Chrome standalone desktop/mobile app installation.
- **Zero Heavy Dependencies**: Written entirely in Python standard library (`urllib`, `json`, `xml`, `zoneinfo`, `http.server`).

---

## Quick Start

### 1. Requirements & API Key
The application requires Python 3.9+ and uses your existing `GOOGLE_AI_API_KEY` (or `GEMINI_API_KEY`):
```bash
# Verify your API key is set
echo $env:GOOGLE_AI_API_KEY   # PowerShell
```

### 2. Run the Local Server & Open in Chrome
Start the local server:
```bash
python server.py 8080
```
Open [http://localhost:8080](http://localhost:8080) in Google Chrome.

### 3. Install as a PWA in Chrome
1. In Google Chrome, visit [http://localhost:8080](http://localhost:8080).
2. Click the **Install** icon in Chrome's address bar (or click the **⊞ Install App** button in the top-right header).
3. The app will install as a standalone desktop or mobile window without browser tabs or address bars.

---

## Running Updates

### Run On-Demand
To fetch fresh market data and generate AI commentary right now:
```bash
python update.py
```
Or via HTTP trigger when the server is running:
```bash
curl http://localhost:8080/api/update
```

Options:
- `python update.py --market-only`: Only update `public/market.json`
- `python update.py --commentary-only`: Only generate `public/commentary.json`

---

## Automated Weekday Scheduling (30m After US Close)

The US stock market regular session closes at 4:00 PM Eastern Time (America/New_York). 30 minutes after close is **16:30 US Eastern Time** on Monday through Friday.

Choose from any of the following 3 automation methods:

### Option A: Background Python Scheduler Daemon
Run `scheduler.py` in the background. It monitors `America/New_York` time, calculates the exact next weekday 16:30 ET run, and executes automatically:
```bash
python scheduler.py
# Or run immediately and then continue on schedule:
python scheduler.py --run-now
```

### Option B: Windows Task Scheduler
Use the included PowerShell helper to register a background scheduled task on Windows:
```powershell
.\setup_windows_task.ps1
```

### Option C: GitHub Actions & Cloud Hosting
This repository includes `.github/workflows/daily_update.yml`.
If you push this project to GitHub:
1. Go to repository **Settings > Secrets and variables > Actions**.
2. Add your `GOOGLE_AI_API_KEY` as a repository secret.
3. Enable GitHub Pages under **Settings > Pages** (Source: GitHub Actions).
4. GitHub Actions will automatically run the update every weekday at 16:30 Eastern Time (20:30 UTC during Daylight Saving / 21:30 UTC during Standard Time) and deploy your live PWA website.

---

## File Structure

```text
Daily_Market_Update/
├── public/
│   ├── index.html            # Main dashboard UI with container queries & themes
│   ├── manifest.json         # Web App Manifest for PWA installation
│   ├── sw.js                 # Service Worker (offline caching & network-first data)
│   ├── market.json           # Real-time market levels, % changes, session dates
│   ├── commentary.json       # AI-authored macro commentary & sources
│   └── icons/
│       ├── icon-192.png      # PWA icon 192x192
│       ├── icon-512.png      # PWA icon 512x512
│       └── apple-touch-icon.png
├── fetch_market_data.py      # Scrapes Yahoo Finance for 19 tickers
├── generate_commentary.py    # RSS news + Gemini 3.6 Flash commentary author
├── update.py                 # Pipeline orchestrator
├── server.py                 # Local PWA server with /api/update trigger
├── scheduler.py              # Weekday 16:30 US Eastern scheduler daemon
├── setup_windows_task.ps1    # Windows Task Scheduler registration script
├── .github/workflows/
│   └── daily_update.yml      # Automated GitHub Actions workflow & Pages deploy
├── requirements.txt          # Dependencies list (zero external packages needed)
└── README.md
```
