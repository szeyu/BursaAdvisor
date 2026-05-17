"""
Gloves sector rules — salience=20.
Primary metric : P/E ratio vs peer average
Peer tickers   : Top Glove (7113.KL), Hartalega (5168.KL),
                 Kossan (0072.KL), Supermax (7229.KL)
Key macro      : USD/MYR (export revenue), nitrile/raw material cost,
                 global supply glut vs shortage cycle
"""
from experta import Rule, MATCH, NOT, TEST
from ...facts import Stock, Recommendation, FundamentalPass, PeerBenchmark, MacroData
from ...enums import Sector, Verdict
from ...data.config_loader import load_sector_config


_cfg = load_sector_config("gloves")
_AVOID_MULT: float = _cfg["avoid_multiplier"]


class GlovesRules:

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.GLOVES, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.GLOVES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        MacroData(usd_myr=MATCH.rate),
        TEST(lambda pe, peer_avg: pe is not None and pe < peer_avg),
        TEST(lambda rate: rate is not None and rate >= 4.40),   # strong USD favourable
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def gloves_buy_undervalued_strong_usd(self, ticker, pe, peer_avg, rate):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.BUY,
            reason=(
                f"Gloves: P/E {pe:.1f}x below peer avg {peer_avg:.1f}x "
                f"(Top Glove, Hartalega, Kossan, Supermax) with favourable "
                f"USD/MYR at {rate:.2f} — strong USD boosts export revenue in ringgit terms"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.GLOVES, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.GLOVES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg: pe is not None and pe < peer_avg),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,   # fires only if USD rule above did not match
    )
    def gloves_buy_undervalued(self, ticker, pe, peer_avg):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.BUY,
            reason=(
                f"Gloves: P/E {pe:.1f}x below peer avg {peer_avg:.1f}x — "
                f"undervalued relative to Top Glove, Hartalega, Kossan, Supermax; "
                f"verify USD/MYR trend before entry"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.GLOVES, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.GLOVES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and peer_avg <= pe <= peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def gloves_watch(self, ticker, pe, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason=(
                f"Gloves: P/E {pe:.1f}x within fair-value band "
                f"({peer_avg:.1f}x–{peer_avg * mult:.1f}x; Top Glove, Hartalega, Kossan, Supermax) — "
                f"monitor USD/MYR direction, nitrile cost trend, and ASP recovery signals"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.GLOVES, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.GLOVES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        MacroData(usd_myr=MATCH.rate),
        TEST(lambda pe, peer_avg, mult: pe is not None and pe > peer_avg * mult),
        TEST(lambda rate: rate is not None and rate < 4.40),   # weak USD compounds risk
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def gloves_avoid_overvalued_weak_usd(self, ticker, pe, peer_avg, mult, rate):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.AVOID,
            reason=(
                f"Gloves: P/E {pe:.1f}x exceeds peer avg +{round((mult-1)*100):.0f}% "
                f"({peer_avg * mult:.1f}x) AND USD/MYR at {rate:.2f} is weak — "
                f"export revenue headwind compounds overvaluation; double risk"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.GLOVES, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.GLOVES, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and pe > peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def gloves_avoid_overvalued(self, ticker, pe, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.AVOID,
            reason=(
                f"Gloves: P/E {pe:.1f}x exceeds peer avg +{round((mult-1)*100):.0f}% "
                f"({peer_avg * mult:.1f}x) — post-cycle premium not justified; "
                f"verify USD/MYR and ASP before re-entering"
            ),
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.GLOVES, pe_ratio=None),
        PeerBenchmark(sector=Sector.GLOVES, metric="pe_ratio"),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def gloves_no_pe_data(self, ticker):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason="Gloves: P/E data unavailable — check if company is loss-making post-cycle; manual verification required",
        ))