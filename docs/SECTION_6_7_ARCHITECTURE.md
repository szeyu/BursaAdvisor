# 6. ES Architecture: KB, IE, and UI

BursaAdvisor has three core components: the **Knowledge Base** (stores rules), the **Inference Engine** (applies rules to a stock), and the **User Interface** (collects input and displays results). An **Explanation Facility** records which rules fired so users can understand every recommendation.

---

## 6.1 Knowledge Base (KB)

Rules follow the form: **IF** condition is true, **THEN** take action. Rules are grouped into three tiers.

### Tier 1: Hard-Stop / Auto-AVOID Rules (Universal)

| Rule ID | Condition | Action |
|---------|-----------|--------|
| R01 | stock.status = PN17 | AVOID (regulatory distress) |
| R02 | auditor_qualification = TRUE | AVOID (financial reporting risk) |
| R03 | consecutive_quarterly_losses >= 2 | AVOID (sustained losses) |
| R04 | debt_to_equity > 2.0x | AVOID (over-leverage) |
| R05 | current_ratio < 1.0x | AVOID (liquidity crisis) |
| R06 | market_cap < RM 500M | AVOID (illiquid micro-cap) |

**Table 4: Tier 1 hard-stop rules**

> **Sector exemptions — R04 and R05:** Not applied to Banking, Healthcare, Utilities, or REITs. These sectors carry structurally high leverage or low current ratios by design. Sector-appropriate metrics are used instead (e.g. loan-to-deposit ratio for Banking; SC/Bursa 50% gearing limit for REITs).

---

### Tier 2: Investor Profile and Suitability Rules (Universal)

| Rule ID | Profile | Condition | Action |
|---------|---------|-----------|--------|
| R10 | Conservative | P/E ≤ 18 AND div_yield ≥ 4.5% AND payout ≤ 70% | FundamentalPass → sector rules may fire BUY |
| R10M | Moderate | P/E ≤ 28 AND div_yield ≥ 3.0% AND payout ≤ 80% | FundamentalPass → sector rules may fire BUY |
| R13 | Aggressive | P/E ≤ 40 AND div_yield ≥ 1.0% AND payout ≤ 90% | FundamentalPass → sector rules may fire BUY |
| R10F | All | Fundamental gate NOT met | WATCH (diagnostic: which threshold failed is shown in explanation) |
| R18A | All | age ≥ 45 OR income-focused preference selected | Activate income-shift mode (P/E bypassed; dividend yield evaluated only) |
| R18B | Income-shift active | div_yield ≥ 4.5% AND payout within profile limit | FundamentalPass (P/E is NOT checked) |
| R14 | All | RSI ≥ 70 AND verdict = BUY | Downgrade → WATCH (overbought; entry timing risk) |
| R15 | All | RSI ≤ 30 AND golden cross = TRUE AND **FundamentalPass = TRUE** AND verdict = WATCH | Upgrade → BUY (oversold + momentum). Only fires if stock cleared fundamental gate — a WATCH from a failed fundamental check cannot be upgraded by technicals. |
| R16L | All | savings_ratio < 20% AND verdict = BUY AND sector is volatile* | Downgrade → WATCH (insufficient capital buffer) |
| R17S | All | investment_horizon < 3 years AND verdict = BUY AND sector is volatile* | Downgrade → WATCH (short horizon; capital may be needed before recovery) |
| Note | REITs | Stock sector = REITs (R04/R05 exempted) | Bypasses fundamental gate entirely — no P/E, dividend yield, or payout check. Evaluated solely on distribution yield vs sector peer average. |

*Volatile sectors: Plantation, Technology, Gloves, Property, Construction

**Table 5: Tier 2 investor profile and suitability rules**

---

### Tier 3: Sector-Specific Valuation Rules

Dividend yield thresholds are handled at profile level (Table 5) and not repeated here.

| Sector | Primary Metric | BUY Signal | WATCH Signal | AVOID Signal | Key Macro Driver |
|--------|---------------|------------|--------------|--------------|-----------------|
| Banking | P/B ratio | P/B < peer avg | peer avg ≤ P/B ≤ peer avg × 1.2 | P/B > peer avg × 1.2 | OPR, GDP growth |
| Plantation | P/E ratio | P/E < peer avg | peer avg ≤ P/E ≤ peer avg × 1.3 | P/E > peer avg × 1.3 | CPO price, USD/MYR |
| REITs | Distribution yield | Yield ≥ peer avg | peer avg ÷ 1.2 ≤ yield < peer avg | Yield < peer avg ÷ 1.2 | OPR, borrowing cost |
| Technology | P/E ratio | P/E < peer avg | peer avg ≤ P/E ≤ peer avg × 1.4 | P/E > peer avg × 1.4 | USD/MYR, OPR |
| Gloves | P/E ratio | P/E < peer avg · Stronger BUY if USD/MYR ≥ 4.40 | peer avg ≤ P/E ≤ peer avg × 1.3 | P/E > peer avg × 1.3 · Stronger AVOID if USD/MYR < 4.40 | USD/MYR, ASP cycle, nitrile cost |
| Healthcare | P/E ratio | P/E < peer avg AND occupancy ≥ 65% | · P/E within peer range (to × 1.25), any occupancy · P/E > peer avg × 1.25 AND occupancy ≥ 65% (overvalued but operationally sound) | P/E > peer avg × 1.25 AND occupancy < 65% | USD/MYR (medical tourism), OPR |
| Utilities | P/E + div yield | P/E < peer avg AND div yield ≥ 4.0% | peer avg ≤ P/E ≤ peer avg × 1.2 AND div yield 3.0%–4.0% | P/E > peer avg × 1.2 **OR** div yield < 3.0% (either alone triggers AVOID) | OPR, coal/fuel price, tariff revision |
| Consumer | P/E ratio | P/E < peer avg | peer avg ≤ P/E ≤ peer avg × 1.35 | P/E > peer avg × 1.35 | Consumer sentiment, inflation |
| Property | P/E ratio | P/E < peer avg | peer avg ≤ P/E ≤ peer avg × 1.2 | P/E > peer avg × 1.2 | OPR, material & labour cost |
| Construction | P/E + order book | P/E < peer avg AND order book provided | peer avg ≤ P/E ≤ peer avg × 1.2 AND order book provided; OR data unavailable | P/E > peer avg × 1.2 (order book not required for AVOID) | OPR, material & labour cost |

