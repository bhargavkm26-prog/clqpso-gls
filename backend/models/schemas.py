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

class CompareRequest(BaseModel):
    source_id: int | str = Field(0, description="Source node ID")
    intermediate_stops: list[int | str] = Field(default_factory=list, description="Intermediate stop IDs")
    traffic_mode: str = Field("peak", description="Traffic mode / scenario")
    iterations: int = Field(100, description="Iterations for iterative algorithms")

class AlgorithmResult(BaseModel):
    algorithm: str
    travel_time_min: float
    distance_km: float
    runtime_ms: float
    cost: float | None = None
    iterations: int | None = None
    is_best: bool = False
    history: list[float] = Field(default_factory=list)

class CompareResponse(BaseModel):
    status: str
    algorithms: list[AlgorithmResult]

