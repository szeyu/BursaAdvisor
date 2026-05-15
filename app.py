import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
import yfinance as yf

from bursaadvisor.engine import BursaAdvisor
from bursaadvisor.facts import (
    InvestorProfile, Stock, Recommendation, FundamentalPass,
    IncomeShiftFlag, LowSavingsFlag, ShortHorizonFlag, PeerBenchmark, MacroData,
)
from bursaadvisor.enums import Sector, Verdict, RiskTolerance, VOLATILE_SECTORS
from bursaadvisor.constants import (
    RISK_THRESHOLDS, INCOME_SHIFT_MIN_DIV,
    HARD_MAX_DE_RATIO, HARD_MIN_CURRENT_RATIO, HARD_MAX_CONSEC_LOSSES, HARD_MIN_MARKET_CAP_B,
)
from bursaadvisor.data.stock_fetcher import fetch_stock_data
from bursaadvisor.data.macro_fetcher import fetch_macro
from bursaadvisor.data.peer_benchmark import compute_peer_avg
from bursaadvisor.data.config_loader import try_load_sector_config

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BursaAdvisor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'JetBrains Mono', 'Fira Code', monospace; }

.card {
    background: #12122a;
    border: 1px solid #1e1e3f;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.card-header {
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #6b7db3;
    margin-bottom: 8px;
}
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
}
.badge-green  { background: #052e16; color: #4ade80; border: 1px solid #166534; }
.badge-yellow { background: #1c1500; color: #fbbf24; border: 1px solid #854d0e; }
.badge-red    { background: #1a0a0a; color: #f87171; border: 1px solid #7f1d1d; }
.badge-gray   { background: #1a1a2e; color: #94a3b8; border: 1px solid #334155; }

.metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 0;
    border-bottom: 1px solid #1e1e3f;
    font-size: 13px;
}
.metric-row:last-child { border-bottom: none; }
.metric-label { color: #94a3b8; }
.metric-value { color: #e2e8f0; font-weight: 600; }

.rec-card { border-radius: 8px; padding: 20px; margin-bottom: 12px; }
.rec-suitable { background: #0a1f12; border: 1px solid #166534; box-shadow: 0 0 20px #052e1640; }
.rec-monitor  { background: #1c1500; border: 1px solid #854d0e; box-shadow: 0 0 20px #1c150040; }
.rec-avoid    { background: #1a0a0a; border: 1px solid #7f1d1d; box-shadow: 0 0 20px #1a0a0a40; }
.rec-label { font-size: 9px; letter-spacing: 2px; color: #6b7db3; text-transform: uppercase; }
.rec-verdict-suitable { font-size: 32px; font-weight: 700; color: #4ade80; }
.rec-verdict-monitor  { font-size: 32px; font-weight: 700; color: #fbbf24; }
.rec-verdict-avoid    { font-size: 32px; font-weight: 700; color: #f87171; }
.rec-confidence { font-size: 13px; color: #94a3b8; }
.rec-reason { font-size: 12px; color: #cbd5e1; margin-top: 10px; line-height: 1.6; }

.conf-bar-bg { background: #1e1e3f; border-radius: 4px; height: 6px; margin: 8px 0; }
.conf-bar-fill-green  { background: #4ade80; height: 6px; border-radius: 4px; }
.conf-bar-fill-yellow { background: #fbbf24; height: 6px; border-radius: 4px; }
.conf-bar-fill-red    { background: #f87171; height: 6px; border-radius: 4px; }

.trace-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 7px 0;
    border-bottom: 1px solid #1a1a2e;
    font-size: 12px;
}
.trace-row:last-child { border-bottom: none; }
.trace-id    { color: #6b7db3; min-width: 80px; font-weight: 600; font-size: 11px; }
.trace-cond  { color: #cbd5e1; flex: 1; }
.trace-fired   { color: #4ade80; font-weight: 600; font-size: 11px; min-width: 60px; text-align: right; }
.trace-skipped { color: #64748b; font-weight: 600; font-size: 11px; min-width: 60px; text-align: right; }
.trace-notmet  { color: #fb923c; font-weight: 600; font-size: 11px; min-width: 60px; text-align: right; }

.wl-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid #1a1a2e;
    font-size: 13px;
}
.wl-row:last-child { border-bottom: none; }
.wl-name   { flex: 1; color: #e2e8f0; font-weight: 600; }
.wl-meta   { color: #6b7db3; font-size: 11px; }
.wl-badge-suitable { color: #4ade80; font-size: 11px; font-weight: 600; }
.wl-badge-monitor  { color: #fbbf24; font-size: 11px; font-weight: 600; }
.wl-badge-avoid    { color: #f87171; font-size: 11px; font-weight: 600; }

.section-label {
    font-size: 9px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #4b5563;
    padding: 4px 0 8px 0;
    border-bottom: 1px solid #1e1e3f;
    margin-bottom: 12px;
}
.macro-chip {
    display: inline-block;
    background: #12122a;
    border: 1px solid #1e1e3f;
    border-radius: 6px;
    padding: 6px 14px;
    margin: 4px 6px 4px 0;
    font-size: 12px;
    color: #94a3b8;
}
.macro-chip b { color: #e2e8f0; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)


# ── Constants ─────────────────────────────────────────────────────────────────

MARKET_OPTIONS = ["Main Market", "ACE Market", "LEAP Market"]

RISK_LABELS = {
    "Conservative": RiskTolerance.CONSERVATIVE,
    "Moderate": RiskTolerance.MODERATE,
    "Aggressive": RiskTolerance.AGGRESSIVE,
}

HORIZON_LABELS = {
    "Short-term (<3y)": 2,
    "Medium (3–5y)": 4,
    "Long-term (6–10y)": 7,
    "Extended (>10y)": 12,
}

AGE_LABELS = {
    "18 – 25": 22,
    "26 – 35": 30,
    "36 – 45": 40,
    "46 – 55": 50,
    "56 and above": 60,
}

SAVINGS_LABELS = {
    "10%": 0.10,
    "15%": 0.15,
    "20% (benchmark)": 0.20,
    "25%": 0.25,
    "30%": 0.30,
    "40%+": 0.40,
}

SECTORS_NEEDING_EXPORT = {Sector.GLOVES, Sector.TECHNOLOGY}
SECTORS_NEEDING_OCCUPANCY = {Sector.HEALTHCARE, Sector.REITS}
SECTORS_NEEDING_ORDER_BOOK = {Sector.CONSTRUCTION}
SECTORS_NEEDING_DIST_YIELD = {Sector.REITS}


# ── Signal badges (based strictly on what the engine rules check) ─────────────

def compute_signal_badges(stock_data: dict, profile_data: dict) -> dict:
    risk = profile_data["risk_tolerance"]
    thresholds = RISK_THRESHOLDS[risk]

    pe = stock_data.get("pe_ratio")
    div = stock_data.get("dividend_yield")
    payout = stock_data.get("payout_ratio")
    rsi = stock_data.get("rsi")
    golden_cross = stock_data.get("golden_cross", False)
    de = stock_data.get("debt_to_equity")
    cr = stock_data.get("current_ratio")
    is_pn17 = stock_data.get("is_pn17", False)

    # Fundamental: mirrors the fundamentals.py gate conditions
    pe_ok = pe is not None and 0 < pe <= thresholds["max_pe"]
    div_ok = div is not None and div >= thresholds["min_div"]
    payout_ok = payout is None or payout <= thresholds["max_payout"]
    if pe_ok and div_ok and payout_ok:
        fundamental = "Undervalued"
    elif (pe is not None and pe > thresholds["max_pe"] * 1.3) or (div is not None and div < thresholds["min_div"] * 0.5):
        fundamental = "Overvalued"
    else:
        fundamental = "Fair Value"

    # Technical: mirrors technicals.py exactly
    # upgrade_oversold_cross: WATCH + RSI ≤ 30 + golden_cross → BUY
    # downgrade_overbought:   BUY  + RSI ≥ 70 → WATCH
    if rsi is not None and rsi <= 30 and golden_cross:
        technical = "Bullish"
    elif rsi is not None and rsi >= 70:
        technical = "Bearish"
    else:
        technical = "Neutral"

    # Risk: mirrors hard_stops.py thresholds
    hard_stop = (
        is_pn17
        or (de is not None and de > HARD_MAX_DE_RATIO)
        or (cr is not None and cr < HARD_MIN_CURRENT_RATIO)
    )
    if hard_stop:
        risk_badge = "High risk"
    elif (de is not None and de > 1.2) or (cr is not None and cr < 1.2):
        risk_badge = "Moderate risk"
    else:
        risk_badge = "Low risk"

    return {"fundamental": fundamental, "technical": technical, "risk": risk_badge}


# ── Rule trace (mirrors the actual rule conditions in each .py file) ───────────

def build_rule_trace(stock_data: dict, profile_data: dict, engine_facts: dict) -> list[dict]:
    risk = profile_data["risk_tolerance"]
    t = RISK_THRESHOLDS[risk]
    ticker = stock_data.get("ticker", "")

    pe = stock_data.get("pe_ratio")
    div = stock_data.get("dividend_yield")
    payout = stock_data.get("payout_ratio")
    rsi = stock_data.get("rsi")
    golden_cross = stock_data.get("golden_cross", False)
    de = stock_data.get("debt_to_equity")
    cr = stock_data.get("current_ratio")
    mc = stock_data.get("market_cap_b")
    losses = stock_data.get("consecutive_losses", 0) or 0
    is_pn17 = stock_data.get("is_pn17", False)
    aq = stock_data.get("auditor_qualified", False)

    has_fundamental_pass = any(
        isinstance(f, FundamentalPass) and f.get("ticker") == ticker
        for f in engine_facts.values()
    )
    has_recommendation = any(
        isinstance(f, Recommendation) and f.get("ticker") == ticker
        for f in engine_facts.values()
    )

    def row(rule_id, condition, status):
        return {"id": rule_id, "condition": condition, "status": status}

    trace = []

    # ── Hard stops (salience 100) ──
    trace.append(row(
        "RULE-H01",
        "IF stock_status = PN17 → AVOID immediately",
        "Fired" if is_pn17 else "Skipped",
    ))
    trace.append(row(
        "RULE-H02",
        "IF auditor opinion = qualified/adverse → AVOID",
        "Fired" if aq else "Skipped",
    ))
    if losses >= HARD_MAX_CONSEC_LOSSES:
        h3 = "Fired"
    elif losses == 0:
        h3 = "Skipped"
    else:
        h3 = "Not met"
    trace.append(row("RULE-H03", f"IF consecutive losses ≥ {HARD_MAX_CONSEC_LOSSES} qtrs → AVOID", h3))

    if de is None:
        h4 = "Skipped"
    elif de > HARD_MAX_DE_RATIO:
        h4 = "Fired"
    else:
        h4 = "Not met"
    trace.append(row("RULE-H04", f"IF D/E > {HARD_MAX_DE_RATIO}x → AVOID (insolvency risk)", h4))

    if cr is None:
        h5 = "Skipped"
    elif cr < HARD_MIN_CURRENT_RATIO:
        h5 = "Fired"
    else:
        h5 = "Not met"
    trace.append(row("RULE-H05", f"IF current ratio < {HARD_MIN_CURRENT_RATIO} → AVOID (liquidity crisis)", h5))

    if mc is None:
        h6 = "Skipped"
    elif mc < HARD_MIN_MARKET_CAP_B:
        h6 = "Fired"
    else:
        h6 = "Not met"
    trace.append(row("RULE-H06", f"IF market cap < RM{HARD_MIN_MARKET_CAP_B * 1000:.0f}M → AVOID (illiquidity)", h6))

    # ── Fundamental gate (salience 50) ──
    pe_ok = pe is not None and 0 < pe <= t["max_pe"]
    div_ok = div is not None and div >= t["min_div"]
    payout_ok = payout is None or payout <= t["max_payout"]
    trace.append(row(
        "RULE-F01",
        f"IF P/E ≤ {t['max_pe']}x AND P/E > 0 → valuation = UNDERVALUED",
        "Fired" if pe_ok else ("Not met" if pe is not None else "Skipped"),
    ))
    trace.append(row(
        "RULE-D01",
        f"IF div_yield ≥ {t['min_div']}% AND payout ≤ {t['max_payout']}% → dividend = SUSTAINABLE",
        "Fired" if (div_ok and payout_ok) else ("Not met" if div is not None else "Skipped"),
    ))

    # ── Technical signals (salience 10) ──
    # upgrade_oversold_cross: existing WATCH + RSI ≤ 30 + golden_cross → BUY
    trace.append(row(
        "RULE-T01",
        f"IF RSI ≤ {int(30)} AND golden_cross = True → upgrade verdict to BUY",
        "Fired" if (rsi is not None and rsi <= 30 and golden_cross) else "Not met",
    ))
    # downgrade_overbought: existing BUY + RSI ≥ 70 → WATCH
    trace.append(row(
        "RULE-T02",
        f"IF RSI ≥ {int(70)} AND verdict = BUY → downgrade to WATCH",
        "Fired" if (rsi is not None and rsi >= 70) else "Not met",
    ))

    # ── Liquidity adequate (derived from hard stop inverse) ──
    if cr is None:
        l1 = "Skipped"
    elif cr > HARD_MIN_CURRENT_RATIO:
        l1 = "Fired"
    else:
        l1 = "Not met"
    trace.append(row("RULE-L01", f"IF current_ratio > {HARD_MIN_CURRENT_RATIO} → liquidity = ADEQUATE", l1))

    # ── Final suitability ──
    trace.append(row(
        "RULE-S01",
        "IF fundamental pass + ¬hard_stop → sector rules → final verdict",
        "Fired" if has_recommendation else "Not met",
    ))

    return trace


# ── Confidence score ───────────────────────────────────────────────────────────

def compute_confidence(
    stock_data: dict,
    verdict: Verdict,
    signals: dict,
    has_fundamental_pass: bool,
    engine_facts: dict,
) -> int:
    if verdict == Verdict.AVOID and stock_data.get("is_pn17"):
        return 95

    if not has_fundamental_pass:
        return 55

    conf = 90
    tech = signals.get("technical", "Neutral")
    if tech == "Neutral":
        conf = min(conf, 78)
    elif tech == "Bearish":
        conf = min(conf, 62)

    if any(isinstance(f, LowSavingsFlag) for f in engine_facts.values()):
        conf -= 5
    if any(isinstance(f, ShortHorizonFlag) for f in engine_facts.values()):
        sector = stock_data.get("sector")
        if sector in VOLATILE_SECTORS:
            conf -= 5

    return max(50, min(95, conf))


# ── Declare peer benchmarks ───────────────────────────────────────────────────

def _declare_peer_benchmarks(engine: BursaAdvisor, sectors: set) -> None:
    for sector in sectors:
        cfg = try_load_sector_config(str(sector))
        if not cfg or not cfg.get("benchmark_peers"):
            continue
        avg, is_live = compute_peer_avg(
            cfg["benchmark_peers"], cfg["primary_metric"], cfg["peer_avg_fallback"]
        )
        engine.declare(PeerBenchmark(
            sector=sector,
            metric=cfg["primary_metric"],
            value=avg,
            avoid_multiplier=cfg.get("avoid_multiplier", 1.2),
            is_live=is_live,
        ))


# ── Run full analysis ─────────────────────────────────────────────────────────

def run_full_analysis(ticker: str, profile_data: dict, extra_inputs: dict) -> dict:
    stock_data = fetch_stock_data(ticker)
    stock_data.update(extra_inputs)

    macro = fetch_macro()

    engine = BursaAdvisor()
    engine.reset()
    engine.declare(InvestorProfile(**profile_data))
    engine.declare(MacroData(**macro))
    engine.declare(Stock(**{k: v for k, v in stock_data.items() if k in Stock.__fields__}))

    sector = stock_data.get("sector")
    if sector:
        _declare_peer_benchmarks(engine, {sector})

    engine.run()
    facts = engine.facts

    recommendation = next(
        (f for f in facts.values() if isinstance(f, Recommendation) and f.get("ticker") == ticker),
        None,
    )
    has_fundamental_pass = any(
        isinstance(f, FundamentalPass) and f.get("ticker") == ticker
        for f in facts.values()
    )

    verdict = recommendation["verdict"] if recommendation else Verdict.WATCH
    reason = recommendation["reason"] if recommendation else "Insufficient data for analysis."

    signals = compute_signal_badges(stock_data, profile_data)
    confidence = compute_confidence(stock_data, verdict, signals, has_fundamental_pass, facts)
    rule_trace = build_rule_trace(stock_data, profile_data, facts)

    cfg = try_load_sector_config(str(sector)) if sector else None
    peer_avg = cfg["peer_avg_fallback"] if cfg else None
    for f in facts.values():
        if isinstance(f, PeerBenchmark) and str(f.get("sector")) == str(sector):
            peer_avg = f.get("value")
            break

    return {
        "stock_data": stock_data,
        "macro": macro,
        "verdict": verdict,
        "reason": reason,
        "signals": signals,
        "confidence": confidence,
        "rule_trace": rule_trace,
        "has_fundamental_pass": has_fundamental_pass,
        "peer_avg": peer_avg,
        "peer_metric": cfg.get("primary_metric") if cfg else None,
        "sector_cfg": cfg,
    }


# ── UI helpers ────────────────────────────────────────────────────────────────

def verdict_display(verdict: Verdict) -> str:
    return {"BUY": "Suitable", "WATCH": "Monitor", "AVOID": "Avoid"}.get(str(verdict), str(verdict))


def badge_html(label: str) -> str:
    cls = {
        "Undervalued": "badge-green", "Fair Value": "badge-yellow", "Overvalued": "badge-red",
        "Bullish": "badge-green",     "Neutral": "badge-yellow",    "Bearish": "badge-red",
        "Low risk": "badge-green",    "Moderate risk": "badge-yellow", "High risk": "badge-red",
    }.get(label, "badge-gray")
    return f'<span class="badge {cls}">{label}</span>'


def fmt_val(v, fmt=".1f", suffix="") -> str:
    if v is None:
        return "N/A"
    try:
        return f"{v:{fmt}}{suffix}"
    except Exception:
        return str(v)


def trace_status_html(status: str) -> str:
    if status == "Fired":
        return '<span class="trace-fired">Fired</span>'
    if status == "Skipped":
        return '<span class="trace-skipped">Skipped</span>'
    return '<span class="trace-notmet">Not met</span>'


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar() -> tuple[dict, dict]:
    st.sidebar.markdown('<div class="section-label">Investor Profile</div>', unsafe_allow_html=True)

    age_label = st.sidebar.selectbox("Age range", list(AGE_LABELS.keys()), index=1)
    savings_label = st.sidebar.selectbox(
        "Monthly savings rate",
        list(SAVINGS_LABELS.keys()),
        index=2,
        help="Below 20% triggers a capital buffer warning that can downgrade volatile sector BUY → WATCH",
    )
    savings_ratio = SAVINGS_LABELS[savings_label]

    st.sidebar.markdown("---")
    st.sidebar.markdown('<div class="section-label">Compliance flags</div>', unsafe_allow_html=True)
    is_pn17 = st.sidebar.checkbox(
        "Stock is under PN17 distress listing",
        value=False,
        help="Triggers immediate AVOID — financial distress / delisting risk",
    )
    auditor_qualified = st.sidebar.checkbox(
        "Auditor issued qualified/adverse opinion",
        value=False,
        help="Triggers immediate AVOID — reliability risk",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown('<div class="section-label">Sector-specific inputs</div>', unsafe_allow_html=True)

    detected_sector = st.session_state.get("detected_sector")

    distribution_yield = None
    occupancy_rate = None
    export_revenue_pct = None
    order_book_rm = None

    if detected_sector in SECTORS_NEEDING_DIST_YIELD:
        distribution_yield = st.sidebar.number_input(
            "Distribution yield (%)", min_value=0.0, max_value=20.0, value=6.0, step=0.1,
            help="Annual payout to unitholders ÷ unit price. BUY threshold: ≥ peer avg.",
        )
    if detected_sector in SECTORS_NEEDING_OCCUPANCY:
        occupancy_rate = st.sidebar.number_input(
            "Portfolio occupancy rate (%)", min_value=0.0, max_value=100.0, value=90.0, step=0.5,
            help="% of lettable space currently tenanted. BUY threshold: ≥ 90%.",
        )
    if detected_sector in SECTORS_NEEDING_EXPORT:
        export_revenue_pct = st.sidebar.number_input(
            "Export revenue (% of total)", min_value=0.0, max_value=100.0, value=60.0, step=1.0,
            help="Higher % = more USD exposure = benefits when MYR weakens.",
        )
    if detected_sector in SECTORS_NEEDING_ORDER_BOOK:
        order_book_rm = st.sidebar.number_input(
            "Outstanding order book (RM billions)", min_value=0.0, value=5.0, step=0.5,
            help="Total unexecuted contract value — revenue visibility.",
        )

    profile_data = {
        "age": AGE_LABELS[age_label],
        "monthly_income": 5000.0,           # mandatory fact field; no rule uses it
        "monthly_savings": round(5000.0 * savings_ratio, 2),
        "savings_ratio": savings_ratio,
        "risk_tolerance": st.session_state.get("risk_tolerance", RiskTolerance.MODERATE),
        "investment_horizon": st.session_state.get("investment_horizon", 4),
        "income_preference": st.session_state.get("income_preference", False),
    }

    extra_inputs = {"is_pn17": is_pn17, "auditor_qualified": auditor_qualified}
    if distribution_yield is not None:
        extra_inputs["distribution_yield"] = distribution_yield
    if occupancy_rate is not None:
        extra_inputs["occupancy_rate"] = occupancy_rate
    if export_revenue_pct is not None:
        extra_inputs["export_revenue_pct"] = export_revenue_pct
    if order_book_rm is not None:
        extra_inputs["order_book_rm"] = order_book_rm

    return profile_data, extra_inputs


# ── Signal analysis (3 cards) ─────────────────────────────────────────────────

def render_signal_analysis(result: dict):
    stock = result["stock_data"]
    signals = result["signals"]

    st.markdown(
        '<div class="section-label">Signal analysis — 3 chains evaluated</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    # ── Fundamental ──────────────────────────────────────────────────────────
    # All 5 metrics are used by fundamentals.py or hard_stops.py
    with col1:
        rows = [
            ("P/E ratio",      fmt_val(stock.get("pe_ratio"),       ".1f", "x")),
            ("P/B ratio",      fmt_val(stock.get("pb_ratio"),       ".1f", "x")),
            ("Dividend yield", fmt_val(stock.get("dividend_yield"), ".1f", "%")),
            ("Payout ratio",   fmt_val(stock.get("payout_ratio"),   ".0f", "%")),
            ("Current ratio",  fmt_val(stock.get("current_ratio"),  ".2f")),
        ]
        rows_html = "".join(
            f'<div class="metric-row"><span class="metric-label">{lbl}</span>'
            f'<span class="metric-value">{val}</span></div>'
            for lbl, val in rows
        )
        st.markdown(f"""
<div class="card">
  <div class="card-header">Fundamental</div>
  {badge_html(signals["fundamental"])}
  {rows_html}
</div>""", unsafe_allow_html=True)

    # ── Technical ─────────────────────────────────────────────────────────────
    # Only RSI and golden_cross — exactly what technicals.py checks
    with col2:
        rsi = stock.get("rsi")
        golden_cross = stock.get("golden_cross", False)
        rsi_str = fmt_val(rsi, ".1f")
        gc_str = "Yes" if golden_cross else "No"
        rows = [
            ("RSI (14d)",          rsi_str),
            ("Golden cross (50d > 200d MA)", gc_str),
        ]
        rows_html = "".join(
            f'<div class="metric-row"><span class="metric-label">{lbl}</span>'
            f'<span class="metric-value">{val}</span></div>'
            for lbl, val in rows
        )
        st.markdown(f"""
<div class="card">
  <div class="card-header">Technical</div>
  {badge_html(signals["technical"])}
  {rows_html}
</div>""", unsafe_allow_html=True)

    # ── Risk / Regulatory ─────────────────────────────────────────────────────
    # All metrics correspond to hard_stops.py checks
    with col3:
        losses = stock.get("consecutive_losses") or 0
        rows = [
            ("PN17 status",        "Yes" if stock.get("is_pn17") else "No"),
            ("Debt-to-equity",     fmt_val(stock.get("debt_to_equity"), ".2f", "x")),
            ("Market cap",         fmt_val(stock.get("market_cap_b"), ".2f", "B RM")),
            ("Consecutive losses", f"{losses} qtrs"),
            ("Auditor opinion",    "Qualified" if stock.get("auditor_qualified") else "Clean"),
        ]
        rows_html = "".join(
            f'<div class="metric-row"><span class="metric-label">{lbl}</span>'
            f'<span class="metric-value">{val}</span></div>'
            for lbl, val in rows
        )
        st.markdown(f"""
<div class="card">
  <div class="card-header">Risk / Regulatory</div>
  {badge_html(signals["risk"])}
  {rows_html}
</div>""", unsafe_allow_html=True)


# ── Recommendation + rule trace ───────────────────────────────────────────────

def render_recommendation_and_trace(result: dict):
    verdict = result["verdict"]
    confidence = result["confidence"]
    reason = result["reason"]
    rule_trace = result["rule_trace"]
    stock = result["stock_data"]
    ticker = stock.get("ticker", "")
    name = stock.get("name", ticker)

    v_str = str(verdict)
    display = verdict_display(verdict)
    css_card    = {"BUY": "rec-suitable", "WATCH": "rec-monitor", "AVOID": "rec-avoid"}.get(v_str, "rec-monitor")
    css_verdict = {"BUY": "rec-verdict-suitable", "WATCH": "rec-verdict-monitor", "AVOID": "rec-verdict-avoid"}.get(v_str, "rec-verdict-monitor")
    css_bar     = {"BUY": "conf-bar-fill-green", "WATCH": "conf-bar-fill-yellow", "AVOID": "conf-bar-fill-red"}.get(v_str, "conf-bar-fill-yellow")

    left, right = st.columns([3, 2])

    with left:
        st.markdown('<div class="section-label">Recommendation</div>', unsafe_allow_html=True)
        st.markdown(f"""
<div class="rec-card {css_card}">
  <div class="rec-label">Verdict for your profile</div>
  <div class="{css_verdict}">{display}</div>
  <div class="conf-bar-bg"><div class="{css_bar}" style="width:{confidence}%"></div></div>
  <div class="rec-confidence">Confidence level &nbsp;<strong>{confidence}%</strong></div>
  <div class="rec-reason">{reason}</div>
</div>""", unsafe_allow_html=True)

        wl = st.session_state.setdefault("watchlist", [])
        if not any(w["ticker"] == ticker for w in wl):
            if st.button("+ Add to Watchlist", key=f"wl_add_{ticker}"):
                wl.append({
                    "ticker": ticker,
                    "name": name,
                    "sector": str(stock.get("sector", "")),
                    "verdict": v_str,
                    "display": display,
                })
                st.rerun()
        else:
            st.caption("✓ In watchlist")

    with right:
        st.markdown('<div class="section-label">Rule trace — inference log</div>', unsafe_allow_html=True)
        rows_html = "".join(
            f'<div class="trace-row">'
            f'<span class="trace-id">{r["id"]}</span>'
            f'<span class="trace-cond">{r["condition"]}</span>'
            f'{trace_status_html(r["status"])}'
            f'</div>'
            for r in rule_trace
        )
        st.markdown(f'<div class="card" style="padding:12px 16px">{rows_html}</div>', unsafe_allow_html=True)


# ── Watchlist ─────────────────────────────────────────────────────────────────

def render_watchlist():
    wl = st.session_state.get("watchlist", [])
    if not wl:
        return

    st.markdown('<div class="section-label">Watchlist</div>', unsafe_allow_html=True)

    badge_css = {"Suitable": "wl-badge-suitable", "Monitor": "wl-badge-monitor", "Avoid": "wl-badge-avoid"}
    rows_html = "".join(
        f'<div class="wl-row">'
        f'<div><div class="wl-name">{item["name"]}</div>'
        f'<div class="wl-meta">{item["ticker"]} · {item["sector"]}</div></div>'
        f'<div class="{badge_css.get(item["display"], "wl-badge-monitor")}">{item["display"]}</div>'
        f'</div>'
        for item in wl
    )
    st.markdown(f'<div class="card">{rows_html}</div>', unsafe_allow_html=True)

    if st.button("Clear watchlist"):
        st.session_state["watchlist"] = []
        st.rerun()


# ── Macro context ─────────────────────────────────────────────────────────────

def render_macro_context(result: dict):
    macro = result["macro"]
    sector = result["stock_data"].get("sector")
    cfg = result.get("sector_cfg") or {}

    sector_str = str(sector).upper() if sector else "MARKET"
    st.markdown(
        f'<div class="section-label">Macro context — {sector_str} sector</div>',
        unsafe_allow_html=True,
    )

    opr_str  = f"{macro['opr']:.2f}%" if macro.get("opr") else "Unavailable"
    fx_str   = f"{macro['usd_myr']:.3f}" if macro.get("usd_myr") else "Unavailable"
    peer_avg = result.get("peer_avg")
    peer_metric = result.get("peer_metric") or ""
    peer_str = f"{peer_avg:.2f}x" if peer_avg is not None else "N/A"

    chips_html = "".join(
        f'<span class="macro-chip"><b>{lbl}</b>&nbsp; {val}</span>'
        for lbl, val in [("OPR (BNM)", opr_str), ("USD/MYR", fx_str), (f"Peer avg ({peer_metric})", peer_str)]
    )
    st.markdown(f'<div class="card">{chips_html}', unsafe_allow_html=True)

    for driver in cfg.get("macro_drivers", []):
        st.markdown(f"<div style='font-size:12px;color:#94a3b8;padding:2px 0'>· {driver}</div>", unsafe_allow_html=True)

    for flag in cfg.get("red_flags", []):
        st.markdown(f"<div style='font-size:12px;color:#f87171;padding:2px 0'>⚠ {flag}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.session_state.setdefault("watchlist", [])
    st.session_state.setdefault("analysis", None)
    st.session_state.setdefault("detected_sector", None)
    st.session_state.setdefault("risk_tolerance", RiskTolerance.MODERATE)
    st.session_state.setdefault("investment_horizon", 4)
    st.session_state.setdefault("income_preference", False)

    profile_data, extra_inputs = render_sidebar()

    # ── Header ──
    st.markdown(
        "<h2 style='margin-bottom:0;color:#e2e8f0;letter-spacing:1px'>📈 BursaAdvisor</h2>"
        "<div style='font-size:12px;color:#4b5563;margin-bottom:16px'>"
        "Knowledge-based expert system for Bursa Malaysia stock screening</div>",
        unsafe_allow_html=True,
    )

    # ── Stock lookup ──
    st.markdown('<div class="section-label">Stock Lookup</div>', unsafe_allow_html=True)
    col_ticker, col_market, col_btn = st.columns([3, 2, 1])
    with col_ticker:
        ticker_input = st.text_input(
            "Bursa ticker", value=st.session_state.get("last_ticker", ""),
            placeholder="e.g. 1295.KL", label_visibility="collapsed",
        )
    with col_market:
        market = st.selectbox("Market", MARKET_OPTIONS, label_visibility="collapsed")
    with col_btn:
        fetch_clicked = st.button("Fetch data", type="primary", use_container_width=True)

    # ── Investor profile row ──
    st.markdown('<div class="section-label">Investor Profile</div>', unsafe_allow_html=True)
    pcol1, pcol2, pcol3 = st.columns(3)

    with pcol1:
        risk_label = st.selectbox("Risk Appetite", list(RISK_LABELS.keys()), index=1)
        st.session_state["risk_tolerance"] = RISK_LABELS[risk_label]

    with pcol2:
        horizon_label = st.selectbox("Investment Horizon", list(HORIZON_LABELS.keys()), index=1)
        st.session_state["investment_horizon"] = HORIZON_LABELS[horizon_label]

    with pcol3:
        div_label = st.selectbox("Dividend Preference", ["Growth-focused", "Income-focused"])
        st.session_state["income_preference"] = (div_label == "Income-focused")

    # Sync session state into profile_data
    profile_data["risk_tolerance"]    = st.session_state["risk_tolerance"]
    profile_data["investment_horizon"] = st.session_state["investment_horizon"]
    profile_data["income_preference"]  = st.session_state["income_preference"]

    # ── Fetch & analyse ──
    if fetch_clicked and ticker_input.strip():
        ticker = ticker_input.strip().upper()
        st.session_state["last_ticker"] = ticker
        with st.spinner(f"Fetching {ticker} and running inference engine..."):
            try:
                result = run_full_analysis(ticker, profile_data, extra_inputs)
                st.session_state["analysis"] = result
                st.session_state["detected_sector"] = result["stock_data"].get("sector")
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.session_state["analysis"] = None

    # ── Results ──
    result = st.session_state.get("analysis")
    if result:
        stock = result["stock_data"]
        st.markdown(
            f"<div style='font-size:13px;color:#94a3b8;margin:8px 0'>"
            f"<b style='color:#e2e8f0'>{stock.get('name', stock.get('ticker',''))}</b>&nbsp; "
            f"<span style='color:#4b5563'>{stock.get('ticker','')} · {stock.get('sector','')} · {market}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        render_signal_analysis(result)
        render_recommendation_and_trace(result)
        render_watchlist()
        render_macro_context(result)
    else:
        render_watchlist()
        st.markdown(
            "<div style='text-align:center;color:#4b5563;padding:60px 0;font-size:13px'>"
            "Enter a Bursa Malaysia ticker above and click <b>Fetch data</b> to begin analysis."
            "</div>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__" or True:
    main()
