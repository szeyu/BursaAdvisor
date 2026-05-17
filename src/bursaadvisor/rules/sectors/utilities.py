"""
Utilities sector rules — salience=20.
Dual-metric sector: P/E ratio AND dividend yield both evaluated.
Peer tickers   : Tenaga Nasional (5347.KL), Ranhill Utilities (5026.KL),
                 YTL Power (6742.KL), Malakoff (5264.KL)
Key macro      : OPR (debt financing cost on capital-heavy infrastructure),
                 coal/fuel price (generation cost; ICPT pass-through lag)
Note           : Utilities are a core INCOME sector — dividend yield
                 is co-equal with P/E; a broken yield thesis = AVOID
                 regardless of P/E alone.
"""
from experta import Rule, MATCH, NOT, TEST
from ...facts import Stock, Recommendation, FundamentalPass, PeerBenchmark, MacroData
from ...enums import Sector, Verdict
from ...data.config_loader import load_sector_config

_cfg = load_sector_config("utilities")
_AVOID_MULT: float  = _cfg["avoid_multiplier"]
_MIN_YIELD: float   = _cfg.get("min_div_yield", 4.0)    # conservative income floor
_BROKEN_YIELD: float = _cfg.get("broken_yield_threshold", 3.0)  # income thesis broken


