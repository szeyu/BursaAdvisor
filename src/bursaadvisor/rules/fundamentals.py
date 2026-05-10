from experta import Rule, MATCH, NOT, TEST
from ..facts import Stock, InvestorProfile, Recommendation, FundamentalPass, IncomeShiftFlag
from ..enums import Verdict
from ..constants import RISK_THRESHOLDS, INCOME_SHIFT_MIN_DIV


class FundamentalRules:

    @Rule(
        InvestorProfile(risk_tolerance=MATCH.risk),
        Stock(
            ticker=MATCH.ticker,
            pe_ratio=MATCH.pe,
            dividend_yield=MATCH.div,
            payout_ratio=MATCH.payout,
        ),
        TEST(lambda risk, pe, div, payout: (
            pe is not None and div is not None
            and pe <= RISK_THRESHOLDS[risk]["max_pe"]
            and div >= RISK_THRESHOLDS[risk]["min_div"]
            and (payout is None or payout <= RISK_THRESHOLDS[risk]["max_payout"])
        )),
        NOT(IncomeShiftFlag()),
        NOT(FundamentalPass(ticker=MATCH.ticker)),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=50,
    )
    def fundamental_pass_normal(self, ticker, risk, pe, div, payout):
        t = RISK_THRESHOLDS[risk]
        note = f"P/E {pe:.1f}x ≤ {t['max_pe']} | Div {div:.1f}% ≥ {t['min_div']}%"
        if payout is not None:
            note += f" | Payout {payout:.0f}% ≤ {t['max_payout']}%"
        self.declare(FundamentalPass(ticker=ticker, note=note))

    @Rule(
        InvestorProfile(risk_tolerance=MATCH.risk),
        Stock(
            ticker=MATCH.ticker,
            dividend_yield=MATCH.div,
            payout_ratio=MATCH.payout,
        ),
        IncomeShiftFlag(),
        TEST(lambda div, payout, risk: (
            div is not None and div >= INCOME_SHIFT_MIN_DIV
            and (payout is None or payout <= RISK_THRESHOLDS[risk]["max_payout"])
        )),
        NOT(FundamentalPass(ticker=MATCH.ticker)),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=50,
    )
    def fundamental_pass_income_shift(self, ticker, risk, div, payout):
        note = f"Income investor (age ≥45): Div {div:.1f}% ≥ {INCOME_SHIFT_MIN_DIV}%"
        self.declare(FundamentalPass(ticker=ticker, note=note))

    @Rule(
        InvestorProfile(risk_tolerance=MATCH.risk),
        Stock(
            ticker=MATCH.ticker,
            pe_ratio=MATCH.pe,
            dividend_yield=MATCH.div,
            payout_ratio=MATCH.payout,
        ),
        NOT(FundamentalPass(ticker=MATCH.ticker)),
        NOT(Recommendation(ticker=MATCH.ticker)),
        salience=1,
    )
    def fundamental_blocked_diagnostic(self, risk, ticker, pe, div, payout):
        """Fires when fundamental gate was not passed — produces a diagnostic WATCH reason."""
        t = RISK_THRESHOLDS[risk]
        issues = []
        if pe is None:
            issues.append("P/E ratio not available (cannot assess valuation)")
        elif pe > t["max_pe"]:
            issues.append(
                f"P/E ratio {pe:.1f}x is too high for {risk} profile (limit: {t['max_pe']}x). "
                f"P/E measures how expensive the stock is relative to its earnings — higher = pricier."
            )
        if div is None:
            issues.append("dividend yield not available")
        elif div < t["min_div"]:
            issues.append(
                f"dividend yield {div:.1f}% is too low for {risk} profile (minimum: {t['min_div']}%). "
                f"Dividend yield = annual dividend ÷ share price — higher means more regular income."
            )
        if payout is not None and payout > t["max_payout"]:
            issues.append(
                f"dividend payout ratio {payout:.0f}% exceeds {t['max_payout']}% limit. "
                f"Payout ratio = % of profit paid as dividends — too high means little profit left to reinvest or absorb losses."
            )
        reason = "Did not pass {risk} investor filter — ".format(risk=risk) + ("; ".join(issues) if issues else "financial data incomplete")
        self.declare(Recommendation(ticker=ticker, verdict=Verdict.WATCH, reason=reason))
