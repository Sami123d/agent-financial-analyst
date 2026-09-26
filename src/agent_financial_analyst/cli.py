"""CLI for agent-financial-analyst."""

from __future__ import annotations

import asyncio
import json

import click

from .core.orchestrator import ResearchOrchestrator
from .schema.models import ResearchReport


def _print_progress(report: ResearchReport) -> None:
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box

        console = Console()
        console.print()
        table = Table(
            title=f"agent-financial-analyst — {report.ticker}",
            box=box.ROUNDED,
            header_style="bold cyan",
        )
        table.add_column("Agent", style="bold", min_width=20)
        table.add_column("Status", justify="center", width=8)
        table.add_column("Time", justify="right", width=6)
        table.add_column("Details")

        for a in report.agent_outputs:
            status = "[green]✅[/]" if not a.error else "[red]❌[/]"
            detail = a.error or (
                f"{a.tokens:,} tokens" if a.tokens else a.content[:50]
            )
            table.add_row(
                a.agent_name, status,
                f"{a.latency_seconds:.1f}s",
                detail,
            )

        table.add_section()
        table.add_row(
            "[bold]Total[/]", "",
            f"[bold]{report.total_latency_seconds:.1f}s[/bold]",
            f"[bold]${report.total_cost_usd:.3f}[/bold]",
        )
        console.print(table)
        console.print()
    except ImportError:
        print(f"\n{report.ticker} — {report.total_latency_seconds:.1f}s, ${report.total_cost_usd:.3f}")
        for a in report.agent_outputs:
            status = "OK" if not a.error else "FAIL"
            print(f"  {a.agent_name}: {status} ({a.latency_seconds:.1f}s)")


@click.group("agent-analyst")
@click.version_option(version="0.1.0", prog_name="agent-financial-analyst")
def cli():
    """Multi-agent equity research, automated."""


@cli.command()
@click.argument("ticker")
@click.option("--model", default="gpt-4o", help="Primary LLM model")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--output-dir", default="reports", help="Output directory")
@click.option("--format", "fmt", type=click.Choice(["markdown", "json"]), default="markdown")
@click.option("--no-technicals", is_flag=True, help="Skip technical analysis")
@click.option("--no-risk", is_flag=True, help="Skip risk assessment")
def report(ticker, model, output, output_dir, fmt, no_technicals, no_risk):
    """Generate a full equity research report for a ticker."""
    orchestrator = ResearchOrchestrator(
        main_model=model,
    )

    result = asyncio.run(orchestrator.analyze(ticker))
    _print_progress(result)

    if fmt == "json":
        data = result.to_dict()
        json_str = json.dumps(data, indent=2)
        if output:
            with open(output, "w") as f:
                f.write(json_str)
        else:
            click.echo(json_str)
    else:
        filepath = output or str(result.save(output_dir))
        if output:
            with open(output, "w") as f:
                f.write(result.markdown)
        else:
            result.save(output_dir)
        click.echo(f"📄 Report saved → {filepath}")


@cli.command()
@click.argument("ticker")
@click.option("--model", default="gpt-4o-mini")
def summary(ticker, model):
    """Quick summary of a stock (no full report)."""
    from .tools import fetch_stock_data, format_number, format_pct

    data = fetch_stock_data(ticker)
    click.echo(f"\n{data.name} ({data.ticker})")
    click.echo(f"  Price: ${data.current_price:.2f}")
    click.echo(f"  Market Cap: {format_number(data.market_cap)}")
    click.echo(f"  P/E: {data.pe_ratio:.1f}x" if data.pe_ratio else "  P/E: N/A")
    click.echo(f"  Revenue Growth: {format_pct(data.revenue_growth)}")
    click.echo(f"  Gross Margin: {data.gross_margin:.1f}%" if data.gross_margin else "")
    click.echo(f"  RSI: {data.rsi_14}" if data.rsi_14 else "")
    click.echo()


@cli.command()
@click.option("--port", default=8000, help="Port to run the API on")
@click.option("--host", default="0.0.0.0", help="Host to bind to")
def serve(port, host):
    """Start the Research Analyst API server."""
    import uvicorn
    from .api.main import app
    click.echo(f"🚀 Starting AnalystPro API on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


@cli.command()
@click.argument("ticker")
def fundamentals(ticker):
    """Show fundamental data for a stock."""
    from .tools import fetch_stock_data, stock_data_summary
    data = fetch_stock_data(ticker)
    click.echo(stock_data_summary(data))


def main():
    cli()


if __name__ == "__main__":
    main()
