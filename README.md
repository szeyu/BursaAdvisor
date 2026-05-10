# BursaAdvisor
Expert system for Bursa Malaysia stock investment advisory.
Built with `experta` (forward chaining, RETE) for WID2001 Knowledge Representation & Reasoning, Universiti Malaya.

## Setup

```bash
git clone <repo-url>
cd BursaAdvisor
make install       # install dependencies (run once, and after every git pull)
```

Requires Python 3.14. Uses `uv` for dependency management.

## Usage

```bash
make start         # interactive screener
make verbose       # screener + inference trace (shows why each verdict was reached)
```

## Adding a sector

Read [SECTOR_GUIDE.md](SECTOR_GUIDE.md) — full walkthrough with complete Plantation example.

Short version: create 2 files, nothing else to touch.
```
rules/sectors/<your_sector>.py          ← copy banking.py, change 6 things
data/sector_configs/<your_sector>.json  ← copy banking.json, update numbers
```

## Project structure

```
src/bursaadvisor/
├── engine.py           ← inference engine (auto-discovers sector rules)
├── facts.py            ← all Fact types (InvestorProfile, Stock, Recommendation ...)
├── enums.py            ← Sector, Verdict, RiskTolerance + VOLATILE_SECTORS
├── constants.py        ← universal thresholds (hard stops, risk profiles, RSI)
├── rules/
│   ├── hard_stops.py   ← salience 100: auto-AVOID conditions
│   ├── profile.py      ← salience  70: investor profile flags
│   ├── fundamentals.py ← salience  50: P/E + dividend + payout gate
│   ├── sectors/        ← salience  20: one file per sector — ADD YOURS HERE
│   │   └── banking.py
│   ├── suitability.py  ← salience  15: investor-stock fit adjustments
│   └── technicals.py   ← salience  10: RSI signals + salience 0 fallback
├── data/
│   ├── stock_fetcher.py         ← yfinance: P/E, P/B, margins, RSI, golden cross ...
│   ├── macro_fetcher.py         ← BNM OPR + USD/MYR exchange rate
│   ├── peer_benchmark.py        ← computes live sector peer averages
│   ├── config_loader.py         ← loads data/sector_configs/*.json
│   └── sector_configs/
│       └── banking.json         ← thresholds + benchmark peer tickers
└── tui/
    ├── prompts.py      ← questionary input flows
    └── display.py      ← rich output (table, warnings, verbose trace)
```

## Inference salience layers

| Salience | Layer | What it does |
|---|---|---|
| 100 | Hard stops | Auto-AVOID: PN17, bad audit, high debt, losses, illiquidity |
| 70 | Profile flags | Detect income-shift (age ≥45), low savings, short horizon |
| 50 | Fundamental gate | P/E ≤ limit, dividend ≥ min, payout ≤ cap for risk profile |
| 20 | Sector rules | BUY/WATCH/AVOID vs live computed peer average |
| 15 | Suitability | Downgrade BUY→WATCH for volatile sectors if horizon <3yr or low savings |
| 10 | Technical signals | RSI overbought → downgrade, oversold + golden cross → upgrade |
| 0 | Fallback | WATCH with diagnostic reason if no sector rule matched |

## Data sources

| Data | Source |
|---|---|
| Stock metrics (P/E, P/B, margins, ROE ...) | yfinance |
| Sector peer averages | yfinance (computed live each session) |
| OPR | Bank Negara Malaysia Open API |
| USD/MYR exchange rate | yfinance |
| Distribution yield, occupancy rate, export %, order book | User input at runtime |
