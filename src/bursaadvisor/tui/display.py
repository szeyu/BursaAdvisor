from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from ..enums import Verdict

console = Console()

_VERDICT_STYLE = {
    Verdict.BUY:   "green",
    Verdict.WATCH: "yellow",
    Verdict.AVOID: "red",
}
_VERDICT_ICON = {
    Verdict.BUY:   "✅ BUY",
    Verdict.WATCH: "⚠  WATCH",
    Verdict.AVOID: "❌ AVOID",
}
_VERDICT_ORDER = {Verdict.BUY: 0, Verdict.WATCH: 1, Verdict.AVOID: 2}


def print_banner():
    content = Text.assemble(
        ("BursaAdvisor", "bold cyan"),
        "  v0.1\n",
        ("Bursa Malaysia Stock Screening Expert System\n", "dim"),
        ("WID2001 Knowledge Representation & Reasoning", "dim italic"),
    )
    console.print(Panel(content, border_style="cyan", padding=(0, 2)))
    console.print()


def print_section(title: str):
    console.rule(f"[bold]{title}[/bold]")


def print_fetch_status(ticker: str, sector: str, ok: bool):
    status = "[green]✓[/green]" if ok else "[red]✗[/red]"
    sector_tag = f"[dim]({sector})[/dim]" if sector else ""
    console.print(f"  {status} {ticker} {sector_tag}")


def print_investor_summary(profile: dict):
    monthly_savings = profile.get("monthly_savings", 0)
    horizon = profile.get("investment_horizon", 0)
    risk = profile.get("risk_tolerance", "—")
    console.print(
        f"  [dim]Investable capacity:[/dim] [bold]RM {monthly_savings:,.0f}/month[/bold]  "
        f"[dim]|  Horizon:[/dim] [bold]{horizon} yr[/bold]  "
        f"[dim]|  Risk:[/dim] [bold]{str(risk).capitalize()}[/bold]"
    )
    console.print()


def print_low_savings_warning(ratio: float):
    console.print(Panel(
        f"[yellow]Savings ratio {ratio * 100:.0f}% is below 20%.[/yellow]\n"
        "Consider building a 3–6 month emergency fund before committing capital.",
        title="[bold yellow]⚠  Financial Health Warning[/bold yellow]",
        border_style="yellow",
        padding=(0, 2),
    ))
    console.print()


def print_results(recommendations: list[dict], verbose_facts: list | None = None):
    if not recommendations:
        console.print("[dim]No recommendations generated.[/dim]")
        return

    recs = sorted(recommendations, key=lambda r: _VERDICT_ORDER.get(r["verdict"], 3))

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Verdict", width=9)
    table.add_column("Ticker", style="bold")
    table.add_column("Company")
    table.add_column("P/B", justify="right")
    table.add_column("Div%", justify="right")
    table.add_column("RSI", justify="right")
    table.add_column("Reason")

    for r in recs:
        verdict = r["verdict"]
        style = _VERDICT_STYLE.get(verdict, "")
        icon = _VERDICT_ICON.get(verdict, verdict)
        pb = f"{r['pb_ratio']:.2f}x" if r.get("pb_ratio") else "—"
        div = f"{r['div']:.1f}%" if r.get("div") else "—"
        rsi = f"{r['rsi']:.0f}" if r.get("rsi") else "—"
        table.add_row(icon, r["ticker"], r["name"], pb, div, rsi, r["reason"], style=style)

    console.print()
    console.print(table)

    buys = sum(1 for r in recs if r["verdict"] == Verdict.BUY)
    watches = sum(1 for r in recs if r["verdict"] == Verdict.WATCH)
    avoids = sum(1 for r in recs if r["verdict"] == Verdict.AVOID)
    console.print(
        f"\n  [green bold]{buys} BUY[/green bold]  "
        f"[yellow bold]{watches} WATCH[/yellow bold]  "
        f"[red bold]{avoids} AVOID[/red bold]\n"
    )

    if verbose_facts:
        console.rule("[dim]Intermediate Inference Facts[/dim]")
        for f in verbose_facts:
            console.print(f"  [dim]{escape(f)}[/dim]")
        console.print()
