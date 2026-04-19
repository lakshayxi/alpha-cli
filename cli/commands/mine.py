import typer
import time
import logging
from rich.console import Console
from alpha_cli.config.settings import ConfigManager
from alpha_cli.core.llm.client import LLMClient
from alpha_cli.core.brain.auth import BrainAuth, AuthenticationError
from alpha_cli.core.brain.simulator import BrainSimulator
from alpha_cli.core.brain.fetcher import BrainFetcher
from alpha_cli.core.storage.db import DatabaseManager
from alpha_cli.core.engine.orchestrator import MiningOrchestrator

app = typer.Typer(help="Autonomous alpha discovery operations.")
console = Console()
config_manager = ConfigManager()

@app.command()
def start(
    region: str = typer.Option(None, "--region", "-r", help="Target region for alpha mining."),
    universe: str = typer.Option(None, "--universe", "-u", help="Target investment universe."),
    iterations: int = typer.Option(10, "--iterations", "-i", min=1, help="Number of mining cycles to execute."),
):
    """
    Initiates the autonomous mining loop.
    Coordinates generation, validation, and remote simulation efforts.
    """
    # Load and validate configuration
    creds = config_manager.load_credentials()
    if not creds:
        console.print("[red]Error: System not configured. Execute 'alpha-cli setup' to begin.[/red]")
        raise typer.Exit(code=1)

    # Use defaults if not overridden
    active_region = region or creds.default_region
    active_universe = universe or creds.default_universe

    console.print(f"[bold green]Starting autonomous discovery: {active_region} {active_universe}[/bold green]")
    
    try:
        # Initialize remote connectivity
        auth = BrainAuth()
        auth.authenticate(creds.brain_username, creds.brain_password)
        
        # Build component graph
        session = auth.session
        llm_client = LLMClient(creds)
        simulator = BrainSimulator(session)
        fetcher = BrainFetcher(session)
        db = DatabaseManager()
        
        orchestrator = MiningOrchestrator(llm_client, simulator, fetcher, db)
        
        # Prepare context for prompt engineering
        orchestrator.prepare_context(active_region, active_universe)

        # Execution loop
        for cycle in range(1, iterations + 1):
            console.print(f"\n[bold]Execution Cycle {cycle} of {iterations}[/bold]")
            orchestrator.run_iteration(active_region, active_universe)
            
            if cycle < iterations:
                # Modest throttle to respect API rate limits
                time.sleep(2)
            
    except AuthenticationError as e:
        console.print(f"[red]Fatal: WorldQuant Brain authentication failed: {e}[/red]")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Discovery process interrupted by operator.[/yellow]")
        raise typer.Exit()
    except Exception as e:
        console.print(f"[red]Unexpected system failure: {e}[/red]")
        logging.exception("Mining loop crash")
        raise typer.Exit(code=1)

    console.print("\n[bold green]Discovery session completed.[/bold green]")
