"""
Healthcare sector rules — salience=20.
Primary metric : P/E ratio vs peer average
Peer tickers   : IHH Healthcare (5225.KL), KPJ Healthcare (5878.KL),
                 Sunway Medical (via Sunway 5211.KL)
Secondary check: occupancy_rate (Stock.occupancy_rate field, % e.g. 75.0)
Key macro      : USD/MYR (medical tourism revenue), OPR (hospital capex financing)
"""
from experta import Rule, MATCH, NOT, TEST
from ...facts import Stock, Recommendation, FundamentalPass, PeerBenchmark, MacroData
from ...enums import Sector, Verdict
from ...data.config_loader import load_sector_config

_cfg = load_sector_config("healthcare")
_AVOID_MULT: float = _cfg["avoid_multiplier"]
_MIN_OCCUPANCY: float = _cfg.get("min_occupancy_rate", 65.0)


class HealthcareRules:

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.HEALTHCARE,
              pe_ratio=MATCH.pe, occupancy_rate=MATCH.occ),
        PeerBenchmark(sector=Sector.HEALTHCARE, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg: pe is not None and pe < peer_avg),
        TEST(lambda occ: occ is not None and occ >= _MIN_OCCUPANCY),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def healthcare_buy(self, ticker, pe, peer_avg, occ):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.BUY,
            reason=(
                f"Healthcare: P/E {pe:.1f}x below peer avg {peer_avg:.1f}x "
                f"(IHH, KPJ, Sunway Medical) with healthy occupancy rate of {occ:.0f}% "
                f"— undervalued with strong patient volume supporting earnings"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.HEALTHCARE,
              pe_ratio=MATCH.pe, occupancy_rate=None),
        PeerBenchmark(sector=Sector.HEALTHCARE, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg: pe is not None and pe < peer_avg),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,   # fires only when occupancy data not available
    )
    def healthcare_buy_no_occupancy(self, ticker, pe, peer_avg):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.BUY,
            reason=(
                f"Healthcare: P/E {pe:.1f}x below peer avg {peer_avg:.1f}x — "
                f"undervalued vs IHH, KPJ, Sunway Medical; "
                f"occupancy data unavailable — verify bed utilisation before entry"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.HEALTHCARE,
              pe_ratio=MATCH.pe, occupancy_rate=MATCH.occ),
        PeerBenchmark(sector=Sector.HEALTHCARE, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and peer_avg <= pe <= peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def healthcare_watch(self, ticker, pe, peer_avg, mult, occ):
        occ_note = (
            f"; occupancy at {occ:.0f}% — {'solid' if occ is not None and occ >= _MIN_OCCUPANCY else 'below threshold, monitor closely'}"
            if occ is not None else "; occupancy data unavailable"
        )
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason=(
                f"Healthcare: P/E {pe:.1f}x within fair-value band "
                f"({peer_avg:.1f}x–{peer_avg * mult:.1f}x)"
                f"{occ_note} — monitor medical tourism recovery and OPR impact on capex"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.HEALTHCARE,
              pe_ratio=MATCH.pe, occupancy_rate=MATCH.occ),
        PeerBenchmark(sector=Sector.HEALTHCARE, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and pe > peer_avg * mult),
        TEST(lambda occ: occ is not None and occ < _MIN_OCCUPANCY),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def healthcare_avoid_overvalued_low_occupancy(self, ticker, pe, peer_avg, mult, occ):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.AVOID,
            reason=(
                f"Healthcare: P/E {pe:.1f}x exceeds peer avg +{round((mult-1)*100):.0f}% "
                f"({peer_avg * mult:.1f}x) AND occupancy rate {occ:.0f}% is below "
                f"{_MIN_OCCUPANCY:.0f}% — premium valuation not supported by utilisation"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.HEALTHCARE, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.HEALTHCARE, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and pe > peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def healthcare_watch_overvalued_good_occupancy(self, ticker, pe, peer_avg, mult):
        # Fires when pe > peer_avg * mult but occupancy is not confirmed below threshold.
        # Per proposal: AVOID requires BOTH overvalued P/E AND low occupancy (<65%).
        # If occupancy is good (>=65%) or unavailable, verdict is WATCH — overvalued but operationally sound.
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason=(
                f"Healthcare: P/E {pe:.1f}x exceeds peer avg +{round((mult-1)*100):.0f}% "
                f"({peer_avg * mult:.1f}x) but occupancy is acceptable — overvalued vs "
                f"IHH, KPJ, Sunway Medical; hold position, do not enter at this price"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.HEALTHCARE, pe_ratio=None),
        PeerBenchmark(sector=Sector.HEALTHCARE, metric="pe_ratio"),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def healthcare_no_pe_data(self, ticker):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason="Healthcare: P/E data unavailable — manual verification of earnings and occupancy required",
        ))