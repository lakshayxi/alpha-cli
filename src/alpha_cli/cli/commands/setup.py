import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from alpha_cli.config.settings import ConfigManager, Credentials, ConfigurationError

app = typer.Typer(help="Interactive configuration and authentication wizard.")
console = Console()
config_manager = ConfigManager()

@app.callback(invoke_without_command=True)
def setup_wizard(ctx: typer.Context):
    """
    Executes the interactive setup sequence to configure LLM and WorldQuant Brain credentials.
    Standardizes settings across the mining engine.
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

        # Step 2: Sensitive Data Entry
        api_key = Prompt.ask(f"Enter {provider} API Key", password=True)

        console.print("\n[bold]WorldQuant Brain Authentication[/bold]")
        username = Prompt.ask("Username (Email)")
        password = Prompt.ask("Password", password=True)

        # Step 3: Global Preferences
        console.print("\n[bold]Mining Preferences[/bold]")
        region = Prompt.ask("Default Region", choices=["USA", "EUR", "CHN", "ASI", "GLB", "IND"], default="USA")
        universe = Prompt.ask("Default Universe", default="TOP3000")

        # Step 4: Secure Persistence
        creds = Credentials(
            llm_provider=provider,
            llm_api_key=api_key,
            brain_username=username,
            brain_password=password,
            default_region=region,
            default_universe=universe
        )

        config_manager.save_credentials(creds)
        console.print("\n[bold green]Configuration persisted successfully.[/bold green]")
        console.print(f"Provider: [bold]{provider}[/bold] | Region: [bold]{region}[/bold]")
        console.print("Run 'alpha-cli mine start' to begin alpha discovery.")
        
    except ConfigurationError as e:
        console.print(f"\n[bold red]Configuration Failure:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
        raise typer.Exit(code=1)
