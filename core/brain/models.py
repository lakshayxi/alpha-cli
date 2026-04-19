from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class SimulationResult(BaseModel):
    alpha_id: str
    expression: str
    region: str
    universe: str
    sharpe: float = 0.0
    fitness: float = 0.0
    turnover: float = 0.0
    returns: float = 0.0
    drawdown: float = 0.0
    margin: float = 0.0
    status: str = "PENDING"
    error_message: Optional[str] = None
    settings: Dict[str, Any]
    timestamp: float
