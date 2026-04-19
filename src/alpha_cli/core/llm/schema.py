from pydantic import BaseModel, Field
from typing import Dict, Optional

class AlphaSettings(BaseModel):
    """Encapsulates simulation parameters recommended by the LLM."""
    universe: str = Field(default="TOP3000", description="Target investment universe.")
    decay: int = Field(default=0, ge=0, le=8, description="Time-series decay parameter.")
    truncation: float = Field(default=0.08, description="Position truncation threshold.")
    neutralization: str = Field(default="SUBINDUSTRY", description="Risk neutralization level.")
    lookback: int = Field(default=20, description="Default lookback window for signal calculation.")

class AlphaGeneration(BaseModel):
    """The structured output schema for LLM-generated alpha ideas."""
    expression: str = Field(description="The formal FASTEXPR mathematical string.")
    thesis: str = Field(description="The underlying economic intuition or rationale.")
    recommended_settings: AlphaSettings = Field(description="Parameters optimized for this specific expression.")
