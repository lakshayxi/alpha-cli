import os
import json
import keyring
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when there is an issue with system configuration."""
    pass

class Credentials(BaseModel):
    """Data container for mining engine preferences."""
    llm_provider: str # 'gemini' or 'claude'
    brain_username: str
    brain_password: str
    default_region: str = "USA"
    default_universe: str = "TOP3000"

class ConfigManager:
    """
    Manages secure persistence of application settings.
    Leverages external CLI tools (Gemini, Claude Code) for LLM authentication.
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
        """Persists preference and credentials."""
        try:
            # Save non-sensitive settings
            config_data = {
                "llm_provider": creds.llm_provider,
                "default_region": creds.default_region,
                "default_universe": creds.default_universe
            }
            
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
                
            # Store WorldQuant sensitive data in keychain
            keyring.set_password(self.SERVICE_NAME, "brain_username", creds.brain_username)
            keyring.set_password(self.SERVICE_NAME, "brain_password", creds.brain_password)
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save credentials: {e}")

    def load_credentials(self) -> Optional[Credentials]:
        """Loads system configuration."""
        if not self.CONFIG_FILE.exists():
            return None
            
        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            provider = config_data.get("llm_provider")
            username = keyring.get_password(self.SERVICE_NAME, "brain_username")
            password = keyring.get_password(self.SERVICE_NAME, "brain_password")
            
            if not all([provider, username, password]):
                return None
                
            return Credentials(
                llm_provider=provider,
                brain_username=username,
                brain_password=password,
                default_region=config_data.get("default_region", "USA"),
                default_universe=config_data.get("default_universe", "TOP3000")
            )
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return None
