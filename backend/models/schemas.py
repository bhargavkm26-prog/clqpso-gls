from typing import Any
from pydantic import BaseModel, Field

class OptimizationRequest(BaseModel):
    iterations: int = Field(100, description="Number of iterations to run")
    scenario_id: str | None = Field(None, description="Traffic scenario to apply before starting")
    depot: tuple[float, float] | None = Field(None, description="(lat, lng) of depot")
    customers: list[tuple[float, float]] | None = Field(None, description="List of (lat, lng) for customers")
    vehicle_capacity: float | None = Field(None, description="Capacity per vehicle")
    max_vehicles: int | None = Field(None, description="Maximum number of vehicles")
    
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

class SettingsRequest(BaseModel):
    alpha_bounds: list[float] | None = None
    max_iterations: int | None = None
    population_size: int | None = None
    use_gls: bool | None = None
    use_swap_star: bool | None = None

class ModeRequest(BaseModel):
    mode: str = Field(..., description="VRP or SHORTEST_PATH")

class BenchmarkRecord(BaseModel):
    name: str
    mean_cost: float
    std: float
    best_cost: float
    runtime_s: float
    gap_to_bks: float
    status: str
