"""
Technology sector rules — salience=20.
Evaluates tech/telecom companies on P/E ratio vs sector peer average.
Focus on growth, export exposure, and foreign exchange risk.
Template pattern: copy from banking.py, adapt 6 key things (see SECTOR_GUIDE.md).
"""
from experta import Rule, MATCH, NOT, TEST
from ...facts import Stock, Recommendation, FundamentalPass, PeerBenchmark, MacroData
from ...enums import Sector, Verdict
from ...data.config_loader import load_sector_config

_cfg = load_sector_config("technology")
_AVOID_MULT: float = _cfg["avoid_multiplier"]


class TechnologyRules:

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.TECHNOLOGY, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.TECHNOLOGY, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg: pe is not None and pe < peer_avg),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def tech_buy(self, ticker, pe, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.BUY,
            reason=f"Technology: P/E {pe:.1f}x below sector avg {peer_avg:.1f}x — growth potential at valuation discount",
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.TECHNOLOGY, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.TECHNOLOGY, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and peer_avg <= pe <= peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def tech_watch(self, ticker, pe, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason=f"Technology: P/E {pe:.1f}x within peer range ({peer_avg:.1f}x–{peer_avg * mult:.1f}x) — monitor revenue growth & USD/MYR exposure",
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.TECHNOLOGY, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.TECHNOLOGY, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and pe > peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def tech_avoid(self, ticker, pe, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.AVOID,
            reason=f"Technology: P/E {pe:.1f}x exceeds sector avg +{round((mult-1)*100):.0f}% ({peer_avg * mult:.1f}x) — valuation stretched relative to peers",
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.TECHNOLOGY, pe_ratio=None),
        PeerBenchmark(sector=Sector.TECHNOLOGY, metric="pe_ratio"),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def tech_no_pe_data(self, ticker):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason="Technology: P/E data unavailable — check revenue growth, FCF, and export revenue exposure manually",
        ))
