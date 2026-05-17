from experta import Rule, MATCH, NOT, TEST
from ..facts import Stock, Recommendation
from ..enums import Verdict, Sector
from ..constants import (
    HARD_MAX_DE_RATIO,
    HARD_MIN_CURRENT_RATIO,
    HARD_MAX_CONSEC_LOSSES,
    HARD_MIN_MARKET_CAP_B,
    EXEMPT_FROM_DE_CR,
)


class HardStopRules:

    @Rule(
        Stock(is_pn17=True, ticker=MATCH.ticker),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=100,
    )
    def avoid_pn17(self, ticker):
        self.declare(Recommendation(ticker=ticker, verdict=Verdict.AVOID,
                                    reason="PN17 listing — financial distress / delisting risk"))

    @Rule(
        Stock(auditor_qualified=True, ticker=MATCH.ticker),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=100,
    )
    def avoid_qualified_audit(self, ticker):
        self.declare(Recommendation(ticker=ticker, verdict=Verdict.AVOID,
                                    reason="Auditor flagged concerns in financials (qualified/adverse opinion) — reliability risk"))

    @Rule(
        Stock(ticker=MATCH.ticker, consecutive_losses=MATCH.losses),
        TEST(lambda losses: losses >= HARD_MAX_CONSEC_LOSSES),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=100,
    )
    def avoid_consecutive_losses(self, ticker, losses):
        self.declare(Recommendation(ticker=ticker, verdict=Verdict.AVOID,
                                    reason=f"{losses} consecutive quarterly losses — deteriorating earnings"))

    @Rule(
        Stock(ticker=MATCH.ticker, debt_to_equity=MATCH.de, sector=MATCH.sector),
        TEST(lambda de, sector: de is not None and de > HARD_MAX_DE_RATIO and sector not in EXEMPT_FROM_DE_CR),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=100,
    )
    def avoid_high_debt(self, ticker, de, sector):
        self.declare(Recommendation(ticker=ticker, verdict=Verdict.AVOID,
                                    reason=f"D/E ratio {de:.2f}x exceeds {HARD_MAX_DE_RATIO}x — insolvency risk"))

    @Rule(
        Stock(ticker=MATCH.ticker, current_ratio=MATCH.cr, sector=MATCH.sector),
        TEST(lambda cr, sector: cr is not None and cr < HARD_MIN_CURRENT_RATIO and sector not in EXEMPT_FROM_DE_CR),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=100,
    )
    def avoid_liquidity_risk(self, ticker, cr, sector):
        self.declare(Recommendation(ticker=ticker, verdict=Verdict.AVOID,
                                    reason=f"Current ratio {cr:.2f}x below {HARD_MIN_CURRENT_RATIO}x — liquidity crisis"))

    @Rule(
        Stock(ticker=MATCH.ticker, market_cap_b=MATCH.mc),
        TEST(lambda mc: mc is not None and mc < HARD_MIN_MARKET_CAP_B),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=100,
    )
    def avoid_small_cap(self, ticker, mc):
        self.declare(Recommendation(ticker=ticker, verdict=Verdict.AVOID,
                                    reason=f"Market cap RM{mc:.2f}B below RM{HARD_MIN_MARKET_CAP_B * 1000:.0f}M floor — illiquidity risk"))
