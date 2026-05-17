# BursaAdvisor Expert System
## Section 2: Declarative Knowledge Base

**WID2002 – Knowledge Representation & Reasoning | Universiti Malaya | 2025**

---

## Overview

The declarative knowledge base of BursaAdvisor is organised into three layers: **investor profile facts**, **universal stock attribute facts**, and **domain threshold facts** (both universal hard stops and ten sector-specific valuation rules). These represent the static ground truth that the inference engine reasons over during a forward-chaining evaluation session.

---

## Layer 1 — Investor Profile Facts

These facts describe the individual investor's financial situation and risk posture. They are collected at runtime via the user interface and instantiated as working memory facts before inference begins.

> **Note:** Investors aged 45 and above are automatically mapped to income-oriented (dividend) stocks by the inference engine. Below 45, growth stock evaluation is permitted depending on `risk_tolerance` and `investment_horizon`.

| Attribute | Data Type | Example Value | Description |
|---|---|---|---|
| `investor_age` | Integer (years) | 28 | Age in years; determines growth vs income preference |
| `monthly_income` | Float (RM) | RM 5,500 | Gross monthly income in Ringgit Malaysia |
| `monthly_savings` | Float (RM) | RM 1,540 | Derived: `monthly_income × savings_ratio` |
| `savings_ratio` | Float (0–1) | 0.28 | Fraction of income allocated for investment |
| `risk_tolerance` | Enum | `moderate` | One of: `conservative` \| `moderate` \| `aggressive` |
| `investment_horizon` | Integer (years) | 5 | Time horizon before expected capital withdrawal |
| `income_preference` | Boolean | `false` | True if investor prioritises dividend income over capital gains |

---

## Layer 2 — Universal Stock Attribute Facts

These facts describe a specific Bursa-listed stock under evaluation. They are entered by the user or fetched from a data source. Sector-specific attributes (e.g. order book, occupancy rate) are only instantiated when the stock's sector matches.

| Attribute | Data Type | Example Value | Description |
|---|---|---|---|
| `stock_ticker` | String | `5347.KL` | Bursa Malaysia ticker symbol |
| `stock_name` | String | `Tenaga Nasional` | Company display name |
| `stock_sector` | Enum (10 sectors) | `Technology` | One of ten BursaAdvisor sectors |
| `stock_pe_ratio` | Float | 22.5 | Price-to-earnings ratio (TTM) |
| `stock_pb_ratio` | Float | 1.8 | Price-to-book ratio (primary for Banking) |
| `stock_ev_ebitda` | Float | 9.2 | EV/EBITDA (supplementary for Utilities, Gloves) |
| `stock_dividend_yield` | Float (%) | 4.8 | Trailing twelve-month dividend yield |
| `stock_distribution_yield` | Float (%) | 5.5 | Distribution yield (primary for REITs) |
| `stock_payout_ratio` | Float (%) | 62 | Dividends paid as % of net profit |
| `stock_debt_to_equity` | Float | 0.9 | Total debt / shareholders' equity |
| `stock_current_ratio` | Float | 1.4 | Current assets / current liabilities |
| `stock_market_cap_rm` | Float (RM B) | 2.4 | Market capitalisation in RM billions |
| `stock_consecutive_losses` | Integer | 0 | Number of consecutive quarters with net loss |
| `stock_eps_growth_yoy` | Float (%) | 12.3 | Year-on-year EPS growth rate |
| `stock_rsi` | Float (0–100) | 58 | 14-day Relative Strength Index |
| `stock_golden_cross` | Boolean | `true` | True if 50-day MA has crossed above 200-day MA |
| `stock_is_pn17` | Boolean | `false` | True if stock is under PN17 financial distress status |
| `stock_auditor_qualified` | Boolean | `false` | True if latest auditor report is qualified |
| `stock_order_book_rm` | Float (RM B) | 8.5 | Outstanding contract order book (Construction only) |
| `stock_export_revenue_pct` | Float (%) | 65 | % of revenue from exports (Technology, Gloves) |
| `stock_nla_psf` | Float (RM) | 450 | Net lettable area per sq ft rental rate (REITs) |
| `stock_occupancy_rate` | Float (%) | 94 | Portfolio occupancy rate (REITs) |