**Table 6: Sector-specific rule summary (ten sectors)**

---

## 6.2 Inference Engine (IE)

Uses **forward chaining** — starts from available data and works toward a conclusion. No scores are added; the final verdict is whichever rule last updates it.

| Step | Action | Notes |
|------|--------|-------|
| 1 | Run Tier 1 hard-stop checks | First rule that fires → AVOID, stop. Banking/Healthcare/Utilities/REITs exempt from R04/R05. |
| 2 | Identify sector | Looked up from Yahoo Finance via ticker. Determines which sector rules apply. |
| 3 | Fundamental gate check | Check P/E, dividend yield, payout ratio against investor profile thresholds. Pass → FundamentalPass declared. Fail → WATCH (diagnostic). REITs skip this step entirely. |
| 4 | Investor suitability checks | Low savings (<20%) or short horizon (<3 yr) in volatile sector → downgrade BUY to WATCH. |
| 5 | Market timing signals | RSI ≥ 70 + BUY → WATCH (overbought). RSI ≤ 30 + golden cross + **FundamentalPass** + WATCH → BUY (oversold). Technical signals cannot override a failed fundamental gate. |
| 6 | Economic context | OPR fetched from BNM Open API. USD/MYR fetched from Yahoo Finance. Sector rules use these to adjust the verdict (e.g. rising OPR → pressure on REITs, Property, Utilities). |
| 7 | Final verdict | Last verdict set by any rule = final answer: BUY / WATCH / AVOID. |
| 8 | Explanation | All fired rules collected and shown as a readable trace in the UI. |

**Table 9: Inference Engine execution steps**

---

## 6.3 User Interface (UI)

| Screen | Type | Key Details |
|--------|------|-------------|
| Investor Profile | Input | · Risk appetite: Conservative / Moderate / Aggressive · Investment horizon: Short (<3 yr) / Medium (3–5 yr) / Long (6–10 yr) / Extended (>10 yr) · Dividend preference toggle · Age ≥ 45 or income-focused → auto income-shift mode |
| Stock Lookup | Input | · User enters Bursa ticker · Auto-fetched: P/E, P/B, dividend yield, payout ratio, D/E, current ratio, market cap, RSI, golden cross, consecutive losses · Manually ticked: PN17 status, qualified audit · Sector-specific extras: Gloves → export revenue %; Construction → order book (RM); Healthcare → occupancy rate (%) |
| Recommendation | Output | · Colour-coded verdict (green = BUY, amber = WATCH, red = AVOID) · Confidence score · Step-by-step rule trace (fired / skipped) · Three signal cards: financial health, market timing, risk level · Personal watchlist save |

**Table 7: UI screen descriptions**

---

# 7. Implementation: Tools and Software

| Tool / Library | Role | Justification |
|---------------|------|---------------|
| Python 3.14 | Core language (KB rules + IE logic) | Clean IF-THEN syntax; large financial library ecosystem |
| Streamlit 1.x | Web UI | No front-end code needed; native form widgets, colour output, markdown rendering |
| pandas | Technical signal computation | 14-period RSI and 50/200-day MA golden cross from yfinance price history |
| experta (PyKnow fork) | Forward-chaining RETE rule engine | CLIPS-compatible; rules as typed Python class methods; KB stays modular |
| yfinance | Live stock data | Fetches P/E, P/B, dividend yield, payout ratio, D/E, current ratio, market cap, RSI, golden cross, consecutive losses, USD/MYR (USDMYR=X) |
| BNM Open API | Live OPR data | OPR not on Yahoo Finance; sourced directly from `api.bnm.gov.my` |
| Git / GitHub | Version control | Five-member team; branch-based workflow |

**Table 8: Implementation toolchain**

Python was chosen over Prolog because the team is already proficient in it and Streamlit removes the need for separate front-end development. The experta library provides the rule engine, so the inference logic did not need to be built from scratch.

## 7.1 System Data Flow

1. User enters ticker + investor profile
2. System fetches stock data (yfinance) and macro data (BNM API + yfinance)
3. Inference engine runs rules in salience order (hard stops → profile → sector → suitability → technicals)
4. Each fired rule is logged to the explanation trace
5. Final verdict and trace displayed to user
