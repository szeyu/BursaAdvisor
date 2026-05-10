import yfinance as yf
import pandas as pd
from ..enums import Sector
from ..constants import YFINANCE_SECTOR_MAP, GLOVE_TICKERS


def _map_sector(yf_sector: str, ticker: str) -> Sector:
    if ticker.upper() in GLOVE_TICKERS:
        return Sector.GLOVES
    return YFINANCE_SECTOR_MAP.get(yf_sector, Sector.UNKNOWN)


def _compute_rsi(hist: pd.DataFrame, period: int = 14) -> float | None:
    if hist.empty or len(hist) < period + 1:
        return None
    delta = hist["Close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi_series = 100 - (100 / (1 + rs))
    last = rsi_series.dropna()
    return float(last.iloc[-1]) if not last.empty else None


def _compute_golden_cross(hist: pd.DataFrame) -> bool:
    if len(hist) < 200:
        return False
    ma50 = hist["Close"].rolling(50).mean().iloc[-1]
    ma200 = hist["Close"].rolling(200).mean().iloc[-1]
    return bool(ma50 > ma200)


def _compute_consecutive_losses(ticker_obj: yf.Ticker) -> int:
    try:
        income = ticker_obj.quarterly_income_stmt
        if income is None or income.empty:
            return 0
        net_income_row = None
        for label in ["Net Income", "NetIncome", "Net Income Common Stockholders"]:
            if label in income.index:
                net_income_row = income.loc[label]
                break
        if net_income_row is None:
            return 0
        count = 0
        for val in net_income_row.values:
            if val is not None and val < 0:
                count += 1
            else:
                break
        return count
    except Exception:
        return 0


def fetch_stock_data(ticker: str) -> dict:
    base = {
        "ticker": ticker,
        "name": ticker,
        "sector": "Unknown",
        # Valuation
        "pe_ratio": None,
        "pb_ratio": None,
        "ev_ebitda": None,
        # Income
        "dividend_yield": None,
        "distribution_yield": None,
        "payout_ratio": None,
        "eps_growth_yoy": None,
        # Profitability & growth
        "revenue_growth": None,
        "gross_margin": None,
        "operating_margin": None,
        "ebitda_margin": None,
        "roe": None,
        "roa": None,
        "free_cashflow_b": None,
        "beta": None,
        # Balance sheet
        "debt_to_equity": None,
        "current_ratio": None,
        "market_cap_b": None,
        # Technical
        "rsi": None,
        "golden_cross": False,
        "consecutive_losses": 0,
        # Compliance (defaults; overridden by user prompts)
        "is_pn17": False,
        "auditor_qualified": False,
        # Sector-specific (filled by user prompts after fetch)
        "export_revenue_pct": None,
        "occupancy_rate": None,
        "order_book_rm": None,
    }
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        base["name"] = info.get("longName") or info.get("shortName") or ticker
        base["sector"] = _map_sector(info.get("sector", ""), ticker)  # returns Sector enum

        raw_pe = info.get("trailingPE") or info.get("forwardPE")
        base["pe_ratio"] = float(raw_pe) if raw_pe else None

        raw_pb = info.get("priceToBook")
        base["pb_ratio"] = float(raw_pb) if raw_pb else None

        raw_ev = info.get("enterpriseToEbitda")
        base["ev_ebitda"] = float(raw_ev) if raw_ev else None

        raw_div = info.get("dividendYield")
        base["dividend_yield"] = float(raw_div) if raw_div else None

        raw_payout = info.get("payoutRatio")
        base["payout_ratio"] = float(raw_payout) * 100 if raw_payout else None

        # EPS growth: yfinance earningsGrowth is YoY as decimal (e.g. 0.12 = 12%)
        raw_eg = info.get("earningsGrowth")
        base["eps_growth_yoy"] = float(raw_eg) * 100 if raw_eg else None

        # --- Profitability & growth ---
        # yfinance returns all margin/growth fields as decimals (e.g. 0.15 = 15%).
        # We convert to % for readability. Fields return None (not 0.0) when not
        # applicable for a sector (e.g. Banking has no "gross margin" concept).

        # % revenue growth YoY — useful for Technology, Construction, Consumer, Healthcare
        raw_rg = info.get("revenueGrowth")
        base["revenue_growth"] = float(raw_rg) * 100 if raw_rg else None

        # % gross profit / revenue — useful for Plantation, Gloves, Technology, Healthcare.
        # Returns None for Banking (banks have no cost-of-goods in the traditional sense).
        raw_gm = info.get("grossMargins")
        base["gross_margin"] = float(raw_gm) * 100 if raw_gm else None

        # % operating profit / revenue — useful across all sectors.
        # For Banking this reflects net interest margin efficiency.
        raw_om = info.get("operatingMargins")
        base["operating_margin"] = float(raw_om) * 100 if raw_om else None

        # % EBITDA / revenue — useful for Plantation, Gloves, Utilities.
        # Returns None for Banking (EBITDA is not a standard bank metric).
        raw_em = info.get("ebitdaMargins")
        base["ebitda_margin"] = float(raw_em) * 100 if raw_em else None

        # % return on equity — key metric for Banking (benchmark: ROE ≥ 10%).
        # Also useful for REITs, Healthcare, Consumer.
        raw_roe = info.get("returnOnEquity")
        base["roe"] = float(raw_roe) * 100 if raw_roe else None

        # % return on assets — key metric for Banking (benchmark: ROA ≥ 1%).
        # Low ROA for Utilities is normal (asset-heavy regulated business).
        raw_roa = info.get("returnOnAssets")
        base["roa"] = float(raw_roa) * 100 if raw_roa else None

        # RM billions free cash flow — useful for Technology, Healthcare, Plantation.
        # Negative FCF is normal for Utilities & Construction (heavy capex).
        # Returns None for Banking (cash flow has different meaning for financial institutions).
        raw_fcf = info.get("freeCashflow")
        base["free_cashflow_b"] = float(raw_fcf) / 1e9 if raw_fcf else None

        # Beta vs market — how volatile the stock is relative to KLCI.
        # > 1.0 = more volatile than market, < 1.0 = more stable.
        # Useful across all sectors for risk-adjusted recommendation context.
        raw_beta = info.get("beta")
        base["beta"] = float(raw_beta) if raw_beta else None

        raw_de = info.get("debtToEquity")
        base["debt_to_equity"] = float(raw_de) / 100 if raw_de else None

        raw_cr = info.get("currentRatio")
        base["current_ratio"] = float(raw_cr) if raw_cr else None

        raw_mc = info.get("marketCap")
        base["market_cap_b"] = float(raw_mc) / 1e9 if raw_mc else None

        hist = t.history(period="1y")
        base["rsi"] = _compute_rsi(hist)
        base["golden_cross"] = _compute_golden_cross(hist)
        base["consecutive_losses"] = _compute_consecutive_losses(t)

    except Exception as e:
        from rich.console import Console
        Console(stderr=True).print(f"[yellow]Warning:[/yellow] Failed to fetch data for {ticker}: {e}")

    return base
