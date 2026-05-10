"""
Fetches the primary valuation metric for a sector's benchmark peers and returns the average.
Used to compute a live peer average before engine.run(), which is then declared as a PeerBenchmark fact.
"""
import yfinance as yf

_YF_FIELD_MAP = {
    "pb_ratio":       "priceToBook",
    "pe_ratio":       "trailingPE",
    "dividend_yield": "dividendYield",
    "ev_ebitda":      "enterpriseToEbitda",
}


def compute_peer_avg(
    peers: list[dict],
    metric: str,
    fallback: float,
) -> tuple[float, bool]:
    """
    Returns (avg_value, is_live).
    is_live=True  → successfully fetched from yfinance.
    is_live=False → all fetches failed; fallback value used.
    """
    yf_field = _YF_FIELD_MAP.get(metric)
    if not yf_field:
        return fallback, False

    tickers_str = " ".join(p["ticker"] for p in peers)
    values: list[float] = []

    try:
        bundle = yf.Tickers(tickers_str)
        for peer in peers:
            try:
                info = bundle.tickers[peer["ticker"]].info or {}
                raw = info.get(yf_field)
                if raw is not None:
                    values.append(float(raw))
            except Exception:
                continue
    except Exception:
        pass

    if values:
        avg = round(sum(values) / len(values), 4)
        return avg, True

    return fallback, False
