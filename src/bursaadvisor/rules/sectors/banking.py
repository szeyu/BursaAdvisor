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
            reason=(
                f"Banking: P/B {pb:.2f}x below peer avg {peer_avg:.2f}x (Maybank, CIMB, Public Bank, HLBank) "
                f"— P/B (price-to-book) measures how much you pay per RM1 of the bank's net assets; "
                f"below peer avg means undervalued relative to comparable banks"
            ),
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
            reason=(
                f"Banking: P/B {pb:.2f}x within fair-value range vs peers "
                f"({peer_avg:.2f}x–{peer_avg * mult:.2f}x; Maybank, CIMB, Public Bank, HLBank) "
                f"— fairly priced but not cheap enough to enter; monitor OPR direction, "
                f"net interest margin trend, and non-performing loan ratio before acting"
            ),
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
            reason=(
                f"Banking: P/B {pb:.2f}x exceeds peer avg by more than {round((mult-1)*100):.0f}% "
                f"(threshold: {peer_avg * mult:.2f}x vs peers Maybank, CIMB, Public Bank, HLBank) "
                f"— you are paying a significant premium over the bank's book value relative to comparable banks; "
                f"downside risk is high if earnings or loan quality deteriorate"
            ),
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
