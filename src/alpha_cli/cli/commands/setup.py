import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from alpha_cli.config.settings import ConfigManager, Credentials, ConfigurationError
import subprocess
import sys
import os

app = typer.Typer(help="Interactive configuration and authentication wizard.")
console = Console()
config_manager = ConfigManager()

@app.callback(invoke_without_command=True)
def setup_wizard(ctx: typer.Context):
    """
    Standardizes settings across the mining engine, offering both API key and 
    native web-based (OAuth) authentication for supported providers like Gemini.
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
        oauth_token_json = None
        
        if provider == "Gemini":
            use_cli_auth = Confirm.ask("Use web-based sign-in (Native OAuth)?")
            if use_cli_auth:
                console.print("\n[bold]Native Google OAuth Setup[/bold]")
                console.print("To use native web login, you must provide an OAuth Desktop Client ID.")
                console.print("1. Go to: [cyan]https://console.cloud.google.com/apis/credentials[/cyan]")
                console.print("2. Create 'OAuth 2.0 Client ID' -> Application type: 'Desktop App'")
                console.print("3. Copy your Client ID and Client Secret below.\n")
                
                client_id = Prompt.ask("Enter OAuth Client ID")
                client_secret = Prompt.ask("Enter OAuth Client Secret", password=True)
                
                # Import here to avoid requiring dependency if not used
                from alpha_cli.core.llm.oauth import GoogleOAuthHandler
                handler = GoogleOAuthHandler()
                
                try:
                    with console.status("[bold green]Waiting for browser authentication...[/bold green]"):
                        oauth_token_json = handler.run_flow(client_id, client_secret)
                    console.print("[green]Successfully acquired OAuth session.[/green]")
                except Exception as e:
                    console.print(f"[red]Error:[/red] Web login failed: {e}")
                    console.print("Falling back to API key authentication.")
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
            use_cli_auth=use_cli_auth,
            oauth_token_json=oauth_token_json
        )

        config_manager.save_credentials(creds)
        console.print("\n[bold green]Configuration persisted successfully.[/bold green]")
        console.print(f"Provider: [bold]{provider}[/bold] | Auth Mode: [bold]{'Web/OAuth' if use_cli_auth else 'API Key'}[/bold]")
        
    except ConfigurationError as e:
        console.print(f"\n[bold red]Configuration Failure:[/bold red] {e}")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled.[/yellow]")
        raise typer.Exit()
    except Exception as e:
        console.print(f"\n[bold red]Unexpected Error:[/bold red] {e}")
        raise typer.Exit(code=1)
