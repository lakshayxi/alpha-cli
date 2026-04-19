import requests
import time
import logging
from typing import Dict, Any, Optional
from alpha_cli.core.brain.models import SimulationResult

logger = logging.getLogger(__name__)

class SimulationError(Exception):
    """Raised when simulation submission or monitoring fails terminaly."""
    pass

class BrainSimulator:
    """
    Manages the lifecycle of an alpha simulation.
    Handles submission, terminal state polling, and metric retrieval.
    """
    
    BASE_URL = "https://api.worldquantbrain.com"
    
    def __init__(self, session: requests.Session):
        self.session = session

    def submit_simulation(self, expression: str, settings: Dict[str, Any], region: str, universe: str) -> str:
        """
        Submits an alpha expression for simulation with a fully valid settings payload.
        """
        try:
            # Construct a compliant WorldQuant Brain settings object
            # Note: removing 'lookback' as it's an internal LLM hint, not a WQ API parameter
            wq_settings = {
                "instrumentType": settings.get("instrumentType", "EQUITY"),
                "region": region,
                "universe": universe,
                "delay": int(settings.get("delay", 1)),
                "decay": int(settings.get("decay", 0)),
                "neutralization": settings.get("neutralization", "SUBINDUSTRY"),
                "truncation": float(settings.get("truncation", 0.08)),
                "pasteurization": "ON",
                "unitHandling": "VERIFY",
                "nanHandling": "OFF",
                "language": "FASTEXPR",
                "visualization": False
            }
            
            payload = {
                'type': 'REGULAR',
                'settings': wq_settings,
                'regular': expression
            }
            
            logger.debug(f"Submitting simulation to {region}:{universe}...")
            response = self.session.post(
                f"{self.BASE_URL}/simulations",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                location = response.headers.get('Location')
                if not location:
                    raise SimulationError("201 Created received but Location header is missing.")
                return location
            else:
                error_msg = f"Simulation submission failed ({response.status_code}): {response.text}"
                logger.error(error_msg)
                raise SimulationError(error_msg)
                
        except requests.RequestException as e:
            raise SimulationError(f"Network error during submission: {e}")

    def poll_simulation(self, simulation_url: str, max_wait: int = 300) -> Dict[str, Any]:
        """Polls status until terminal (handling silent progress and FAIL)."""
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(simulation_url, timeout=20)
                if response.status_code != 200:
                    time.sleep(5)
                    continue
                data = response.json()
                status = data.get('status', 'UNKNOWN')
                if status == 'UNKNOWN' and data.get('progress', 0) > 0:
                    status = 'RUNNING'
                if status in ['COMPLETE', 'FAILED', 'ERROR', 'FAIL']:
                    return data
                time.sleep(5)
            except Exception:
                time.sleep(10)
        raise SimulationError("Simulation timed out.")

    def get_alpha_details(self, alpha_id: str) -> Dict[str, Any]:
        """Retrieves comprehensive performance metrics."""
        response = self.session.get(f"{self.BASE_URL}/alphas/{alpha_id}", timeout=20)
        if response.status_code == 200:
            return response.json()
        raise SimulationError(f"Failed to fetch alpha details: {response.status_code}")
