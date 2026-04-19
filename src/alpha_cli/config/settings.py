import os
import json
import keyring
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, ValidationError

# Configure logging to stderr for internal system messages
logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when there is an issue with system configuration or credentials."""
    pass

class Credentials(BaseModel):
    """Data container for system credentials and preferences."""
    llm_provider: str
    llm_api_key: str
    brain_username: str
    brain_password: str
    default_region: str = "USA"
    default_universe: str = "TOP3000"

class ConfigManager:
    """
    Manages secure persistence of credentials and application settings.
    Uses the system keychain for sensitive data and local JSON for non-sensitive preferences.
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
        """
        Persists credentials securely.
        
        Args:
            creds: Validated Credentials object.
        """
        try:
            # Save non-sensitive preferences to disk
            config_data = {
                "llm_provider": creds.llm_provider,
                "default_region": creds.default_region,
                "default_universe": creds.default_universe
            }
            
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
                
            # Store sensitive keys in the system keychain
            keyring.set_password(self.SERVICE_NAME, f"{creds.llm_provider}_api_key", creds.llm_api_key)
            keyring.set_password(self.SERVICE_NAME, "brain_username", creds.brain_username)
            keyring.set_password(self.SERVICE_NAME, "brain_password", creds.brain_password)
            
            logger.info("Credentials and configuration saved successfully.")
        except Exception as e:
            raise ConfigurationError(f"Failed to save credentials: {e}")

    def load_credentials(self) -> Optional[Credentials]:
        """
        Loads credentials from secure storage.
        
        Returns:
            Populated Credentials object or None if configuration is missing/invalid.
        """
        if not self.CONFIG_FILE.exists():
            logger.debug("Configuration file not found.")
            return None
            
        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            provider = config_data.get("llm_provider")
            if not provider:
                return None
                
            api_key = keyring.get_password(self.SERVICE_NAME, f"{provider}_api_key")
            username = keyring.get_password(self.SERVICE_NAME, "brain_username")
            password = keyring.get_password(self.SERVICE_NAME, "brain_password")
            
            if not all([api_key, username, password]):
                logger.warning("Configuration exists but sensitive data is missing from keychain.")
                return None
                
            return Credentials(
                llm_provider=provider,
                llm_api_key=api_key,
                brain_username=username,
                brain_password=password,
                default_region=config_data.get("default_region", "USA"),
                default_universe=config_data.get("default_universe", "TOP3000")
            )
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Corrupt configuration detected: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {e}")
            return None
