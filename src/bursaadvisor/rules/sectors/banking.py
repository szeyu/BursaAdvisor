"""
Banking sector rules — salience=20.
Use this file as a template for your sector. Full walkthrough in SECTOR_GUIDE.md.
"""
from experta import Rule, MATCH, NOT, TEST
from ...facts import Stock, Recommendation, FundamentalPass, PeerBenchmark
from ...enums import Sector, Verdict
from ...data.config_loader import load_sector_config

_cfg = load_sector_config("banking")
_AVOID_MULT: float = _cfg["avoid_multiplier"]


class BankingRules:

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.BANKING, pb_ratio=MATCH.pb),
        PeerBenchmark(sector=Sector.BANKING, metric="pb_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pb, peer_avg: pb is not None and pb < peer_avg),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def banking_buy(self, ticker, pb, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.BUY,
            reason=f"Banking: P/B {pb:.2f}x below peer avg {peer_avg:.2f}x",
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.BANKING, pb_ratio=MATCH.pb),
        PeerBenchmark(sector=Sector.BANKING, metric="pb_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pb, peer_avg, mult: pb is not None and peer_avg <= pb <= peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def banking_watch(self, ticker, pb, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason=f"Banking: P/B {pb:.2f}x within peer range ({peer_avg:.2f}x–{peer_avg * mult:.2f}x) — monitor interest margin and loan quality",
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.BANKING, pb_ratio=MATCH.pb),
        PeerBenchmark(sector=Sector.BANKING, metric="pb_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pb, peer_avg, mult: pb is not None and pb > peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def banking_avoid(self, ticker, pb, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.AVOID,
            reason=f"Banking: P/B {pb:.2f}x exceeds peer avg +{round((mult-1)*100):.0f}% ({peer_avg * mult:.2f}x)",
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.BANKING, pb_ratio=None),
        PeerBenchmark(sector=Sector.BANKING, metric="pb_ratio"),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def banking_no_pb_data(self, ticker):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason="Banking: P/B data unavailable — manual verification required",
        ))
