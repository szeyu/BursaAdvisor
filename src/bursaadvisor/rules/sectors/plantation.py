"""
Plantation sector rules — salience=20.
Evaluates palm oil and agricultural companies on P/E ratio vs sector peer average.
Focus on commodity price exposure (CPO) and currency risk (USD/MYR).
"""
from experta import Rule, MATCH, NOT, TEST
from ...facts import Stock, Recommendation, FundamentalPass, PeerBenchmark, MacroData
from ...enums import Sector, Verdict
from ...data.config_loader import load_sector_config

_cfg = load_sector_config("plantation")
_AVOID_MULT: float = _cfg["avoid_multiplier"]


class PlantationRules:

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.PLANTATION, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.PLANTATION, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg: pe is not None and pe < peer_avg),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def plantation_buy(self, ticker, pe, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.BUY,
            reason=f"Plantation: P/E {pe:.1f}x below sector median {peer_avg:.1f}x (SD Guthrie, KLK, Genting Plantations, United Plantations) — attractive on commodity cyclical recovery",
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.PLANTATION, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.PLANTATION, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and peer_avg <= pe <= peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def plantation_watch(self, ticker, pe, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason=f"Plantation: P/E {pe:.1f}x within sector range ({peer_avg:.1f}x–{peer_avg * mult:.1f}x; SD Guthrie, KLK, Genting Plantations, United Plantations) — monitor CPO price, yield & USD/MYR",
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.PLANTATION, pe_ratio=MATCH.pe),
        PeerBenchmark(sector=Sector.PLANTATION, metric="pe_ratio",
                      value=MATCH.peer_avg, avoid_multiplier=MATCH.mult),
        TEST(lambda pe, peer_avg, mult: pe is not None and pe > peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def plantation_avoid(self, ticker, pe, peer_avg, mult):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.AVOID,
            reason=f"Plantation: P/E {pe:.1f}x exceeds sector median +{round((mult-1)*100):.0f}% (threshold: {peer_avg * mult:.1f}x vs SD Guthrie, KLK, Genting Plantations) — valuation premium unjustified by commodity outlook",
        ))

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.PLANTATION, pe_ratio=None),
        PeerBenchmark(sector=Sector.PLANTATION, metric="pe_ratio"),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def plantation_no_pe_data(self, ticker):
        self.declare(Recommendation(
            ticker=ticker,
            verdict=Verdict.WATCH,
            reason="Plantation: P/E data unavailable — assess gross margin, CPO spot price, and replanting capex manually",
        ))
