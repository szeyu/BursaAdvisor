"""Construction sector rules — salience=20.

Uses only filled knowledge from the elicitation sheet:
- Main valuation metric: P/E.
- Construction-specific knowledge: order book.
- Macro drivers: OPR, inflation, labour/material cost.

Blank PDF fields such as fair value range, explicit undervalued/overvalued
thresholds, and order-book cutoffs are not converted into invented thresholds.
"""

from experta import Rule, MATCH, NOT, TEST

from ...facts import Stock, Recommendation, FundamentalPass, PeerBenchmark, MacroData
from ...enums import Sector, Verdict
from ...data.config_loader import load_sector_config

_cfg = load_sector_config("construction")
_AVOID_MULT: float = _cfg["avoid_multiplier"]


def _opr_note(opr: float | None) -> str:
    if opr is None:
        return " | OPR unavailable — project-financing risk should be checked manually"
    return f" | OPR {opr:.2f}% affects project financing and borrowing cost"


class ConstructionRules:
    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(
            ticker=MATCH.ticker,
            sector=Sector.CONSTRUCTION,
            pe_ratio=MATCH.pe,
            order_book_rm=MATCH.order_book,
        ),
        PeerBenchmark(
            sector=Sector.CONSTRUCTION,
            metric="pe_ratio",
            value=MATCH.peer_avg,
            avoid_multiplier=MATCH.mult,
        ),
        MacroData(opr=MATCH.opr),
        TEST(lambda pe, order_book, peer_avg: pe is not None and order_book is not None and pe < peer_avg),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def construction_buy(self, ticker, pe, order_book, peer_avg, mult, opr):
        self.declare(
            Recommendation(
                ticker=ticker,
                verdict=Verdict.BUY,
                reason=(
                    f"Construction: P/E {pe:.1f}x below peer avg {peer_avg:.1f}x (Gamuda, IJM Corp, Sunway Construction, WCT Holdings); "
                    f"order book RM{order_book:.1f}b captured for revenue visibility"
                    f"{_opr_note(opr)}"
                ),
            )
        )

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(
            ticker=MATCH.ticker,
            sector=Sector.CONSTRUCTION,
            pe_ratio=MATCH.pe,
            order_book_rm=MATCH.order_book,
        ),
        PeerBenchmark(
            sector=Sector.CONSTRUCTION,
            metric="pe_ratio",
            value=MATCH.peer_avg,
            avoid_multiplier=MATCH.mult,
        ),
        MacroData(opr=MATCH.opr),
        TEST(
            lambda pe, order_book, peer_avg, mult: (
                pe is not None
                and order_book is not None
                and peer_avg <= pe <= peer_avg * mult
            )
        ),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def construction_watch(self, ticker, pe, order_book, peer_avg, mult, opr):
        self.declare(
            Recommendation(
                ticker=ticker,
                verdict=Verdict.WATCH,
                reason=(
                    f"Construction: P/E {pe:.1f}x within peer range "
                    f"({peer_avg:.1f}x–{peer_avg * mult:.1f}x; Gamuda, IJM Corp, Sunway Construction, WCT Holdings); order book RM{order_book:.1f}b "
                    f"captured for revenue visibility — monitor OPR, material cost and labour cost"
                    f"{_opr_note(opr)}"
                ),
            )
        )

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(
            ticker=MATCH.ticker,
            sector=Sector.CONSTRUCTION,
            pe_ratio=MATCH.pe,
            order_book_rm=MATCH.order_book,
        ),
        PeerBenchmark(
            sector=Sector.CONSTRUCTION,
            metric="pe_ratio",
            value=MATCH.peer_avg,
            avoid_multiplier=MATCH.mult,
        ),
        MacroData(opr=MATCH.opr),
        TEST(lambda pe, peer_avg, mult: pe is not None and pe > peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def construction_avoid(self, ticker, pe, order_book, peer_avg, mult, opr):
        # Overvalued P/E alone triggers AVOID — order book not required per proposal.
        ob_note = f"; order book RM{order_book:.1f}b" if order_book is not None else "; order book unavailable"
        self.declare(
            Recommendation(
                ticker=ticker,
                verdict=Verdict.AVOID,
                reason=(
                    f"Construction: P/E {pe:.1f}x exceeds peer avg by more than {round((mult - 1) * 100):.0f}% "
                    f"(threshold: {peer_avg * mult:.1f}x vs Gamuda, IJM Corp, Sunway Construction, WCT Holdings)"
                    f"{ob_note}"
                    f"{_opr_note(opr)}"
                ),
            )
        )

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(
            ticker=MATCH.ticker,
            sector=Sector.CONSTRUCTION,
            pe_ratio=None,
        ),
        PeerBenchmark(sector=Sector.CONSTRUCTION, metric="pe_ratio"),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def construction_no_pe_data(self, ticker):
        self.declare(
            Recommendation(
                ticker=ticker,
                verdict=Verdict.WATCH,
                reason=(
                    "Construction: P/E unavailable — manual verification required "
                    "before assessing valuation and revenue visibility"
                ),
            )
        )