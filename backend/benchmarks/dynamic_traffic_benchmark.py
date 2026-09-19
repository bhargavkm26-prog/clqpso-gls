"""
Category B — Dynamic Traffic Re-Routing Benchmark Engine.

Dedicated benchmark evaluating real-time re-optimization across sequential
traffic scenarios (baseline -> moderate -> disruption -> recovery) on the
Bangalore urban road network.
"""

import time
import json
from pathlib import Path
from typing import Any
from backend.orchestrator import OptimizerOrchestrator

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "traffic_scenarios"

def run_dynamic_traffic_benchmark(seed: int = 42) -> dict[str, Any]:
    """Execute dynamic traffic transition benchmark."""
    config = {
        "optimizer": {
            "population_size": 64,
            "max_iterations": 50,
            "seed": seed
        },
        "vrp": {
            "num_customers": 25,
            "vehicle_capacity": 100.0
        },
        "graph": {
            "mode": "synthetic",
            "grid_size": 10
        }
    }

    orchestrator = OptimizerOrchestrator(config)
    orchestrator.setup_problem(
        num_customers=config['vrp']['num_customers'],
        scenario_file=str(SCENARIOS_DIR / "baseline.json")
    )

    scenarios = ["baseline", "moderate", "disruption", "recovery"]
    scenario_results = []
    prev_fitness = None

    for scenario_id in scenarios:
        scenario_path = SCENARIOS_DIR / f"{scenario_id}.json"
        
        t0 = time.perf_counter()
        if scenario_id != "baseline" and scenario_path.exists():
            orchestrator.update_traffic_scenario(scenario_path)

        res = orchestrator.run()
        t1 = time.perf_counter()

        cost_diff = (res.best_fitness - prev_fitness) if prev_fitness is not None else 0.0
        prev_fitness = res.best_fitness

        scenario_results.append({
            "scenario": scenario_id,
            "best_fitness": float(res.best_fitness),
            "fitness_change": float(cost_diff),
            "reoptimization_time_seconds": float(t1 - t0),
            "vehicle_count": len(res.best_routes),
            "routes": res.best_routes
        })

    return {
        "category": "Bangalore Dynamic Traffic",
        "seed": seed,
        "scenarios": scenario_results
    }