---

## Layer 3a — Universal Hard-Stop Threshold Constants

These sector-agnostic thresholds are hardcoded constants in the knowledge base. Any stock triggering one or more of these conditions receives an automatic **AVOID** recommendation, overriding all other rule outcomes.

| Fact / Constant Name | Value | Rule / Meaning |
|---|---|---|
| `HARD_MAX_DE_RATIO` | > 2.0x | Debt-to-equity above this threshold → auto-AVOID (all sectors) |
| `HARD_MIN_CURRENT_RATIO` | < 1.0 | Current ratio below this → flag liquidity risk |
| `HARD_MAX_CONSECUTIVE_LOSSES` | ≥ 2 quarters | Two or more consecutive quarterly net losses → auto-AVOID |
| `HARD_MIN_MARKET_CAP_RM` | < RM 500m | Below this market cap → not suitable for retail recommendation |
| `HARD_IS_PN17` | = true | Stock under PN17 financial distress listing → auto-AVOID |
| `HARD_AUDITOR_QUALIFIED` | = true | Auditor issued a qualified opinion on latest financials → auto-AVOID |
| `HARD_MIN_SAVINGS_RATIO` | < 0.20 | Investor saving less than 20% of income → flag insufficient capital buffer |

---

## Layer 3b — Investor Risk Profile Threshold Constants

The following constants define the valuation guardrails for each investor risk profile. They are applied after hard-stop checks and before sector-specific rules. RSI thresholds are universal across all profiles.

| Threshold / Parameter | Conservative | Moderate | Aggressive |
|---|:---:|:---:|:---:|
| `MIN_DIVIDEND_YIELD_PCT` | ≥ 4.5% | ≥ 3.0% | ≥ 1.0% |
| `MAX_PE_RATIO` (growth) | ≤ 18x | ≤ 28x | ≤ 40x |
| `MAX_PAYOUT_RATIO_PCT` | ≤ 70% | ≤ 80% | ≤ 90% |
| `MIN_RSI_ENTRY` (oversold) | < 30 | < 30 | < 30 |
| `MAX_RSI_ENTRY` (overbought) | ≥ 70 | ≥ 70 | ≥ 70 |
| `AGE_INCOME_SHIFT` | ≥ 45 yrs | ≥ 45 yrs | ≥ 45 yrs |

---

## Layer 3c — Sector-Specific Valuation Threshold Facts (10 Sectors)

BursaAdvisor covers ten sectors derived from the elicitation interview, with **Gloves and Healthcare separated** (different valuation drivers), and **Property and Construction separated** (different macro sensitivities). Benchmark peers are sourced from the Bursa Malaysia Sectorial Index Series Factsheet (September 2025) and verified by market capitalisation ranking.

---

### 1. Banking (Financial Services)

| Field | Value |
|---|---|
| **Primary Metric** | P/B Ratio |
| **BUY Threshold** | P/B below peer average (Big 4 benchmark) |
| **AVOID Threshold** | P/B > peer avg + 20%; deteriorating NIM |
| **Min Div Yield (Conservative)** | 5–6% |
| **#1 Macro Driver** | GDP growth & economic cycle |
| **#2 Macro Driver** | OPR (net interest margin impact) |
| **Sector Red Flag** | Rising NPL ratio; BNM regulatory action |
| **Benchmark Peers (Top 5 by Mkt Cap)** | Maybank, Public Bank, CIMB, Hong Leong Bank, RHB Bank |

---

### 2. Plantation

| Field | Value |
|---|---|
| **Primary Metric** | P/E Ratio |
| **BUY Threshold** | P/E below sector median peers |
| **AVOID Threshold** | P/E > sector median + 30%; declining CPO price trend |
| **Min Div Yield (Conservative)** | ≥ 5% |
| **#1 Macro Driver** | CPO (crude palm oil) price |
| **#2 Macro Driver** | MYR/USD exchange rate |
| **Sector Red Flag** | CPO price sustained below RM 3,500/tonne |
| **Benchmark Peers (Top 5 by Mkt Cap)** | SD Guthrie (SDG), IOI Corp, KLK, Genting Plantations, United Plantations |

---

### 3. REITs

