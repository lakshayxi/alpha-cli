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

    def submit_simulation(self, expression: str, settings: Dict[str, Any]) -> str:
        """
        Submits an alpha expression for simulation.
        
        Args:
            expression: The FASTEXPR string.
            settings: Dictionary of simulation parameters.
            
        Returns:
            The simulation progress URL (Location header).
            
        Raises:
            SimulationError: If submission fails.
        """
        try:
            payload = {
                'type': 'REGULAR',
                'settings': settings,
                'regular': expression
            }
            
            logger.debug(f"Submitting simulation for: {expression[:50]}...")
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
        """
        Polls the simulation status until it reaches a terminal state.
        
        Args:
            simulation_url: URL to poll.
            max_wait: Maximum time in seconds to wait before timing out.
            
        Returns:
            Terminal simulation response dictionary.
            
        Raises:
            SimulationError: If polling times out or fails.
        """
        start_time = time.time()
        poll_interval = 5
        
        logger.debug(f"Monitoring simulation: {simulation_url}")
        
        while time.time() - start_time < max_wait:
            try:
                response = self.session.get(simulation_url, timeout=20)
                if response.status_code != 200:
                    logger.debug(f"Status check returned {response.status_code}, retrying...")
                    time.sleep(poll_interval)
                    continue
                
                data = response.json()
                status = data.get('status', 'UNKNOWN')
                progress = data.get('progress', 0.0)
                
                # Logic: treat non-zero progress with UNKNOWN status as RUNNING
                if status == 'UNKNOWN' and progress > 0:
                    status = 'RUNNING'
                
                logger.debug(f"Simulation status: {status} ({progress:.1%})")
                
                # Terminal states defined by WorldQuant API
                if status in ['COMPLETE', 'FAILED', 'ERROR', 'FAIL']:
                    return data
                
                time.sleep(poll_interval)
            except requests.RequestException as e:
                logger.warning(f"Polling network error: {e}. Retrying in 10s...")
                time.sleep(10)
        
        raise SimulationError(f"Simulation timed out after {max_wait} seconds.")

    def get_alpha_details(self, alpha_id: str) -> Dict[str, Any]:
        """
        Retrieves comprehensive performance metrics for a completed alpha.
        
        Args:
            alpha_id: Unique identifier for the alpha.
            
        Returns:
            Full metrics dictionary.
            
        Raises:
            SimulationError: If metrics cannot be retrieved.
        """
        try:
            logger.debug(f"Retrieving details for alpha: {alpha_id}")
            response = self.session.get(f"{self.BASE_URL}/alphas/{alpha_id}", timeout=20)
            if response.status_code == 200:
                return response.json()
            else:
                raise SimulationError(f"Failed to fetch alpha details ({response.status_code}): {response.text}")
        except requests.RequestException as e:
            raise SimulationError(f"Network error retrieving alpha details: {e}")
