import re
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class SemanticValidator:
    """
    Analyzes FASTEXPR signals for logical anti-patterns and market-specific violations.
    Prevents submissions that would result in redundant or mathematically flawed simulations.
    """
    
    def validate(self, expression: str, neutralization: str = "SUBINDUSTRY") -> List[str]:
        """
        Executes a suite of semantic integrity checks.
        
        Returns:
            List of violation descriptions. Empty if valid.
        """
        violations = []
        
        # Rule 1: Prevent double neutralization
        if neutralization != "NONE":
            if "group_neutralize" in expression.lower():
                violations.append("Redundant Neutralization: Signal contains group_neutralize while settings already enforce neutralization.")

        # Rule 2: Discourage final wrappers that degrade signal quality
        if expression.strip().lower().startswith("ts_decay_linear("):
            violations.append("Suboptimal Outermost Wrapper: ts_decay_linear should not be the final operation in the signal chain.")

        # Rule 3: Detect potential unit dimension mismatches
        if "+" in expression:
            price_terms = ["close", "open", "high", "low", "vwap"]
            has_price = any(term in expression.lower() for term in price_terms)
            has_volume = "volume" in expression.lower()
            
            if has_price and has_volume:
                # Basic check for cross-unit addition patterns
                if re.search(r'(?:price|close|open|high|low|vwap).*\+.*volume', expression.lower()) or \
                   re.search(r'volume.*\+.*(?:price|close|open|high|low|vwap)', expression.lower()):
                    violations.append("Unit Dimension Mismatch: Attempting to add price-based metrics and volume-based metrics.")

        # Rule 4: Identify ineffective division guards
        # Pattern: max(x, constant * x) which is tautological
        if re.search(r'max\s*\(\s*(\w+)\s*,\s*0\.\d+\s*\*\s*\1\s*\)', expression.lower()):
            violations.append("Tautological Division Guard: self-referencing max() guard detected.")

        return violations
