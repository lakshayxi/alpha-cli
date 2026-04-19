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
        Retrieves data fields by first identifying available datasets for the region.
        This approach bypasses the 400 errors triggered by broad data-field searches.
        """
        try:
            logger.info(f"Identifying available datasets for {region}...")
            
            # Step 1: Fetch a sample of fundamental and model datasets
            datasets_params = {
                'region': region,
                'delay': 1,
                'instrumentType': 'EQUITY',
                'limit': 5
            }
            
            ds_response = self.session.get(f"{self.BASE_URL}/data-sets", params=datasets_params, timeout=30)
            ds_response.raise_for_status()
            datasets = ds_response.json().get('results', [])
            
            if not datasets:
                logger.warning(f"No datasets found for {region}. Using emergency fallback fields.")
                return [{"id": "returns", "description": "Daily total returns"}]

            # Step 2: Fetch actual fields from the first few datasets
            all_fields = []
            for ds in datasets[:2]: # Only use top 2 datasets to stay within context limits
                ds_id = ds.get('id')
                logger.debug(f"Retrieving fields from dataset: {ds_id}")
                
                field_params = {
                    'dataset.id': ds_id,
                    'region': region,
                    'limit': 50 # Capture 50 fields per dataset
                }
                
                f_response = self.session.get(f"{self.BASE_URL}/data-fields", params=field_params, timeout=30)
                if f_response.status_code == 200:
                    fields = f_response.json().get('results', [])
                    all_fields.extend(fields)

            if not all_fields:
                return [{"id": "returns", "description": "Daily total returns"}]

            logger.info(f"Successfully synthesized context with {len(all_fields)} fields from {region} datasets.")
            return all_fields

        except Exception as e:
            logger.error(f"Data discovery pipeline failed: {e}")
            return [{"id": "returns", "description": "Daily total returns"}]
