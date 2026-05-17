"""Universal thresholds only — numbers that apply across ALL sectors and investor profiles.

Sector-specific thresholds live in data/sector_configs/*.json.
"""

from .enums import Sector, RiskTolerance

# Sectors exempt from D/E (R04) and current ratio (R05) hard stops.
# These carry structurally high leverage or low current ratios by design.
EXEMPT_FROM_DE_CR = {Sector.BANKING, Sector.HEALTHCARE, Sector.UTILITIES, Sector.REITS}

# --- Hard stop thresholds (universal, all sectors) ---
HARD_MAX_DE_RATIO = 2.0
HARD_MIN_CURRENT_RATIO = 1.0
HARD_MAX_CONSEC_LOSSES = 2
HARD_MIN_MARKET_CAP_B = 0.5   # RM billions

# --- Investor risk profile gates (applied before sector rules) ---
RISK_THRESHOLDS = {
    RiskTolerance.CONSERVATIVE: {"max_pe": 18.0, "min_div": 4.5, "max_payout": 70.0},
    RiskTolerance.MODERATE:     {"max_pe": 28.0, "min_div": 3.0, "max_payout": 80.0},
    RiskTolerance.AGGRESSIVE:   {"max_pe": 40.0, "min_div": 1.0, "max_payout": 90.0},
}
INCOME_SHIFT_MIN_DIV = 4.5    # minimum div % required when income_shift is active

# --- Technical signal thresholds (universal, all sectors) ---
RSI_OVERBOUGHT = 70.0
RSI_OVERSOLD = 30.0

# --- yfinance sector string → BursaAdvisor Sector enum ---
YFINANCE_SECTOR_MAP = {
    "Financial Services": Sector.BANKING,
    "Banks":              Sector.BANKING,
    "Technology":         Sector.TECHNOLOGY,
    "Real Estate":        Sector.REITS,
    "Consumer Defensive": Sector.CONSUMER,
    "Consumer Cyclical":  Sector.CONSUMER,
    "Healthcare":         Sector.HEALTHCARE,
    "Utilities":          Sector.UTILITIES,
    "Basic Materials":    Sector.PLANTATION,
    "Industrials":        Sector.CONSTRUCTION,
    "Energy":             Sector.UTILITIES,
    "Communication Services": Sector.TECHNOLOGY,
}

GLOVE_TICKERS = {"7113.KL", "5168.KL", "0072.KL", "7229.KL"}

REIT_TICKERS = {"5176.KL", "5212.KL", "5109.KL", "5307.KL", "5106.KL"}

PROPERTY_TICKERS = {"8206.KL", "8664.KL", "5288.KL", "5249.KL", "8583.KL"}

CONSTRUCTION_TICKERS = {"5263.KL", "1651.KL", "5398.KL", "9679.KL"}