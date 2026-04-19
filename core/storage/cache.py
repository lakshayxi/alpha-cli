import hashlib
from typing import Set

class ExpressionCache:
    """Hash-based cache to prevent exact duplicate expressions"""
    
    def __init__(self):
        self._hashes: Set[str] = set()

    def add(self, expression: str):
        """Adds an expression hash to the cache"""
        h = self._get_hash(expression)
        self._hashes.add(h)

    def contains(self, expression: str) -> bool:
        """Checks if an expression has already been seen"""
        h = self._get_hash(expression)
        return h in self._hashes

    def _get_hash(self, expression: str) -> str:
        """Normalizes and hashes an expression string"""
        # Normalize: lowercase, strip, remove spaces
        normalized = expression.lower().strip().replace(" ", "")
        return hashlib.md5(normalized.encode()).hexdigest()
