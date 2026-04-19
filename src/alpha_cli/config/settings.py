import os
import json
import keyring
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when there is an issue with system configuration or credentials."""
    pass

class Credentials(BaseModel):
    """Data container for system credentials and preferences."""
    llm_provider: str
    llm_api_key: Optional[str] = None # Optional for CLI-based auth (Gemini/OAuth)
    brain_username: str
    brain_password: str
    default_region: str = "USA"
    default_universe: str = "TOP3000"
    use_cli_auth: bool = False # Flag for Gemini OAuth

class ConfigManager:
    """
    Manages secure persistence of credentials and application settings.
    Supports both API key and CLI-based (OAuth) authentication modes.
    """
    
    SERVICE_NAME = "alpha-cli"
    CONFIG_DIR = Path.home() / ".alpha-cli"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    
    def __init__(self):
        try:
            self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ConfigurationError(f"Failed to create configuration directory: {e}")

    def save_credentials(self, creds: Credentials) -> None:
        """Persists configuration and sensitive keys."""
        try:
            config_data = {
                "llm_provider": creds.llm_provider,
                "default_region": creds.default_region,
                "default_universe": creds.default_universe,
                "use_cli_auth": creds.use_cli_auth
            }
            
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
                
            # Only store API key if not using CLI-based OAuth
            if not creds.use_cli_auth and creds.llm_api_key:
                keyring.set_password(self.SERVICE_NAME, f"{creds.llm_provider}_api_key", creds.llm_api_key)
            
            keyring.set_password(self.SERVICE_NAME, "brain_username", creds.brain_username)
            keyring.set_password(self.SERVICE_NAME, "brain_password", creds.brain_password)
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save credentials: {e}")

    def load_credentials(self) -> Optional[Credentials]:
        """Loads configuration and retrieves sensitive keys from the system keychain."""
        if not self.CONFIG_FILE.exists():
            return None
            
        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            provider = config_data.get("llm_provider")
            use_cli_auth = config_data.get("use_cli_auth", False)
            
            api_key = None
            if not use_cli_auth:
                api_key = keyring.get_password(self.SERVICE_NAME, f"{provider}_api_key")
            
            username = keyring.get_password(self.SERVICE_NAME, "brain_username")
            password = keyring.get_password(self.SERVICE_NAME, "brain_password")
            
            # For CLI auth, we don't need a stored API key
            if not username or not password or (not use_cli_auth and not api_key):
                return None
                
            return Credentials(
                llm_provider=provider,
                llm_api_key=api_key,
                brain_username=username,
                brain_password=password,
                default_region=config_data.get("default_region", "USA"),
                default_universe=config_data.get("default_universe", "TOP3000"),
                use_cli_auth=use_cli_auth
            )
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return None
