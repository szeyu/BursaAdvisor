import argparse
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .engine import BursaAdvisor
from .facts import (
    InvestorProfile, Stock, Recommendation,
    LowSavingsFlag, FundamentalPass, IncomeShiftFlag, ShortHorizonFlag, PeerBenchmark, MacroData,
)
from .data.stock_fetcher import fetch_stock_data
from .data.config_loader import try_load_sector_config
from .data.peer_benchmark import compute_peer_avg
from .data.macro_fetcher import fetch_macro
from .tui.prompts import collect_investor_profile, collect_tickers, collect_stock_details
from .tui.display import (
    print_banner, print_section, print_fetch_status,
    print_low_savings_warning, print_investor_summary, print_results,
)

console = Console()


def _declare_peer_benchmarks(engine: BursaAdvisor, sectors: set) -> None:
    """Compute live peer averages for each detected sector and declare as working memory facts."""
    for sector in sectors:
        cfg = try_load_sector_config(str(sector))
        if not cfg or not cfg.get("benchmark_peers"):
            continue

        metric = cfg["primary_metric"]
        fallback = cfg["peer_avg_fallback"]
        multiplier = cfg.get("avoid_multiplier", 1.2)

        with Progress(
            SpinnerColumn(),
            TextColumn(f"  Computing [cyan]{sector}[/cyan] peer avg ({metric})..."),
            transient=True,
            console=console,
        ) as progress:
            progress.add_task("benchmark", total=None)
            avg, is_live = compute_peer_avg(cfg["benchmark_peers"], metric, fallback)

        source = "[green]live[/green]" if is_live else "[yellow]fallback[/yellow]"
        console.print(f"  [dim]{sector} peer avg:[/dim] [bold]{avg:.2f}x[/bold]  [{source}]")

        engine.declare(PeerBenchmark(
            sector=sector,
            metric=metric,
            value=avg,
            avoid_multiplier=multiplier,
            is_live=is_live,
        ))


def main():
    parser = argparse.ArgumentParser(description="BursaAdvisor — Bursa Malaysia stock screener")
    parser.add_argument("--verbose", action="store_true", help="Show intermediate inference facts")
    args = parser.parse_args()

    print_banner()

    profile_data = collect_investor_profile()
    print_investor_summary(profile_data)
    tickers = collect_tickers()

    engine = BursaAdvisor()
    engine.reset()
    engine.declare(InvestorProfile(**profile_data))

    console.print()
    print_section("Fetching Market Data")

    with Progress(SpinnerColumn(), TextColumn("  Fetching macro indicators (OPR, USD/MYR)..."),
                  transient=True, console=console) as p:
        p.add_task("macro", total=None)
        macro = fetch_macro()

    opr_str = f"{macro['opr']:.2f}%" if macro["opr"] else "unavailable"
    fx_str  = f"{macro['usd_myr']:.3f}" if macro["usd_myr"] else "unavailable"
    console.print(f"  [dim]OPR:[/dim] [bold]{opr_str}[/bold]   [dim]USD/MYR:[/dim] [bold]{fx_str}[/bold]")
    engine.declare(MacroData(**macro))

    stock_cache: dict[str, dict] = {}

    for ticker in tickers:
        with Progress(
            SpinnerColumn(),
            TextColumn(f"  Fetching [cyan]{ticker}[/cyan]..."),
            transient=True,
            console=console,
        ) as progress:
            progress.add_task("fetch", total=None)
            data = fetch_stock_data(ticker)

        flags = collect_stock_details(ticker, data["sector"])
        data.update(flags)
        stock_cache[ticker] = data

        ok = data["market_cap_b"] is not None or data["pe_ratio"] is not None
        print_fetch_status(ticker, data["sector"], ok)

        engine.declare(Stock(**{k: v for k, v in data.items() if k in Stock.__fields__}))

    # Compute live peer benchmarks for all sectors present in this session
    seen_sectors = {d["sector"] for d in stock_cache.values()}
    _declare_peer_benchmarks(engine, seen_sectors)

    console.print()
    print_section("Running Inference Engine")
    engine.run()

    if any(isinstance(f, LowSavingsFlag) for f in engine.facts.values()):
        print_low_savings_warning(profile_data["savings_ratio"])

    recs = []
    for f in engine.facts.values():
        if isinstance(f, Recommendation):
            ticker = f["ticker"]
            stock = stock_cache.get(ticker, {})
            recs.append({
                "ticker": ticker,
                "name": stock.get("name", ticker),
                "verdict": f["verdict"],
                "reason": f["reason"],
                "pb_ratio": stock.get("pb_ratio"),
                "div": stock.get("dividend_yield"),
                "rsi": stock.get("rsi"),
            })

    verbose_facts = None
    if args.verbose:
        verbose_facts = []
        for f in engine.facts.values():
            if isinstance(f, MacroData):
                opr = f"{f['opr']:.2f}%" if f["opr"] else "N/A"
                fx  = f"{f['usd_myr']:.3f}" if f["usd_myr"] else "N/A"
                verbose_facts.append(
                    f"Macro indicators — OPR: {opr} (BNM policy rate)  |  USD/MYR: {fx} (exchange rate)"
                )
            elif isinstance(f, PeerBenchmark):
                src = "fetched live from yfinance" if f["is_live"] else "using fallback value (yfinance unavailable)"
                avoid = f["value"] * f["avoid_multiplier"]
                verbose_facts.append(
                    f"Sector peer average ({f['sector']}): {f['metric']} = {f['value']:.2f}x  "
                    f"[BUY if below {f['value']:.2f}x | AVOID if above {avoid:.2f}x]  source: {src}"
                )
            elif isinstance(f, FundamentalPass):
                verbose_facts.append(
                    f"Passed investor filter ({f['ticker']}): {f['note']}"
                )
            elif isinstance(f, IncomeShiftFlag):
                verbose_facts.append(
                    "Income-shift active: evaluating stocks on dividend yield only (age 45+ or income preference selected)"
                )
            elif isinstance(f, LowSavingsFlag):
                verbose_facts.append(
                    "Low savings warning: savings below 20% of income — volatile sector BUY recommendations downgraded to WATCH"
                )
            elif isinstance(f, ShortHorizonFlag):
                verbose_facts.append(
                    "Short horizon warning: investment horizon under 3 years — "
                    "volatile sectors (Technology, Gloves, Construction, Plantation, Property) downgraded from BUY to WATCH"
                )

    print_section("Results")
    print_results(recs, verbose_facts)


if __name__ == "__main__":
    main()
