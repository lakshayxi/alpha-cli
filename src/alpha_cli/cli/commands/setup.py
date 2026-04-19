import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from alpha_cli.config.settings import ConfigManager, Credentials, ConfigurationError
import subprocess
import sys

app = typer.Typer(help="Interactive configuration and authentication wizard.")
console = Console()
config_manager = ConfigManager()

@app.callback(invoke_without_command=True)
def setup_wizard(ctx: typer.Context):
    """
    Standardizes settings across the mining engine, offering both API key and 
    CLI-based (OAuth) authentication for supported providers like Gemini.
    """
    if ctx.invoked_subcommand is not None:
        return

    console.print(Panel.fit(
        "[bold blue]Alpha-CLI Configuration Wizard[/bold blue]\n"
        "Securely configure your AI providers and market credentials.",
        border_style="blue"
    ))

    try:
        # Step 1: Provider Selection
        provider = Prompt.ask(
            "Select AI Provider",
            choices=["OpenAI", "Anthropic", "Gemini"],
            default="Anthropic"
        )

        # Step 2: Authentication Strategy
        api_key = None
        use_cli_auth = False
        
        if provider == "Gemini":
            use_cli_auth = Confirm.ask("Use CLI-based sign-in (OAuth via Google Cloud)?")
            if use_cli_auth:
                console.print("\n[bold yellow]Requirement:[/bold yellow] Ensure you have the 'gcloud' CLI installed.")
                console.print("We will now attempt to initialize the login flow...")
                try:
                    # Attempt to trigger the standard Google ADC login
                    subprocess.run(["gcloud", "auth", "application-default", "login"], check=True)
                    console.print("[green]CLI Sign-in process completed.[/green]")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    console.print("[red]Error:[/red] Failed to trigger 'gcloud' login. Reverting to API key.")
                    use_cli_auth = False

        if not use_cli_auth:
            api_key = Prompt.ask(f"Enter {provider} API Key", password=True)

        # Step 3: WorldQuant Brain Credentials
        console.print("\n[bold]WorldQuant Brain Authentication[/bold]")
        username = Prompt.ask("Username (Email)")
        password = Prompt.ask("Password", password=True)

        # Step 4: Global Preferences
        console.print("\n[bold]Mining Preferences[/bold]")
        region = Prompt.ask("Default Region", choices=["USA", "EUR", "CHN", "ASI", "GLB", "IND"], default="USA")
        universe = Prompt.ask("Default Universe", default="TOP3000")

        # Step 5: Secure Persistence
        creds = Credentials(
            llm_provider=provider,
            llm_api_key=api_key,
            brain_username=username,
            brain_password=password,
            default_region=region,
            default_universe=universe,
            use_cli_auth=use_cli_auth
        )

        config_manager.save_credentials(creds)
        console.print("\n[bold green]Configuration persisted successfully.[/bold green]")
        console.print(f"Provider: [bold]{provider}[/bold] | Auth Mode: [bold]{'CLI/OAuth' if use_cli_auth else 'API Key'}[/bold]")
        
    except ConfigurationError as e:
        console.print(f"\n[bold red]Configuration Failure:[/bold red] {e}")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled.[/yellow]")
        raise typer.Exit()
    except Exception as e:
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
        raise typer.Exit(code=1)
