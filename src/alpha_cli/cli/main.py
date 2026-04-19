import typer
import logging
import sys
from rich.console import Console
from alpha_cli.cli.commands import setup, mine, results

# Initialize the Typer application
app = typer.Typer(
    name="alpha-cli",
    help="Professional Command Line Interface for WorldQuant Brain Alpha Mining.",
    add_completion=False,
    no_args_is_help=True
)

# Register sub-command modules
app.add_typer(setup.app, name="setup")
app.add_typer(mine.app, name="mine")
app.add_typer(results.app, name="results")

console = Console()

def configure_logging(verbose: bool = False):
    """Initializes system-wide logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr
    )

@app.callback()
def global_options(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable detailed debug logging.")
):
    """
    Global configuration entry point for all alpha-cli commands.
    """
    configure_logging(verbose)
    if ctx.invoked_subcommand is None:
        console.print("[bold cyan]Alpha-CLI[/bold cyan]: WorldQuant Brain Discovery Engine")

if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        console.print(f"[bold red]Fatal Runtime Error:[/bold red] {e}")
        sys.exit(1)