| Field | Value |
|---|---|
| **Primary Metric** | Distribution Yield |
| **BUY Threshold** | Yield > 6%; occupancy > 90% |
| **AVOID Threshold** | Yield < 4%; rising OPR environment |
| **Min Div Yield (Conservative)** | 4–5% |
| **#1 Macro Driver** | OPR (borrowing & refinancing cost) |
| **#2 Macro Driver** | Occupancy rate / consumer footfall |
| **Sector Red Flag** | Rising OPR; tenant default rate spike |
| **Benchmark Peers (Top 5 by Mkt Cap)** | KLCC REIT, IGB REIT, Sunway REIT, Pavilion REIT, Axis REIT |

---

### 4. Technology

| Field | Value |
|---|---|
| **Primary Metric** | P/E Ratio |
| **BUY Threshold** | P/E below sector median; growing order book |
| **AVOID Threshold** | P/E > 40x; USD weakening vs MYR |
| **Min Div Yield (Conservative)** | < 3% (growth focus) |
| **#1 Macro Driver** | USD/MYR rate (export revenue exposure) |
| **#2 Macro Driver** | US semiconductor demand cycle |
| **Sector Red Flag** | USD/MYR sustained below 4.2; US tech inventory glut |
| **Benchmark Peers (Top 5 by Mkt Cap)** | Inari Amertron, ViTrox, Frontken, MPI, Greatech Technology |

---

### 5. Healthcare

| Field | Value |
|---|---|
| **Primary Metric** | P/E Ratio |
| **BUY Threshold** | P/E below sector median; expanding beds/revenue |
| **AVOID Threshold** | P/E > peer avg × 1.25 (+25%); low occupancy rate (< 65%) |
| **Min Div Yield (Conservative)** | < 3% (growth reinvestment) |
| **#1 Macro Driver** | Healthcare inflation & staff cost |
| **#2 Macro Driver** | Medical tourism demand (MYR strength matters) |
| **Sector Red Flag** | Regulatory pricing cap; MoH policy changes |
| **Benchmark Peers (Top 5 by Mkt Cap)** | IHH Healthcare, KPJ Healthcare, Apex Healthcare, Duopharma, Pharmaniaga |

---

### 6. Gloves

| Field | Value |
|---|---|
| **Primary Metric** | P/E / EV-EBITDA |
| **BUY Threshold** | P/E at multi-year low; ASP (avg selling price) recovering |
| **AVOID Threshold** | P/E > peer avg × 1.3 (+30%); stronger AVOID if USD/MYR < 4.40 |
| **Min Div Yield (Conservative)** | < 3% |
| **#1 Macro Driver** | USD/MYR rate (most revenue USD-denominated) |
| **#2 Macro Driver** | Global healthcare demand & ASP trend |
| **Sector Red Flag** | New low-cost competitor capacity surge (Thailand, China); ASP collapse |
| **Benchmark Peers (Top 5 by Mkt Cap)** | Top Glove, Hartalega, Kossan, Supermax, Careplus Group |

---

### 7. Utilities

| Field | Value |
|---|---|
| **Primary Metric** | Dividend Yield |
| **BUY Threshold** | Yield > 5%; stable regulated returns |
| **AVOID Threshold** | P/E > peer avg × 1.2 OR dividend yield < 3.0% (either alone triggers AVOID) |
| **Min Div Yield (Conservative)** | ≥ 5% |
| **#1 Macro Driver** | Coal & fuel price (40–50% of generation cost) |
| **#2 Macro Driver** | OPR (debt financing cost; sector is capital-intensive) |
| **Sector Red Flag** | Fuel price spike without corresponding tariff revision |
| **Benchmark Peers (Top 5 by Mkt Cap)** | TNB, Petronas Gas, YTL Power Int'l, YTL Corp, Gas Malaysia |

---

### 8. Consumer / Retail

| Field | Value |
|---|---|
| **Primary Metric** | P/E Ratio |
| **BUY Threshold** | P/E below sector median; rising consumer confidence |
| **AVOID Threshold** | P/E > 30x; sustained high inflation eroding margins |
| **Min Div Yield (Conservative)** | < 3% |
| **#1 Macro Driver** | Inflation (consumer purchasing power erosion) |
| **#2 Macro Driver** | Private consumption index & wage growth |
| **Sector Red Flag** | Sustained CPI > 4%; aggressive foreign retail entry |
| **Benchmark Peers (Top 5 by Mkt Cap)** | 99 Speedmart, Mr DIY Group, Nestle Malaysia, F&N, Padini Holdings |

