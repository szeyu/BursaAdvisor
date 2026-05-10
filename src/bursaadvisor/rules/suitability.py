"""
Investor-stock suitability rules — salience=15.

Runs after sector rules (20) have set initial verdicts, before technical signals (10).
Adjusts verdicts based on investor profile fit, not just stock fundamentals.
"""
from experta import Rule, MATCH, AS, TEST
from ..facts import Stock, Recommendation, ShortHorizonFlag, LowSavingsFlag
from ..enums import Verdict, Sector, VOLATILE_SECTORS


class SuitabilityRules:

    @Rule(
        ShortHorizonFlag(),
        AS.rec << Recommendation(ticker=MATCH.ticker, verdict=Verdict.BUY),
        Stock(ticker=MATCH.ticker, sector=MATCH.sector),
        TEST(lambda sector: sector in VOLATILE_SECTORS),
        salience=15,
    )
    def downgrade_short_horizon_volatile(self, rec, ticker, sector):
        """BUY in volatile sector + short horizon → WATCH. Capital may be needed before recovery."""
        self.modify(
            rec,
            verdict=Verdict.WATCH,
            reason=rec["reason"] + f" | Short horizon (<3yr) — {sector} is cyclical/volatile",
        )

    @Rule(
        LowSavingsFlag(),
        AS.rec << Recommendation(ticker=MATCH.ticker, verdict=Verdict.BUY),
        Stock(ticker=MATCH.ticker, sector=MATCH.sector),
        TEST(lambda sector: sector in VOLATILE_SECTORS),
        salience=15,
    )
    def note_low_savings_volatile(self, rec, ticker, sector):
        """BUY in volatile sector + low savings → WATCH. Insufficient buffer for drawdown risk."""
        self.modify(
            rec,
            verdict=Verdict.WATCH,
            reason=rec["reason"] + f" | Low savings buffer — reduce exposure to {sector} volatility",
        )
