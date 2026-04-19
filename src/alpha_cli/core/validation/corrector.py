import re
import logging
from typing import List, Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)

class AlphaCorrector:
    """
    Implements deterministic correction logic for common FASTEXPR and WorldQuant Brain errors.
    Focuses on surgical precision to avoid corrupting valid segments of an expression.
    """
    
    # Mapping of operators that are incompatible with event-type data fields.
    EVENT_OPERATOR_SWAPS = {
        "inverse": "ts_rank",
        "mean": "vec_avg",
        "std": "ts_rank",
        "abs": "ts_rank",
        "log": "ts_rank",
    }

    def fix_input_count_error(self, expression: str, error_message: str) -> Tuple[str, List[str]]:
        """
        Surgically adds or removes parameters for a specific operator mentioned in an error message.
        
        Args:
            expression: The original FASTEXPR string.
            error_message: The error string returned by the WorldQuant API.
            
        Returns:
            A tuple of (fixed_expression, list_of_applied_fixes).
        """
        # Identify the problematic operator and the expected count
        op_name_match = re.search(r"Operator\s+'(\w+)'", error_message, re.IGNORECASE)
        count_match = re.search(r"invalid number of inputs\s*:\s*(\d+)\s*,\s*should be (?:exactly|at least)\s*(\d+)", error_message, re.IGNORECASE)
        
        if not count_match:
            return expression, []

        actual_count = int(count_match.group(1))
        expected_count = int(count_match.group(2))
        target_op = op_name_match.group(1).lower() if op_name_match else None

        operator_pattern = r'\b([a-z_]+)\s*\('
        matches = list(re.finditer(operator_pattern, expression, re.IGNORECASE))
        
        if target_op:
            # Narrow down to the specific operator if name was extracted
            matches = [m for m in matches if m.group(1).lower() == target_op]

        for m in matches:
            op_name = m.group(1)
            start_pos = m.start()
            
            # Find the scope of the current function call
            end_pos = self._find_matching_paren(expression, m.end() - 1)
            if end_pos == -1:
                continue

            params_str = expression[m.end():end_pos-1]
            params = self._split_params(params_str)
            
            if len(params) == actual_count:
                # Apply padding with safe default values (usually 1)
                if expected_count > len(params):
                    needed = expected_count - len(params)
                    new_params = params + ["1"] * needed
                    fixed_call = f"{op_name}({', '.join(new_params)})"
                    logger.info(f"Corrected {op_name}: padded from {len(params)} to {expected_count} inputs.")
                    return expression[:start_pos] + fixed_call + expression[end_pos:], [f"Padded {op_name} inputs"]
                
                # Apply truncation
                elif expected_count < len(params) and expected_count > 0:
                    new_params = params[:expected_count]
                    fixed_call = f"{op_name}({', '.join(new_params)})"
                    logger.info(f"Corrected {op_name}: truncated from {len(params)} to {expected_count} inputs.")
                    return expression[:start_pos] + fixed_call + expression[end_pos:], [f"Truncated {op_name} inputs"]

        return expression, []

    def swap_event_operators(self, expression: str) -> Tuple[str, List[str]]:
        """
        Identifies event-type fields and replaces incompatible operators with their safe equivalents.
        """
        fixes = []
        fixed_expr = expression
        
        # Detect fields starting with known event prefixes
        event_fields = re.findall(r'\b((?:nws|rp|fnd)_[a-z0-9_]+)\b', fixed_expr, re.IGNORECASE)
        if not event_fields:
            return expression, []

        for incompatible_op, safe_op in self.EVENT_OPERATOR_SWAPS.items():
            pattern = r'\b' + re.escape(incompatible_op) + r'\s*\('
            if re.search(pattern, fixed_expr, re.IGNORECASE):
                fixed_expr = re.sub(pattern, f"{safe_op}(", fixed_expr, flags=re.IGNORECASE)
                fixes.append(f"Swapped {incompatible_op} to {safe_op} for event field compatibility.")
        
        return fixed_expr, fixes

    def _find_matching_paren(self, s: str, start_index: int) -> int:
        """Helper to find the index of a matching closing parenthesis."""
        count = 0
        for i in range(start_index, len(s)):
            if s[i] == '(':
                count += 1
            elif s[i] == ')':
                count -= 1
                if count == 0:
                    return i + 1
        return -1

    def _split_params(self, params_str: str) -> List[str]:
        """Splits a comma-separated string into a list of parameters, respecting nested parentheses."""
        params = []
        current = []
        depth = 0
        for char in params_str:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ',' and depth == 0:
                params.append("".join(current).strip())
                current = []
                continue
            current.append(char)
        if current:
            params.append("".join(current).strip())
        return params
