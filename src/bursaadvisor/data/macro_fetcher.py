"""
Fetches Malaysian macro indicators that affect multiple sectors.
Called once per session in __main__.py before engine.run().
"""
import requests
import yfinance as yf

_BNM_OPR_URL = "https://api.bnm.gov.my/public/opr"
_BNM_HEADERS = {"Accept": "application/vnd.BNM.API.v1+json"}


def fetch_opr() -> float | None:
    """
    Fetches current OPR from Bank Negara Malaysia Open API.
    OPR = Overnight Policy Rate — BNM's main monetary policy tool.
    Higher OPR → higher borrowing costs → bad for REITs, Property, Utilities, Construction.
    Lower OPR → cheaper credit → good for those same sectors.
    """
    try:
        r = requests.get(_BNM_OPR_URL, headers=_BNM_HEADERS, timeout=5)
        r.raise_for_status()
        return float(r.json()["data"]["new_opr_level"])
    except Exception:
        return None


def fetch_usd_myr() -> float | None:
    """
    Fetches current USD/MYR exchange rate from yfinance.
    Value = how many RM per 1 USD (e.g. 4.45 means USD 1 = RM 4.45).
    Higher rate (weaker MYR) → good for exporters: Technology, Gloves, Plantation.
    Lower rate (stronger MYR) → bad for exporters, good for importers.
    """
    try:
        info = yf.Ticker("USDMYR=X").info
        rate = info.get("regularMarketPrice") or info.get("previousClose")
        return float(rate) if rate else None
    except Exception:
        return None


def fetch_macro() -> dict:
    """Returns dict with all macro indicators. None values mean fetch failed."""
    return {
        "opr":     fetch_opr(),
        "usd_myr": fetch_usd_myr(),
    }