---

### 9. Property

| Field | Value |
|---|---|
| **Primary Metric** | P/E Ratio |
| **BUY Threshold** | Low P/E + rising property sales volume; low unsold inventory |
| **AVOID Threshold** | High OPR + shrinking sales; high unsold units (overhang) |
| **Min Div Yield (Conservative)** | < 3% |
| **#1 Macro Driver** | OPR (mortgage & home financing cost) |
| **#2 Macro Driver** | Property overhang level & household debt-to-income ratio |
| **Sector Red Flag** | Rising OPR; high-rise overhang; stricter lending requirements |
| **Benchmark Peers (Top 5 by Mkt Cap)** | Sime Darby Prop., IOI Properties, Eco World, SP Setia, Mah Sing Group |

---

### 10. Construction

| Field | Value |
|---|---|
| **Primary Metric** | P/E + Order Book |
| **BUY Threshold** | Low P/E + growing order book; major infrastructure award pipeline |
| **AVOID Threshold** | High OPR + stagnant order book; cost overruns |
| **Min Div Yield (Conservative)** | < 3% |
| **#1 Macro Driver** | OPR (financing cost for projects & developers) |
| **#2 Macro Driver** | Inflation (labour & material cost: steel, cement) |
| **Sector Red Flag** | Project cancellations; government capex cuts; labour shortage |
| **Benchmark Peers (Top 5 by Mkt Cap)** | Gamuda, IJM Corp, Sunway Construction, WCT Holdings, Kerjaya Prospek |

---

## Layer 3d — Auto-AVOID Hard-Stop Trigger Summary

The following conditions trigger an immediate **AVOID** recommendation regardless of sector, valuation metrics, or investor profile. They are evaluated **first** in the inference engine before any other rules fire.

| Condition | Triggering Fact | Rationale |
|---|---|---|
| PN17 listing status | `stock_is_pn17 = true` | Company is under financial distress; delisting risk is imminent |
| Qualified audit opinion | `stock_auditor_qualified = true` | Auditor cannot confirm financials are accurate; credibility risk |
| Two or more consecutive losses | `stock_consecutive_losses ≥ 2` | Sustained earnings deterioration signals structural problems |
| Excessive debt level | `stock_debt_to_equity > 2.0` | High leverage raises insolvency risk, especially in rising OPR environment. **Exempt: Banking, Healthcare, Utilities, REITs** (structurally high leverage by design; governed by sector-specific regulatory limits instead) |
| Liquidity stress | `stock_current_ratio < 1.0` | Short-term liabilities exceed short-term assets; cash crunch risk. **Exempt: Banking, Healthcare, Utilities, REITs** (current ratio < 1.0 is structurally normal for asset-heavy and financial sectors) |
| Below retail market cap floor | `stock_market_cap_rm < 0.5` (RM 500m) | Small-cap illiquidity and information asymmetry disadvantage retail investors |

---

## Data Sources & Notes

- Sector thresholds are elicited from the analyst interview (Knowledge Elicitation Sheet, 2025) and cross-referenced with analyst consensus from research houses (Maybank IB, RHB Research, CIMB Securities).
- Benchmark peer lists are drawn from the official **Bursa Malaysia Sectorial Index Series Factsheet (September 2025)**, ranked by market capitalisation within each sector's Main Market index constituents.
- The **Gloves** sector is treated independently from Healthcare due to significantly different valuation cycles, macro drivers (ASP volatility vs. occupancy/bed capacity), and investor sentiment patterns.
- The **Construction** sector is separated from Property because their primary valuation anchor (order book vs. property sales volume) and macro sensitivity (labour/material inflation vs. mortgage OPR) diverge materially.
- All monetary thresholds are denominated in **Ringgit Malaysia (RM)**. OPR = Overnight Policy Rate, set by Bank Negara Malaysia. CPO = Crude Palm Oil. ASP = Average Selling Price. NIM = Net Interest Margin. NPL = Non-Performing Loan.