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
        """Retrieves the complete list of available mathematical operators."""
        try:
            response = self.session.get(f"{self.BASE_URL}/operators", timeout=30)
            response.raise_for_status()
            data = response.json()
            operators = data if isinstance(data, list) else data.get('results', [])
            logger.info(f"Retrieved {len(operators)} operators.")
            return operators
        except Exception as e:
            logger.error(f"Failed to fetch operators: {e}")
            return []

    def fetch_data_fields(self, region: str, universe: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieves data fields using the correct WorldQuant Brain search parameters.
        """
        try:
            # WorldQuant API uses 'search' or filters for data-fields
            # Let's use a simpler query that is less likely to trigger a 400
            params = {
                'region': region,
                'universe': universe,
                'limit': limit,
                'offset': 0,
                # Adding some standard search context to avoid broad rejections
                'search': 'returns' 
            }
            logger.debug(f"Requesting fields: {self.BASE_URL}/data-fields with params {params}")
            response = self.session.get(f"{self.BASE_URL}/data-fields", params=params, timeout=30)
            
            if response.status_code == 400:
                # If 400, retry with minimal params
                logger.warning("Broad field search rejected, retrying with minimal filters...")
                response = self.session.get(
                    f"{self.BASE_URL}/data-fields", 
                    params={'limit': limit, 'region': region}, 
                    timeout=30
                )
            
            response.raise_for_status()
            data = response.json()
            fields = data if isinstance(data, list) else data.get('results', [])
            logger.info(f"Retrieved {len(fields)} fields for {region}.")
            return fields
        except Exception as e:
            logger.error(f"Failed to fetch data fields: {e}")
            return []
