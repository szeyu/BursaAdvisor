from experta import Rule, MATCH, NOT, TEST
from ..facts import InvestorProfile, IncomeShiftFlag, LowSavingsFlag, ShortHorizonFlag


class ProfileRules:

    @Rule(
        InvestorProfile(age=MATCH.age),
        TEST(lambda age: age >= 45),
        NOT(IncomeShiftFlag()),
        salience=70,
    )
    def set_income_shift_by_age(self, age):
        """Age >= 45 → income-oriented evaluation path."""
        self.declare(IncomeShiftFlag())

    @Rule(
        InvestorProfile(income_preference=True),
        NOT(IncomeShiftFlag()),
        salience=70,
    )
    def set_income_shift_by_preference(self):
        """Investor explicitly prefers dividends → same income-oriented path as age >= 45."""
        self.declare(IncomeShiftFlag())

    @Rule(
        InvestorProfile(savings_ratio=MATCH.ratio),
        TEST(lambda ratio: ratio < 0.20),
        NOT(LowSavingsFlag()),
        salience=70,
    )
    def flag_low_savings(self, ratio):
        self.declare(LowSavingsFlag())

    @Rule(
        InvestorProfile(investment_horizon=MATCH.horizon),
        TEST(lambda horizon: horizon < 3),
        NOT(ShortHorizonFlag()),
        salience=70,
    )
    def flag_short_horizon(self, horizon):
        """Horizon < 3 years → equities are risky; volatile sectors will be downgraded."""
        self.declare(ShortHorizonFlag())
