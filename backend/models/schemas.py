from typing import Any
from pydantic import BaseModel, Field

class OptimizationRequest(BaseModel):
    iterations: int = Field(100, description="Number of iterations to run")
    scenario_id: str | None = Field(None, description="Traffic scenario to apply before starting")
    
class OptimizationResponse(BaseModel):
    status: str
    message: str
    
class TrafficUpdateRequest(BaseModel):
    scenario_id: str = Field(..., description="ID of the traffic scenario to apply (e.g., 'disruption', 'recovery')")
    
class TrafficUpdateResponse(BaseModel):
    status: str
    message: str
    scenario_id: str
    affected_edges: int

class SystemStatusResponse(BaseModel):
    is_running: bool
    current_iteration: int
    best_cost: float | None
    scenario_id: str | None
