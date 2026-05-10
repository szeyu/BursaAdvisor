# Adding a Sector

Create 2 files. Engine auto-discovers them — no other file to edit.

```
rules/sectors/<sector>.py
data/sector_configs/<sector>.json
```

---

## Step 1 — JSON config (`data/sector_configs/<sector>.json`)

Copy `banking.json` and update the values.

```json
{
  "sector": "Plantation",
  "primary_metric": "pe_ratio",
  "peer_avg_fallback": 18.0,
  "avoid_multiplier": 1.3,
  "benchmark_peers": [
    {"name": "SD Guthrie",          "ticker": "5285.KL"},
    {"name": "IOI Corp",            "ticker": "1961.KL"},
    {"name": "KLK",                 "ticker": "2445.KL"},
    {"name": "Genting Plantations", "ticker": "2291.KL"},
    {"name": "United Plantations",  "ticker": "2089.KL"}
  ],
  "extra_inputs": [],
  "macro_drivers": ["CPO price", "MYR/USD rate"],
  "red_flags": ["CPO price below RM 3,500/tonne"]
}
```

**Field reference:**

| Field | Meaning |
|---|---|
| `primary_metric` | yfinance field name used in your rules. See options below. |
| `peer_avg_fallback` | Value used when yfinance fetch fails. Set to a reasonable sector median. |
| `avoid_multiplier` | `avoid_threshold = peer_avg × multiplier`. Check BURSA_DECLARATIVE_KB.md Layer 3c for your sector's avoid threshold. |
| `benchmark_peers` | Top 5 stocks by market cap. Tickers from Bursa Malaysia website. |

**`primary_metric` options** (must match a field in `facts.py` `Stock`):

| Metric | Use for |
|---|---|
| `pe_ratio` | Plantation, Healthcare, Technology, Consumer, Property, Construction |
| `pb_ratio` | Banking, REITs (NAV proxy) |
| `dividend_yield` | Utilities |
| `ev_ebitda` | Gloves |
| `distribution_yield` | REITs (user-supplied, not yfinance) |

---

## Step 2 — Rules file (`rules/sectors/<sector>.py`)

Copy `rules/sectors/banking.py`. Make these 6 changes:

**1. Config name**
```python
_cfg = load_sector_config("plantation")   # match your JSON filename
```

**2. Sector enum**
```python
Stock(ticker=MATCH.ticker, sector=Sector.PLANTATION, ...)
PeerBenchmark(sector=Sector.PLANTATION, ...)
```

All 10 sectors are already defined in `enums.py` — just pick yours:
`BANKING` `PLANTATION` `REITS` `TECHNOLOGY` `HEALTHCARE` `GLOVES` `UTILITIES` `CONSUMER` `PROPERTY` `CONSTRUCTION`

**3. Metric field in `Stock()` match**
```python
# Banking used:
Stock(ticker=MATCH.ticker, sector=Sector.BANKING, pb_ratio=MATCH.pb)

# Plantation uses pe_ratio instead:
Stock(ticker=MATCH.ticker, sector=Sector.PLANTATION, pe_ratio=MATCH.pe)
```

**4. Metric field in `PeerBenchmark()` match**
```python
PeerBenchmark(sector=Sector.PLANTATION, metric="pe_ratio",
              value=MATCH.peer_avg, avoid_multiplier=MATCH.mult)
```

**5. `TEST` lambda variable names** — rename `pb` → `pe` (or whatever your metric is):
```python
TEST(lambda pe, peer_avg: pe is not None and pe < peer_avg)          # BUY
TEST(lambda pe, peer_avg, mult: pe is not None and peer_avg <= pe <= peer_avg * mult)  # WATCH
TEST(lambda pe, peer_avg, mult: pe is not None and pe > peer_avg * mult)               # AVOID
```

**6. Reason strings**
```python
reason=f"Plantation: P/E {pe:.1f}x below sector median {peer_avg:.1f}x"
reason=f"Plantation: P/E {pe:.1f}x within range ({peer_avg:.1f}x–{peer_avg * mult:.1f}x) — watch CPO price"
reason=f"Plantation: P/E {pe:.1f}x exceeds sector median +{round((mult-1)*100):.0f}% ({peer_avg * mult:.1f}x)"
```

Also update the `no_data` fallback rule — change `pb_ratio=None` to `pe_ratio=None` (or your metric).

---

## Understanding `PeerBenchmark`

The system fetches live metric values for your benchmark peers from yfinance, computes the average, and stores it as a `PeerBenchmark` fact in working memory before `engine.run()`. Your rules match on it like any other fact.

```
Session start → yfinance fetches P/E for 5 plantation peers → avg = 17.3
              → PeerBenchmark(sector=PLANTATION, metric="pe_ratio", value=17.3) declared

engine.run()  → your rule matches PeerBenchmark → peer_avg = 17.3
              → TEST: pe < 17.3? → BUY
```

If yfinance is unavailable, `peer_avg_fallback` from your JSON is used instead.

---

## Which sectors need extra user inputs?

These are already handled in `tui/prompts.py` — no code change needed.

| Sector | Extra prompt | Field in `Stock` |
|---|---|---|
| REITs | Distribution yield + occupancy rate | `distribution_yield`, `occupancy_rate` |
| Technology | Export revenue % | `export_revenue_pct` |
| Gloves | Export revenue % | `export_revenue_pct` |
| Construction | Order book (RM billions) | `order_book_rm` |
| All others | None — yfinance provides everything | — |

---

## Macro indicators available in rules

`MacroData` is declared automatically each session. Match it in rules when relevant:

```python
MacroData(opr=MATCH.opr, usd_myr=MATCH.rate)
```

| Field | Affects |
|---|---|
| `opr` | Banking (NIM), REITs (borrowing cost), Utilities, Property, Construction |
| `usd_myr` | Technology, Gloves, Plantation (USD-denominated revenue/commodity) |

---

## Additional yfinance fields available in `Stock`

Beyond P/E and P/B, the following are fetched automatically and ready to use in rules:

| Field | Relevant sectors |
|---|---|
| `revenue_growth` | Technology, Construction, Consumer, Healthcare |
| `gross_margin` | Plantation, Gloves, Technology, Healthcare *(None for Banking)* |
| `operating_margin` | All sectors |
| `ebitda_margin` | Plantation, Gloves, Utilities *(None for Banking)* |
| `roe` | Banking (benchmark ≥10%), REITs, Consumer |
| `roa` | Banking (benchmark ≥1%) |
| `free_cashflow_b` | Technology, Healthcare, Plantation *(None for Banking)* |
| `beta` | All sectors — volatility vs KLCI |
| `eps_growth_yoy` | Technology, Healthcare, Consumer |
| `ev_ebitda` | Gloves, Utilities |

Always guard with `TEST(lambda x: x is not None and ...)` before using.

---

## Checklist

```
[ ] data/sector_configs/<sector>.json
      - primary_metric matches a Stock field name
      - benchmark_peers has correct .KL tickers (verify on bursamalaysia.com)
      - peer_avg_fallback is a reasonable sector median

[ ] rules/sectors/<sector>.py
      - class name ends with "Rules" (required for auto-discovery)
      - load_sector_config("<sector>") matches JSON filename exactly
      - Sector.<YOURSECTOR> used in all Stock() and PeerBenchmark() matches
      - salience=20 on BUY/WATCH/AVOID rules
      - salience=19 on the no-data fallback rule

[ ] Test: make install && make start
      - enter a real ticker from your sector
      - check verdict + reason make sense
```
