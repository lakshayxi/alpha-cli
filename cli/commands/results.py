import typer
from rich.console import Console
from rich.table import Table
from datetime import datetime
from alpha_cli.core.storage.db import DatabaseManager

app = typer.Typer(help="Historical performance analysis and reporting.")
console = Console()
db = DatabaseManager()

@app.command()
def view(
    limit: int = typer.Option(20, "--limit", "-l", min=1, help="Maximum records to display."),
    min_sharpe: float = typer.Option(0.0, "--min-sharpe", "-s", help="Minimum Sharpe ratio filter."),
):
    """
    Displays a tabulated view of simulation results from the local database.
    Allows for quick filtering and analysis of discovered signals.
    """
    results = db.get_all_results()
    
    if not results:
        console.print("[yellow]No simulation history found.[/yellow]")
        return

    table = Table(title="Historical Alpha Simulations")
    table.add_column("Timestamp", style="dim")
    table.add_column("Expression", style="cyan", overflow="fold")
    table.add_column("Region", style="green")
    table.add_column("Sharpe", justify="right")
    table.add_column("Fitness", justify="right")
    table.add_column("Status", style="magenta")

    displayed_count = 0
    for res in results:
        sharpe = res.get('sharpe', 0.0)
        if sharpe < min_sharpe:
            continue
        
        ts = datetime.fromtimestamp(res['timestamp']).strftime('%Y-%m-%d %H:%M')
        
        # Performance-based styling
        sharpe_style = "bold green" if sharpe >= 1.25 else "red"
        fitness_style = "bold green" if res.get('fitness', 0.0) >= 1.0 else "red"
        
        table.add_row(
            ts,
            res['expression'],
            res['region'],
            f"[{sharpe_style}]{sharpe:.2f}[/{sharpe_style}]",
            f"[{fitness_style}]{res.get('fitness', 0.0):.2f}[/{fitness_style}]",
            res['status']
        )
        
        displayed_count += 1
        if displayed_count >= limit:
            break

    console.print(table)
    console.print(f"\n[dim]Displayed {displayed_count} of {len(results)} total records.[/dim]")
