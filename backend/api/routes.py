import asyncio
import os
import logging
from typing import Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect

from backend.config import load_config
from backend.orchestrator import OptimizerOrchestrator
from backend.models.schemas import (
    OptimizationRequest,
    OptimizationResponse,
    TrafficUpdateRequest,
    TrafficUpdateResponse,
    SystemStatusResponse,
)
from backend.api.websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Global orchestrator instance (for simplicity in this prototype)
_orchestrator: OptimizerOrchestrator | None = None
_is_running: bool = False
_current_scenario: str = "baseline"

def get_orchestrator() -> OptimizerOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        cfg = load_config()
        # Ensure scenarios directory exists
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "scenarios")
        os.makedirs(data_dir, exist_ok=True)
        # Create baseline if it doesn't exist
        baseline_path = os.path.join(data_dir, "baseline.json")
        if not os.path.exists(baseline_path):
            import json
            with open(baseline_path, 'w') as f:
                json.dump({}, f)
                
        _orchestrator = OptimizerOrchestrator(
            config=cfg
        )
        _orchestrator.data_dir = data_dir
        _orchestrator.setup_problem(scenario_file=baseline_path)
    return _orchestrator

async def run_optimization_task(iterations: int):
    global _is_running
    _is_running = True
    orch = get_orchestrator()
    
    if orch.qpso is None:
        orch._init_optimizer_components()
    
    try:
        for i in range(iterations):
            if not _is_running:
                break
                
            # Perform one iteration of QPSO (which includes local search/GLS/levy)
            orch.qpso.step()
            
            # Get best route
            best_fitness = float(orch.qpso.gbest_fitness)
            
            # Decode for visualization
            split_result = orch.qpso.gbest_split
            
            # Broadcast update
            await manager.broadcast({
                "type": "iteration_update",
                "iteration": orch.qpso.iteration,
                "best_fitness": best_fitness,
                "routes": split_result.routes,
                "cost_details": {
                    "total_cost": split_result.total_cost,
                    "travel_time": sum(orch.fitness_evaluator._route_cost(r, orch.cost_matrix_manager.matrix) for r in split_result.routes)
                },
                "elapsed_ms": orch.qpso.convergence_history[-1].elapsed_ms if orch.qpso.convergence_history else 0.0
            })
            
            # Yield control back to event loop to allow other requests (like traffic updates) to process
            await asyncio.sleep(0.05)
            
    except Exception as e:
        logger.error(f"Optimization task failed: {e}")
    finally:
        _is_running = False
        await manager.broadcast({"type": "status", "is_running": False})

@router.post("/start", response_model=OptimizationResponse)
async def start_optimization(req: OptimizationRequest, background_tasks: BackgroundTasks):
    global _is_running, _current_scenario
    if _is_running:
        raise HTTPException(status_code=400, detail="Optimization already running")
        
    orch = get_orchestrator()
    
    if req.scenario_id:
        scenario_path = os.path.join(orch.data_dir, f"{req.scenario_id}.json")
        if os.path.exists(scenario_path):
            orch.update_traffic_scenario(scenario_path)
            _current_scenario = req.scenario_id
        else:
            raise HTTPException(status_code=404, detail=f"Scenario {req.scenario_id} not found")
            
    background_tasks.add_task(run_optimization_task, req.iterations)
    return OptimizationResponse(status="success", message="Optimization started")

@router.post("/stop", response_model=OptimizationResponse)
async def stop_optimization():
    global _is_running
    if not _is_running:
        return OptimizationResponse(status="success", message="Optimization is not running")
        
    _is_running = False
    return OptimizationResponse(status="success", message="Optimization stopped")

@router.post("/traffic", response_model=TrafficUpdateResponse)
async def update_traffic(req: TrafficUpdateRequest):
    global _current_scenario
    orch = get_orchestrator()
    scenario_path = os.path.join(orch.data_dir, f"{req.scenario_id}.json")
    
    if not os.path.exists(scenario_path):
        raise HTTPException(status_code=404, detail=f"Scenario {req.scenario_id} not found")
        
    orch.update_traffic_scenario(scenario_path)
    _current_scenario = req.scenario_id
    
    # Broadcast traffic change event
    import json
    with open(scenario_path, 'r') as f:
        scenario_data = json.load(f)
        
    congested_edges = list(orch.traffic_manager.affected_edges)
        
    asyncio.create_task(manager.broadcast({
        "type": "traffic_update",
        "scenario_id": req.scenario_id,
        "affected_edges": scenario_data,
        "congested_edges": congested_edges
    }))
    
    return TrafficUpdateResponse(
        status="success", 
        message=f"Traffic scenario {req.scenario_id} applied",
        scenario_id=req.scenario_id,
        affected_edges=len(scenario_data)
    )

@router.get("/status", response_model=SystemStatusResponse)
async def get_status():
    global _is_running, _current_scenario
    
    if _orchestrator is None:
        return SystemStatusResponse(
            is_running=False,
            current_iteration=0,
            best_cost=None,
            scenario_id=None
        )
        
    orch = _orchestrator
    best_cost = None
    if orch.qpso and len(orch.qpso.gbest_fitness) > 0:
        best_cost = float(orch.qpso.gbest_fitness.min())
        
    return SystemStatusResponse(
        is_running=_is_running,
        current_iteration=orch.qpso.iteration if orch.qpso else 0,
        best_cost=best_cost,
        scenario_id=_current_scenario
    )

@router.get("/nodes")
async def get_nodes():
    orch = get_orchestrator()
    nodes = []
    for node_id, data in orch.graph.nodes(data=True):
        nodes.append({
            "id": node_id,
            "x": data.get("x", 0),
            "y": data.get("y", 0),
            "is_depot": node_id == 0
        })
    return {"nodes": nodes}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open, client might send pings
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
