"""REITs sector rules — salience=20.

Uses only filled knowledge from the elicitation sheet:
- Main valuation focus: distribution/dividend yield.
- Debt/borrowing sensitivity: OPR affects REIT borrowing cost.
- Red flag noted in PDF: higher OPR is negative for REITs.

Blank PDF fields such as fair value range and explicit undervalued/overvalued
thresholds are not converted into extra hardcoded thresholds.
"""

from experta import Rule, MATCH, NOT, TEST

from ...facts import Stock, Recommendation, PeerBenchmark, MacroData
from ...enums import Sector, Verdict
from ...data.config_loader import load_sector_config

_cfg = load_sector_config("reits")
_AVOID_MULT: float = _cfg["avoid_multiplier"]


def _opr_note(opr: float | None) -> str:
    if opr is None:
        return " | OPR unavailable — borrowing-cost risk should be checked manually"
    return f" | OPR {opr:.2f}% affects REIT borrowing/refinancing cost"


class ReitsRules:
    @Rule(
        Stock(ticker=MATCH.ticker, sector=Sector.REITS, distribution_yield=MATCH.dy),
        PeerBenchmark(
            sector=Sector.REITS,
            metric="distribution_yield",
            value=MATCH.peer_avg,
            avoid_multiplier=MATCH.mult,
        ),
        MacroData(opr=MATCH.opr),
        TEST(lambda dy, peer_avg: dy is not None and dy >= peer_avg),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def reits_buy(self, ticker, dy, peer_avg, mult, opr):
        self.declare(
            Recommendation(
                ticker=ticker,
                verdict=Verdict.BUY,
                reason=(
                    f"REITs: distribution yield {dy:.1f}% meets/exceeds peer benchmark "
                    f"{peer_avg:.1f}% (KLCC REIT, IGB REIT, Sunway REIT, Pavilion REIT, Axis REIT)"
                    f"{_opr_note(opr)}"
                ),
            )
        )

    @Rule(
        Stock(ticker=MATCH.ticker, sector=Sector.REITS, distribution_yield=MATCH.dy),
        PeerBenchmark(
            sector=Sector.REITS,
            metric="distribution_yield",
            value=MATCH.peer_avg,
            avoid_multiplier=MATCH.mult,
        ),
        MacroData(opr=MATCH.opr),
        TEST(lambda dy, peer_avg, mult: dy is not None and peer_avg / mult <= dy < peer_avg),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def reits_watch(self, ticker, dy, peer_avg, mult, opr):
        self.declare(
            Recommendation(
                ticker=ticker,
                verdict=Verdict.WATCH,
                reason=(
                    f"REITs: distribution yield {dy:.1f}% is below peer benchmark "
                    f"{peer_avg:.1f}% (KLCC REIT, IGB REIT, Sunway REIT, Pavilion REIT, Axis REIT) but still within peer range"
                    f"{_opr_note(opr)}"
                ),
            )
        )

    @Rule(
        Stock(ticker=MATCH.ticker, sector=Sector.REITS, distribution_yield=MATCH.dy),
        PeerBenchmark(
            sector=Sector.REITS,
            metric="distribution_yield",
            value=MATCH.peer_avg,
            avoid_multiplier=MATCH.mult,
        ),
        MacroData(opr=MATCH.opr),
        TEST(lambda dy, peer_avg, mult: dy is not None and dy < peer_avg / mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def reits_avoid(self, ticker, dy, peer_avg, mult, opr):
        self.declare(
            Recommendation(
                ticker=ticker,
                verdict=Verdict.AVOID,
                reason=(
                    f"REITs: distribution yield {dy:.1f}% is materially below peer benchmark "
                    f"{peer_avg:.1f}% (KLCC REIT, IGB REIT, Sunway REIT, Pavilion REIT, Axis REIT)"
                    f"{_opr_note(opr)}"
                ),
            )
        )

    @Rule(
        Stock(ticker=MATCH.ticker, sector=Sector.REITS, distribution_yield=None),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def reits_no_distribution_yield_data(self, ticker):
        self.declare(
            Recommendation(
                ticker=ticker,
                verdict=Verdict.WATCH,
                reason="REITs: distribution yield unavailable — manual verification required",
            )
        )