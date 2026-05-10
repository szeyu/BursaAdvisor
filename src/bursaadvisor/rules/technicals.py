from experta import Rule, MATCH, NOT, AS, TEST
from ..facts import Stock, Recommendation
from ..enums import Verdict
from ..constants import RSI_OVERBOUGHT, RSI_OVERSOLD


class TechnicalRules:

    @Rule(
        AS.rec << Recommendation(ticker=MATCH.ticker, verdict=Verdict.BUY),
        Stock(ticker=MATCH.ticker, rsi=MATCH.rsi),
        TEST(lambda rsi: rsi is not None and rsi >= RSI_OVERBOUGHT),
        salience=10,
    )
    def downgrade_overbought(self, rec, ticker, rsi):
        self.modify(rec, verdict=Verdict.WATCH, reason=rec["reason"] + f" | RSI {rsi:.0f} overbought")

    @Rule(
        AS.rec << Recommendation(ticker=MATCH.ticker, verdict=Verdict.WATCH),
        Stock(ticker=MATCH.ticker, rsi=MATCH.rsi, golden_cross=True),
        TEST(lambda rsi: rsi is not None and rsi <= RSI_OVERSOLD),
        salience=10,
    )
    def upgrade_oversold_cross(self, rec, ticker, rsi):
        self.modify(rec, verdict=Verdict.BUY, reason=rec["reason"] + f" | RSI {rsi:.0f} oversold + golden cross")

    @Rule(
        Stock(ticker=MATCH.ticker),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=0,
    )
    def fallback_watch(self, ticker):
        self.declare(Recommendation(ticker=ticker, verdict=Verdict.WATCH,
                                    reason="Insufficient data for a confident verdict"))
