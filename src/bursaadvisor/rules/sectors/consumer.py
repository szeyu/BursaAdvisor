"""
Consumer/Retail sector rules — salience=20.
Evaluates consumer and retail companies on P/E ratio vs sector peer average.
Focus on revenue growth, margin sustainability, and consumer discretionary exposure.
"""
from experta import Rule, MATCH, NOT, TEST
from ...facts import Stock, Recommendation, FundamentalPass, PeerBenchmark, MacroData
from ...enums import Sector, Verdict
from ...data.config_loader import load_sector_config

_cfg = load_sector_config("consumer")
_AVOID_MULT: float = _cfg["avoid_multiplier"]


class ConsumerRules:

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.CONSUMER, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.CONSUMER, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg: pe is not None and pe < peer_avg),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def consumer_buy(self, ticker, pe, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.BUY,
            reason=f"Consumer: P/E {pe:.1f}x below sector avg {peer_avg:.1f}x — attractive entry for resilient retailing",
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.CONSUMER, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.CONSUMER, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and peer_avg <= pe <= peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def consumer_watch(self, ticker, pe, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason=f"Consumer: P/E {pe:.1f}x within peer range ({peer_avg:.1f}x–{peer_avg * mult:.1f}x) — monitor same-store sales & operating margins",
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.CONSUMER, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.CONSUMER, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and pe > peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def consumer_avoid(self, ticker, pe, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.AVOID,
            reason=f"Consumer: P/E {pe:.1f}x exceeds sector avg +{round((mult-1)*100):.0f}% ({peer_avg * mult:.1f}x) — premium valuation with margin pressure risk",
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.CONSUMER, pe_ratio=None),
        PeerBenchmark(sector=Sector.CONSUMER, metric="pe_ratio"),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def consumer_no_pe_data(self, ticker):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason="Consumer: P/E data unavailable — check revenue growth trajectory and operating margin trends manually",
        ))
