import requests
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BrainFetcher:
    """
    Retrieves metadata catalogs from the WorldQuant Brain API.
    Provides necessary context (operators and fields) for LLM-based alpha generation.
    """
    
    BASE_URL = "https://api.worldquantbrain.com"
    
    def __init__(self, session: requests.Session):
        self.session = session

    def fetch_operators(self) -> List[Dict[str, Any]]:
        """
        Retrieves the complete list of available mathematical operators.
        
        Returns:
            List of operator definitions.
        """
        try:
            logger.debug("Fetching operator catalog...")
            response = self.session.get(f"{self.BASE_URL}/operators", timeout=30)
            response.raise_for_status()
            data = response.json()
            operators = data.get('results', [])
            logger.info(f"Retrieved {len(operators)} operators.")
            return operators
        except requests.RequestException as e:
            logger.error(f"Failed to fetch operators: {e}")
            return []

    def fetch_data_fields(self, region: str, universe: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieves a representative subset of data fields for a given region and universe.
        
        Args:
            region: Market region (e.g., 'USA').
            universe: Investment universe (e.g., 'TOP3000').
            limit: Maximum number of fields to retrieve.
            
        Returns:
            List of field metadata objects.
        """
        try:
            logger.debug(f"Fetching data fields for {region}:{universe} (limit={limit})...")
            params = {
                'region': region,
                'universe': universe,
                'limit': limit,
                'offset': 0
            }
            response = self.session.get(f"{self.BASE_URL}/data-fields", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            fields = data.get('results', [])
            logger.info(f"Retrieved {len(fields)} fields for {region}:{universe}.")
            return fields
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data fields: {e}")
            return []
