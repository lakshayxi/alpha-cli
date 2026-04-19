import re
import logging
from typing import List, Dict, Any, Tuple
from alpha_cli.core.storage.db import DatabaseManager

logger = logging.getLogger(__name__)

class PatternAnalyzer:
    """
    Simulates human-like observation by analyzing the database for recurring patterns.
    Synthesizes raw simulation data into high-level 'Heuristics' for the LLM.
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db

    def synthesize_learnings(self) -> None:
        """
        Runs a reflection cycle to extract patterns from historical simulations.
        Learnings are persisted as heuristics in the database.
        """
        logger.info("Initiating pattern analysis and heuristic synthesis...")
        raw_insights = self.db.get_performance_insights()
        
        # 1. Analyze Success Motifs (Operator sequences that work)
        self._analyze_success_motifs(raw_insights.get("top_performers", []))
        
        # 2. Analyze Failure Modes (Specific errors that repeat)
        self._analyze_failure_modes(raw_insights.get("frequent_errors", []))

    def _analyze_success_motifs(self, top_alphas: List[Tuple[str, float, float]]) -> None:
        """Identifies recurring mathematical structures in high-Sharpe alphas."""
        if not top_alphas:
            return
            
        operator_counts = {}
        for expr, sharpe, fitness in top_alphas:
            # Extract common 2-operator sequences like ts_rank(ts_delta(...))
            sequences = re.findall(r'(\w+)\s*\(\s*(\w+)\s*\(', expr)
            for seq in sequences:
                pair = f"{seq[0]}({seq[1]}(...))"
                operator_counts[pair] = operator_counts.get(pair, 0) + 1
        
        # Store high-confidence motifs
        for motif, count in operator_counts.items():
            if count >= 2: # Pattern observed at least twice
                content = f"The sequence '{motif}' is frequently found in alphas with Sharpe > 1.0."
                # Confidence is a simple ratio here
                confidence = min(0.9, 0.5 + (count / len(top_alphas)))
                self.db.store_heuristic("SUCCESS_PATTERN", content, confidence)

    def _analyze_failure_modes(self, frequent_errors: List[Tuple[str, int]]) -> None:
        """Identifies systemic mistakes that the system should avoid."""
        for error_cat, count in frequent_errors:
            if count >= 3: # Systemic issue
                if error_cat == "EVENT_INCOMPATIBILITY":
                    content = "Systemic issue: Multiple event fields failed with cross-sectional operators. Favor ts_rank for normalization."
                    self.db.store_heuristic("FAILURE_PATTERN", content, 0.85)
                elif error_cat == "PARAMETER_MISMATCH":
                    content = "Frequent syntax rejection: Ensure lookback parameters are explicitly provided for all ts_* functions."
                    self.db.store_heuristic("FAILURE_PATTERN", content, 0.8)
                elif error_cat == "LOW_CONSISTENCY":
                    content = "Pattern observed: High Sharpe signals often have low Fitness due to insufficient decay. Suggest increasing decay to 4+."
                    self.db.store_heuristic("FAILURE_PATTERN", content, 0.75)
