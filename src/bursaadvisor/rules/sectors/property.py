"""Property sector rules — salience=20.

Uses only filled knowledge from the elicitation sheet:
- Main valuation metric: P/E.
- Macro driver: high OPR / borrowing cost.
- Secondary macro pressure: inflation / material cost.

Blank PDF fields such as fair value range and explicit undervalued/overvalued
thresholds are handled the same way as Banking: compare against peer average
instead of adding invented thresholds.
"""

from experta import Rule, MATCH, NOT, TEST

from ...facts import Stock, Recommendation, FundamentalPass, PeerBenchmark, MacroData
from ...enums import Sector, Verdict
from ...data.config_loader import load_sector_config

_cfg = load_sector_config("property")
_AVOID_MULT: float = _cfg["avoid_multiplier"]


def _opr_note(opr: float | None) -> str:
    if opr is None:
        return " | OPR unavailable — borrowing-cost risk should be checked manually"
    return f" | OPR {opr:.2f}% affects mortgage demand and developer borrowing cost"


class PropertyRules:
    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.PROPERTY, pe_ratio=MATCH.pe),
        PeerBenchmark(
            sector=Sector.PROPERTY,
            metric="pe_ratio",
            value=MATCH.peer_avg,
            avoid_multiplier=MATCH.mult,
        ),
        MacroData(opr=MATCH.opr),
        TEST(lambda pe, peer_avg: pe is not None and pe < peer_avg),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def property_buy(self, ticker, pe, peer_avg, mult, opr):
        self.declare(
            Recommendation(
                ticker=ticker,
                verdict=Verdict.BUY,
                reason=(
                    f"Property: P/E {pe:.1f}x below peer avg {peer_avg:.1f}x "
                    f"(Sime Darby Prop, IOI Properties, Eco World, SP Setia, Mah Sing) "
                    f"— stock is undervalued relative to sector peers; low P/E for a developer "
                    f"suggests the market is pricing in more earnings than the share price reflects"
                    f"{_opr_note(opr)}"
                ),
            )
        )

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.PROPERTY, pe_ratio=MATCH.pe),
        PeerBenchmark(
            sector=Sector.PROPERTY,
            metric="pe_ratio",
            value=MATCH.peer_avg,
            avoid_multiplier=MATCH.mult,
        ),
        MacroData(opr=MATCH.opr),
        TEST(lambda pe, peer_avg, mult: pe is not None and peer_avg <= pe <= peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def property_watch(self, ticker, pe, peer_avg, mult, opr):
        self.declare(
            Recommendation(
                ticker=ticker,
                verdict=Verdict.WATCH,
                reason=(
                    f"Property: P/E {pe:.1f}x within peer range "
                    f"({peer_avg:.1f}x–{peer_avg * mult:.1f}x) — monitor OPR, borrowing cost "
                    f"and material-cost inflation"
                    f"{_opr_note(opr)}"
                ),
            )
        )

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.PROPERTY, pe_ratio=MATCH.pe),
        PeerBenchmark(
            sector=Sector.PROPERTY,
            metric="pe_ratio",
            value=MATCH.peer_avg,
            avoid_multiplier=MATCH.mult,
        ),
        MacroData(opr=MATCH.opr),
        TEST(lambda pe, peer_avg, mult: pe is not None and pe > peer_avg * mult),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=20,
    )
    def property_avoid(self, ticker, pe, peer_avg, mult, opr):
        self.declare(
            Recommendation(
                ticker=ticker,
                verdict=Verdict.AVOID,
                reason=(
                    f"Property: P/E {pe:.1f}x exceeds peer avg by more than {round((mult - 1) * 100):.0f}% "
                    f"(threshold: {peer_avg * mult:.1f}x vs Sime Darby Prop, IOI Prop, Eco World, SP Setia, Mah Sing) "
                    f"— overvalued relative to sector peers; premium not justified given OPR sensitivity "
                    f"on mortgage demand and developer borrowing costs"
                    f"{_opr_note(opr)}"
                ),
            )
        )

    @Rule(
        FundamentalPass(ticker=MATCH.ticker),
        Stock(ticker=MATCH.ticker, sector=Sector.PROPERTY, pe_ratio=None),
        PeerBenchmark(sector=Sector.PROPERTY, metric="pe_ratio"),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=19,
    )
    def property_no_pe_data(self, ticker):
        self.declare(
            Recommendation(
                ticker=ticker,
                verdict=Verdict.WATCH,
                reason="Property: P/E data unavailable — manual verification required",
            )
        )