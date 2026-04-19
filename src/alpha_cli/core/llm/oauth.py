import json
import logging
from typing import Dict, Any
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

class GoogleOAuthHandler:
    """
    Handles the OAuth 2.0 Authorization Code flow for Desktop applications.
    Spins up a local server to receive the authorization callback.
    """
    
    # Required scope for Gemini API access
    SCOPES = ['https://www.googleapis.com/auth/generative-language.retriever']

    def run_flow(self, client_id: str, client_secret: str) -> str:
        """
        Initiates the interactive web-based login flow.
        
        Args:
            client_id: Google Cloud OAuth Client ID.
            client_secret: Google Cloud OAuth Client Secret.
            
        Returns:
            A JSON string containing the serialized credentials (tokens).
        """
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"]
            }
        }
        
        try:
            flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
            
            # This opens the browser and starts a local server
            creds = flow.run_local_server(
                port=0, 
                authorization_prompt_message="Opening your browser for Google sign-in...",
                success_message="Authentication successful! You can close this tab and return to the CLI."
            )
            
            logger.info("Successfully acquired Google OAuth tokens.")
            return creds.to_json()
            
        except Exception as e:
            logger.error(f"OAuth flow failed: {e}")
            raise
