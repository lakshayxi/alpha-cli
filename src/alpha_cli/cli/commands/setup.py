import typer
import shutil
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from alpha_cli.config.settings import ConfigManager, Credentials, ConfigurationError

app = typer.Typer(help="Interactive configuration for WorldQuant and Agent CLI delegation.")
console = Console()
config_manager = ConfigManager()

@app.callback(invoke_without_command=True)
def setup_wizard(ctx: typer.Context):
    """
    Standardizes settings by verifying the availability of specialized agent CLIs
    (like Gemini or Claude Code) and configuring WorldQuant Brain credentials.
    """
    if ctx.invoked_subcommand is not None:
        return

    console.print(Panel.fit(
        "[bold blue]Alpha-CLI Configuration Wizard[/bold blue]\n"
        "Leveraging specialized agent CLIs for autonomous discovery.",
        border_style="blue"
    ))

    try:
        # Step 1: Agent CLI Selection
        provider = Prompt.ask(
            "Select your primary Agent CLI for generation",
            choices=["gemini", "claude"],
            default="gemini"
        )

        # Step 2: Verification
        console.print(f"\nVerifying '{provider}' installation...")
        if not shutil.which(provider):
            console.print(f"[bold red]Error:[/bold red] '{provider}' CLI was not found in your system PATH.")
            if provider == "gemini":
                console.print("Please install the Gemini CLI before continuing.")
            else:
                console.print("Please install Claude Code (claude) before continuing.")
            raise typer.Exit(code=1)
        
        console.print(f"[green]Confirmed:[/green] '{provider}' is available.")

        # Step 3: WorldQuant Brain Credentials
        console.print("\n[bold]WorldQuant Brain Authentication[/bold]")
        username = Prompt.ask("Username (Email)")
        password = Prompt.ask("Password", password=True)

        # Step 4: Global Preferences
        console.print("\n[bold]Discovery Preferences[/bold]")
        region = Prompt.ask("Default Region", choices=["USA", "EUR", "CHN", "ASI", "GLB", "IND"], default="USA")
        universe = Prompt.ask("Default Universe", default="TOP3000")

        # Step 5: Secure Persistence
        creds = Credentials(
            llm_provider=provider,
            brain_username=username,
            brain_password=password,
            default_region=region,
            default_universe=universe
        )

        config_manager.save_credentials(creds)
        console.print("\n[bold green]Configuration persisted successfully.[/bold green]")
        console.print(f"Engine: [bold]Alpha-CLI[/bold] | Delegate: [bold]{provider}[/bold]")
        console.print(f"Status: Ready to mine in [bold]{region}[/bold].")
        
    except ConfigurationError as e:
        console.print(f"\n[bold red]Configuration Failure:[/bold red] {e}")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup aborted by operator.[/yellow]")
        raise typer.Exit()
    except Exception as e:
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
        raise typer.Exit(code=1)
