import questionary
from rich.console import Console

from ..enums import Sector, RiskTolerance

console = Console()


def _pct_validator(text: str) -> bool | str:
    try:
        v = float(text)
        return True if 0 <= v <= 100 else "Enter a value between 0 and 100"
    except ValueError:
        return "Enter a percentage (e.g. 25)"


def _float_validator(text: str) -> bool | str:
    try:
        return True if float(text) >= 0 else "Must be zero or positive"
    except ValueError:
        return "Enter a number (e.g. 5.0)"


def collect_investor_profile() -> dict:
    console.print()
    console.rule("[bold]Investor Profile[/bold]")

    age = questionary.select(
        "Your age range:",
        instruction="Investors 46+ are automatically shifted to dividend-income evaluation.",
        choices=[
            questionary.Choice("18 – 25",       value=22),
            questionary.Choice("26 – 35",       value=30),
            questionary.Choice("36 – 45",       value=40),
            questionary.Choice("46 – 55",       value=50),
            questionary.Choice("56 and above",  value=60),
        ],
        default=30,
    ).ask()

    income = questionary.select(
        "Monthly gross income (RM):",
        instruction="Gross income before EPF/SOCSO. Used to calculate your savings capacity.",
        choices=[
            questionary.Choice("Below RM 3,000",           value=2500.0),
            questionary.Choice("RM 3,000 – RM 5,000",      value=4000.0),
            questionary.Choice("RM 5,000 – RM 8,000",      value=6500.0),
            questionary.Choice("RM 8,000 – RM 12,000",     value=10000.0),
            questionary.Choice("Above RM 12,000",          value=15000.0),
        ],
        default=4000.0,
    ).ask()

    savings_ratio = questionary.select(
        "What % of your monthly income do you invest/save?",
        instruction=f"Below 20% triggers a capital buffer warning. Each option shows your RM amount at RM {income:,.0f}/month.",
        choices=[
            questionary.Choice(f"10%  — RM {income * 0.10:,.0f}/month",              value=0.10),
            questionary.Choice(f"15%  — RM {income * 0.15:,.0f}/month",              value=0.15),
            questionary.Choice(f"20%  — RM {income * 0.20:,.0f}/month  (benchmark)", value=0.20),
            questionary.Choice(f"25%  — RM {income * 0.25:,.0f}/month",              value=0.25),
            questionary.Choice(f"30%  — RM {income * 0.30:,.0f}/month",              value=0.30),
            questionary.Choice(f"40%+ — RM {income * 0.40:,.0f}/month",              value=0.40),
        ],
        default=0.20,
    ).ask()

    risk = questionary.select(
        "Risk tolerance:",
        instruction="Controls the P/E ceiling and minimum dividend yield used to screen stocks.",
        choices=[
            questionary.Choice(
                "Conservative — P/E ≤18x, dividend ≥4.5%, payout ≤70%",
                value=RiskTolerance.CONSERVATIVE,
            ),
            questionary.Choice(
                "Moderate     — P/E ≤28x, dividend ≥3.0%, payout ≤80%",
                value=RiskTolerance.MODERATE,
            ),
            questionary.Choice(
                "Aggressive   — P/E ≤40x, dividend ≥1.0%, payout ≤90%",
                value=RiskTolerance.AGGRESSIVE,
            ),
        ],
        default=RiskTolerance.MODERATE,
    ).ask()

    horizon = questionary.select(
        "Investment horizon:",
        instruction="How long before you need this money back. Under 3 years → volatile sectors downgraded.",
        choices=[
            questionary.Choice("Under 3 years  (short-term)",   value=2),
            questionary.Choice("3 – 5 years",                   value=4),
            questionary.Choice("6 – 10 years   (medium-term)",  value=7),
            questionary.Choice("More than 10 years (long-term)", value=12),
        ],
        default=4,
    ).ask()

    income_pref = questionary.select(
        "Investment focus:",
        choices=[
            questionary.Choice("Capital growth — higher potential returns, lower dividend required", value=False),
            questionary.Choice("Regular income — dividends prioritised, min 4.5% yield required",   value=True),
        ],
        default=False,
    ).ask()

    return {
        "age": age,
        "monthly_income": income,
        "monthly_savings": round(income * savings_ratio, 2),
        "savings_ratio": savings_ratio,
        "risk_tolerance": risk,
        "investment_horizon": horizon,
        "income_preference": income_pref,
    }


def collect_tickers() -> list[str]:
    console.print()
    console.rule("[bold]Stock Selection[/bold]")

    raw = questionary.text(
        "Enter Bursa Malaysia tickers to screen:",
        default="1155.KL",
        instruction="Comma-separated. Format: number.KL  e.g. 1155.KL, 5347.KL. Find tickers at klse.i3investor.com.",
        validate=lambda t: True if any(p.strip() for p in t.split(",")) else "Enter at least one ticker",
    ).ask()

    return [t.strip().upper() for t in raw.split(",") if t.strip()]


def collect_stock_details(ticker: str, sector: str) -> dict:
    console.print(f"  [dim]Sector detected:[/dim] [cyan]{sector}[/cyan]")

    is_pn17 = questionary.confirm(
        f"  Is {ticker} under PN17 distress listing? (check bursamalaysia.com — triggers AVOID)",
        default=False,
    ).ask()

    auditor_qualified = questionary.confirm(
        f"  Has the auditor flagged concerns in {ticker}'s financials? (a 'qualified/adverse' opinion — NOT a clean 'unqualified' opinion)",
        default=False,
    ).ask()

    extras: dict = {"is_pn17": is_pn17, "auditor_qualified": auditor_qualified}

    if sector == Sector.REITS:
        console.print(f"  [dim]REITs — distribution yield and occupancy not available on yfinance[/dim]")
        raw_dy = questionary.text(
            f"  Distribution yield for {ticker} (%):",
            default="6.0",
            instruction="Annual payout to unitholders ÷ unit price. Find on REIT manager website. BUY threshold: ≥6%.",
            validate=_pct_validator,
        ).ask()
        extras["distribution_yield"] = float(raw_dy)

        raw_occ = questionary.text(
            f"  Portfolio occupancy rate for {ticker} (%):",
            default="92",
            instruction="% of lettable space currently tenanted. Find in quarterly report. BUY threshold: ≥90%.",
            validate=_pct_validator,
        ).ask()
        extras["occupancy_rate"] = float(raw_occ)

    elif sector in (Sector.TECHNOLOGY, Sector.GLOVES):
        console.print(f"  [dim]{sector} — export exposure determines USD/MYR sensitivity[/dim]")
        raw_exp = questionary.text(
            f"  Export revenue as % of total revenue for {ticker}:",
            default="60",
            instruction="Higher % = more USD revenue = benefits when MYR weakens. Find in annual report geographic segment. BUY threshold: ≥60%.",
            validate=_pct_validator,
        ).ask()
        extras["export_revenue_pct"] = float(raw_exp)

    elif sector == Sector.CONSTRUCTION:
        console.print(f"  [dim]Construction — order book size = revenue visibility[/dim]")
        raw_ob = questionary.text(
            f"  Outstanding order book for {ticker} (RM billions):",
            default="5.0",
            instruction="Total unexecuted contract value. Find in quarterly results press release or investor presentation.",
            validate=_float_validator,
        ).ask()
        extras["order_book_rm"] = float(raw_ob)

    return extras
