from enum import Enum
import logging
from alpha_cli.core.brain.models import SimulationResult

logger = logging.getLogger(__name__)

class Action(Enum):
    """Lifecycle actions for an alpha candidate based on performance evaluation."""
    DROP = "DROP"       # Sub-threshold performance; discard.
    ITERATE = "ITERATE" # Promising Sharpe but low fitness; needs parameter tuning.
    PUSH = "PUSH"       # High-conviction alpha; preserve for final submission.
    FLIP = "FLIP"       # Inverse signal detected; retry with sign reversal.

class DecisionEngine:
    """
    Evaluates simulation metrics to determine the optimal next step in the alpha lifecycle.
    Implements a prioritized decision tree based on Sharpe and Fitness thresholds.
    """
    
    def decide(self, result: SimulationResult) -> Action:
        """
        Analyzes performance metrics and recommends a lifecycle action.
        
        Args:
            result: SimulationResult containing computed metrics.
            
        Returns:
            The recommended Action enum.
        """
        sharpe = abs(result.sharpe)
        fitness = result.fitness
        
        # Rule 1: Detect inverse correlation (significant negative Sharpe)
        if result.sharpe < -0.8:
            logger.info(f"Signal inversion detected (Sharpe: {result.sharpe}). Recommending sign flip.")
            return Action.FLIP
            
        # Rule 2: Immediate drop for catastrophic performance
        if sharpe < 0.5:
            return Action.DROP
            
        # Rule 3: Drop for signals that lack consistency (low fitness at marginal Sharpe)
        if 0.5 <= sharpe <= 1.0 and fitness < 0.3:
            return Action.DROP
            
        # Rule 4: High-Sharpe signals with low fitness are optimization candidates
        if sharpe > 1.5 and fitness < 0.7:
            return Action.ITERATE
            
        # Rule 5: Strong signals that meet target criteria
        if sharpe >= 1.25 and fitness >= 1.0:
            return Action.PUSH
            
        # Default logic for generic "healthy" signals
        if sharpe > 1.0 and fitness > 0.5:
            return Action.PUSH
            
        return Action.DROP
