from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SettingsOptimizer:
    """
    Implements a sequential optimization strategy for near-passing alphas.
    Systematically adjusts simulation parameters (lookback, decay, truncation)
    to maximize signal robustness and consistency.
    """
    
    def optimize(self, current_settings: Dict[str, Any], attempt_number: int) -> Dict[str, Any]:
        """
        Generates an optimized settings dictionary for a specific iteration.
        
        Optimization Hierarchy:
        1. Increase lookback (stabilize signal)
        2. Increase decay (smoothen transitions)
        3. Tighten truncation (reduce tail risk impact)
        """
        optimized = current_settings.copy()
        
        if attempt_number == 1:
            # Shift towards longer memory
            optimized['lookback'] = 60
            logger.debug("Optimization stage 1: lookback increased to 60.")
            
        elif attempt_number == 2:
            # Apply heavier decay to reduce turnover impact
            current_decay = optimized.get('decay', 0)
            optimized['decay'] = min(8, current_decay + 2)
            optimized['lookback'] = 90
            logger.debug(f"Optimization stage 2: decay={optimized['decay']}, lookback=90.")
            
        elif attempt_number == 3:
            # Maximum stabilization and aggressive truncation
            current_trunc = optimized.get('truncation', 0.08)
            optimized['truncation'] = max(0.01, current_trunc - 0.02)
            optimized['decay'] = 8
            optimized['lookback'] = 120
            logger.debug(f"Optimization stage 3: truncation={optimized['truncation']}, max lookback/decay.")
            
        return optimized