class UtilitiesRules:

    # ── BUY ───────────────────────────────────────────────────────────────────

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.UTILITIES,
              pe_ratio=MATCH.pe, dividend_yield=MATCH.dy),
        PeerBenchmark(sector=Sector.UTILITIES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg: pe is not None and pe < peer_avg),
        TEST(lambda dy: dy is not None and dy >= _MIN_YIELD),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def utilities_buy(self, ticker, pe, peer_avg, dy):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.BUY,
            reason=(
                f"Utilities: P/E {pe:.1f}x below peer avg {peer_avg:.1f}x "
                f"(TNB, Ranhill, YTL Power, Malakoff) with dividend yield {dy:.1f}% "
                f">= {_MIN_YIELD:.1f}% income threshold — strong income BUY"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.UTILITIES,
              pe_ratio=MATCH.pe, dividend_yield=MATCH.dy),
        PeerBenchmark(sector=Sector.UTILITIES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        MacroData(opr=MATCH.opr),
        TEST(lambda pe, peer_avg: pe is not None and pe < peer_avg),
        TEST(lambda dy: dy is not None and dy >= _MIN_YIELD),
        TEST(lambda opr: opr is not None and opr <= 3.0),   # low OPR = cheap financing
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=21,   # slightly higher — OPR context strengthens conviction
    )
    def utilities_buy_low_opr(self, ticker, pe, peer_avg, dy, opr):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.BUY,
            reason=(
                f"Utilities: P/E {pe:.1f}x below peer avg {peer_avg:.1f}x, "
                f"yield {dy:.1f}%, and OPR at {opr:.2f}% reduces financing cost "
                f"on infrastructure debt — favourable macro tailwind for capital-heavy operators"
            ),
        ))

    # ── WATCH ─────────────────────────────────────────────────────────────────

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.UTILITIES,
              pe_ratio=MATCH.pe, dividend_yield=MATCH.dy),
        PeerBenchmark(sector=Sector.UTILITIES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and peer_avg <= pe <= peer_avg * mult),
        TEST(lambda dy: dy is not None and dy >= _BROKEN_YIELD),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def utilities_watch(self, ticker, pe, peer_avg, mult, dy):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason=(
                f"Utilities: P/E {pe:.1f}x within fair-value band "
                f"({peer_avg:.1f}x–{peer_avg * mult:.1f}x), yield {dy:.1f}% — "
                f"monitor OPR direction, coal/fuel cost trend, and tariff revision news"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.UTILITIES,
              pe_ratio=MATCH.pe, dividend_yield=MATCH.dy),
        PeerBenchmark(sector=Sector.UTILITIES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        MacroData(opr=MATCH.opr),
        TEST(lambda pe, peer_avg, mult: pe is not None and peer_avg <= pe <= peer_avg * mult),
        TEST(lambda dy: dy is not None and dy >= _BROKEN_YIELD),
        TEST(lambda opr: opr is not None and opr > 3.0),   # rising OPR = cost headwind
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=21,
    )
    def utilities_watch_high_opr(self, ticker, pe, peer_avg, mult, dy, opr):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason=(
                f"Utilities: P/E {pe:.1f}x at fair value, yield {dy:.1f}% — "
                f"but OPR at {opr:.2f}% raises financing costs on infrastructure debt "
                f"and makes yield less competitive vs fixed income; hold, reassess at OPR peak"
            ),
        ))

    # ── AVOID ─────────────────────────────────────────────────────────────────

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.UTILITIES,
              pe_ratio=MATCH.pe, dividend_yield=MATCH.dy),
        PeerBenchmark(sector=Sector.UTILITIES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda dy: dy is not None and dy < _BROKEN_YIELD),
        TEST(lambda pe, peer_avg, mult: pe is not None and pe > peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def utilities_avoid_broken_yield_overvalued(self, ticker, pe, peer_avg, mult, dy):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.AVOID,
            reason=(
                f"Utilities: income thesis broken — yield {dy:.1f}% below {_BROKEN_YIELD:.1f}% "
                f"floor AND P/E {pe:.1f}x exceeds peer avg +{round((mult-1)*100):.0f}% "
                f"({peer_avg * mult:.1f}x); no valuation or income support vs TNB, Malakoff"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.UTILITIES,
              pe_ratio=MATCH.pe, dividend_yield=MATCH.dy),
        PeerBenchmark(sector=Sector.UTILITIES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and pe > peer_avg * mult),
        TEST(lambda dy: dy is not None and dy >= _BROKEN_YIELD),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def utilities_avoid_overvalued(self, ticker, pe, peer_avg, mult, dy):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.AVOID,
            reason=(
                f"Utilities: P/E {pe:.1f}x exceeds peer avg +{round((mult-1)*100):.0f}% "
                f"({peer_avg * mult:.1f}x) — overvalued vs TNB, Ranhill, YTL Power, Malakoff; "
                f"yield {dy:.1f}% does not compensate for valuation risk"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.UTILITIES,
              pe_ratio=MATCH.pe, dividend_yield=MATCH.dy),
        PeerBenchmark(sector=Sector.UTILITIES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda dy: dy is not None and dy < _BROKEN_YIELD),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=18,
    )
    def utilities_avoid_low_yield(self, ticker, pe, peer_avg, mult, dy):
        # OR logic: yield < 3.0% alone triggers AVOID regardless of P/E level.
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.AVOID,
            reason=(
                f"Utilities: dividend yield {dy:.1f}% below {_BROKEN_YIELD:.1f}% income floor "
                f"— income thesis broken; yield alone triggers AVOID per sector rules "
                f"(P/E {pe:.1f}x vs peer avg {peer_avg:.1f}x)"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.UTILITIES,
              pe_ratio=MATCH.pe, dividend_yield=MATCH.dy),
        PeerBenchmark(sector=Sector.UTILITIES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg: pe is not None and pe < peer_avg),
        TEST(lambda dy: dy is not None and _BROKEN_YIELD <= dy < _MIN_YIELD),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def utilities_watch_undervalued_mid_yield(self, ticker, pe, peer_avg, mult, dy):
        # Undervalued P/E but yield below BUY threshold (3.0–4.0%) → WATCH not BUY.
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason=(
                f"Utilities: P/E {pe:.1f}x below peer avg {peer_avg:.1f}x (cheap) "
                f"but dividend yield {dy:.1f}% below {_MIN_YIELD:.1f}% BUY threshold "
                f"— monitor yield recovery before entering"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.UTILITIES,
              pe_ratio=None, dividend_yield=MATCH.dy),
        PeerBenchmark(sector=Sector.UTILITIES, metric="pe_ratio"),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def utilities_no_pe_data(self, ticker, dy):
        dy_note = f"{dy:.1f}%" if dy is not None else "unavailable"
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason=f"Utilities: P/E data unavailable (yield: {dy_note}) — manual verification of earnings stability and tariff exposure required",
        ))