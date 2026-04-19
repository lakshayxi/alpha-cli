import requests
from requests.auth import HTTPBasicAuth
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Raised when authentication with the Brain API fails."""
    pass

class BrainAuth:
    """
    Manages the lifecycle of an authenticated session with the WorldQuant Brain API.
    Handles credential verification and session persistence.
    """
    
    BASE_URL = "https://api.worldquantbrain.com"
    
    def __init__(self):
        self._session = requests.Session()
        self._is_authenticated = False

    def authenticate(self, username: str, password: str) -> bool:
        """
        Establishes an authenticated session.
        
        Args:
            username: User email address.
            password: User password.
            
        Returns:
            True if successful.
            
        Raises:
            AuthenticationError: If the server rejects the credentials.
        """
        try:
            logger.debug(f"Attempting authentication for user: {username}")
            response = self._session.post(
                f"{self.BASE_URL}/authentication",
                auth=HTTPBasicAuth(username, password),
                timeout=30
            )
            
            if response.status_code == 201:
                self._is_authenticated = True
                logger.info(f"Authentication successful for {username}")
                return True
            else:
                error_msg = f"Auth failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise AuthenticationError(error_msg)
                
        except requests.RequestException as e:
            logger.error(f"Network error during authentication: {e}")
            raise AuthenticationError(f"Connection failure: {e}")

    @property
    def session(self) -> requests.Session:
        """Provides access to the internal authenticated session."""
        if not self._is_authenticated:
            logger.warning("Accessing session before successful authentication.")
        return self._session

    @property
    def is_authenticated(self) -> bool:
        """Indicates if the session is currently authenticated."""
        return self._is_authenticated
