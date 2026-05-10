from experta import Fact, Field


class InvestorProfile(Fact):
    age = Field(object, mandatory=True)
    monthly_income = Field(object, mandatory=True)
    monthly_savings = Field(object, mandatory=True)
    savings_ratio = Field(object, mandatory=True)
    risk_tolerance = Field(object, mandatory=True)
    investment_horizon = Field(object, mandatory=True)
    income_preference = Field(object, mandatory=True)


class Stock(Fact):
    # Identity
    ticker = Field(object, mandatory=True)
    name = Field(object, mandatory=True)
    sector = Field(object, mandatory=True)
    # Valuation
    pe_ratio = Field(object, default=None)
    pb_ratio = Field(object, default=None)
    ev_ebitda = Field(object, default=None)
    # Income
    dividend_yield = Field(object, default=None)
    distribution_yield = Field(object, default=None)
    payout_ratio = Field(object, default=None)
    eps_growth_yoy = Field(object, default=None)
    # --- Profitability & growth (all in %, None = not applicable for that sector) ---
    # Use these fields in your sector rules. Always guard: TEST(lambda x: x is not None and ...)
    revenue_growth = Field(object, default=None)
    # ^ % revenue growth YoY. Useful for: Technology, Construction, Consumer, Healthcare.

    gross_margin = Field(object, default=None)
    # ^ % gross profit ÷ revenue. Useful for: Plantation, Gloves, Technology, Healthcare.
    #   Returns None for Banking — banks have no traditional cost-of-goods.

    operating_margin = Field(object, default=None)
    # ^ % operating profit ÷ revenue. Useful across all sectors.
    #   For Banking, reflects net interest margin efficiency.

    ebitda_margin = Field(object, default=None)
    # ^ % EBITDA ÷ revenue. Useful for: Plantation, Gloves, Utilities.
    #   Returns None for Banking — EBITDA is not a standard bank metric.

    roe = Field(object, default=None)
    # ^ % return on equity. KEY metric for Banking (benchmark: ROE ≥ 10%).
    #   Also useful for REITs, Healthcare, Consumer.

    roa = Field(object, default=None)
    # ^ % return on assets. KEY metric for Banking (benchmark: ROA ≥ 1%).
    #   Low ROA is normal for Utilities (asset-heavy regulated business).

    free_cashflow_b = Field(object, default=None)
    # ^ RM billions free cash flow. Useful for: Technology, Healthcare, Plantation.
    #   Negative FCF is normal for Utilities & Construction (high capital expenditure).
    #   Returns None for Banking — cash flow has different meaning for financial institutions.

    beta = Field(object, default=None)
    # ^ Price volatility vs KLCI. >1.0 = more volatile than market, <1.0 = more stable.
    #   Useful across all sectors for risk-adjusted context.
    # Balance sheet
    debt_to_equity = Field(object, default=None)
    current_ratio = Field(object, default=None)
    market_cap_b = Field(object, default=None)
    # Technical
    rsi = Field(object, default=None)
    golden_cross = Field(object, default=False)
    consecutive_losses = Field(object, default=0)
    # Compliance flags (user-supplied)
    is_pn17 = Field(object, default=False)
    auditor_qualified = Field(object, default=False)
    # Sector-specific (user-supplied)
    export_revenue_pct = Field(object, default=None)
    occupancy_rate = Field(object, default=None)
    order_book_rm = Field(object, default=None)


class Recommendation(Fact):
    ticker = Field(object, mandatory=True)
    verdict = Field(object, mandatory=True)
    reason = Field(object, mandatory=True)


# --- Intermediate inference facts (typed, not raw Fact with magic keys) ---

class IncomeShiftFlag(Fact):
    """Fired when investor age >= 45 — switches to income-oriented evaluation."""
    pass


class LowSavingsFlag(Fact):
    """Fired when investor savings ratio < 20% — advisory warning only, not a hard stop."""
    pass


class FundamentalPass(Fact):
    """Fired when a stock clears the fundamental gate for the investor's risk profile."""
    ticker = Field(object, mandatory=True)
    note = Field(object, default="")


class ShortHorizonFlag(Fact):
    """Fired when investment_horizon < 3 years — volatile sectors downgraded BUY → WATCH."""
    pass


class MacroData(Fact):
    """
    Malaysian macro indicators fetched automatically before inference.
    Declared once per session — all sector rules can match on it.

    Usage in a rule:
        MacroData(opr=MATCH.opr, usd_myr=MATCH.rate)
        TEST(lambda opr: opr > 3.0)   # high OPR → bad for REITs/Property/Utilities

    Sector relevance:
        opr      → Banking (NIM), REITs (borrowing cost), Utilities (debt financing),
                   Property (mortgage rates), Construction (project financing)
        usd_myr  → Technology (export revenue in USD), Gloves (USD revenue),
                   Plantation (CPO sold in USD), Healthcare (medical tourism)
    """
    opr = Field(object, default=None)        # % e.g. 2.75 — Bank Negara OPR
    usd_myr = Field(object, default=None)    # e.g. 4.45 — how many RM per 1 USD


class PeerBenchmark(Fact):
    """
    Live-computed peer average for a sector's primary valuation metric.
    Declared before engine.run() — sector rules match on this instead of hardcoded constants.
    """
    sector = Field(object, mandatory=True)
    metric = Field(object, mandatory=True)           # e.g. "pb_ratio"
    value = Field(object, mandatory=True)            # computed peer average
    avoid_multiplier = Field(object, default=1.2)    # avoid threshold = value * multiplier
    is_live = Field(object, default=False)           # True = fetched live; False = fallback
