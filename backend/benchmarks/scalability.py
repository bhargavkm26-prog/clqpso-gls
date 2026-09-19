"""
Scalability Experiment Module.

Evaluates performance (runtime, fitness, vehicle count) across scaling customer
sizes from 32 to 200 nodes.
"""

import time
import numpy as np
from pathlib import Path
from typing import Any
from backend.benchmarks.instance_loader import load_cvrp_instance, CVRPInstance
from backend.orchestrator import OptimizerOrchestrator
from backend.benchmarks.reproducibility import validate_solution

RESULTS_DIR = Path(__file__).resolve().parent / "results" / "scalability"

def generate_synthetic_cvrp(num_customers: int, seed: int = 42) -> CVRPInstance:
    """Generate a reproducible synthetic CVRP instance."""
    rng = np.random.RandomState(seed)
    dimension = num_customers + 1
    coords = rng.uniform(0, 100, (dimension, 2))
    demands = rng.randint(5, 25, num_customers).astype(np.float64)
    all_demands = np.zeros(dimension, dtype=np.float64)
    all_demands[1:] = demands

    cost_matrix = np.zeros((dimension, dimension), dtype=np.float64)
    for i in range(dimension):
        for j in range(dimension):
            if i != j:
                cost_matrix[i, j] = np.linalg.norm(coords[i] - coords[j])

    return CVRPInstance(
        name=f"Synthetic-{num_customers}",
        dimension=dimension,
        num_customers=num_customers,
        vehicle_capacity=100.0,
        vehicles=int(np.ceil(np.sum(demands) / 100.0)),
        depot_index=0,
        depot_coord=(coords[0, 0], coords[0, 1]),
        coords=coords,
        demands=demands,
        all_demands=all_demands,
        cost_matrix=cost_matrix
    )

def run_scalability_experiment(customer_counts: list[int] = None, seed: int = 42) -> list[dict[str, Any]]:
    """Run scalability benchmark across specified customer sizes."""
    if customer_counts is None:
        customer_counts = [32, 53, 80, 100, 150, 200]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for n in customer_counts:
        # Load standard instance if available, else synthetic
        if n == 32:
            instance = load_cvrp_instance("A-n32-k5")
        elif n == 53:
            instance = load_cvrp_instance("A-n53-k7")
        elif n == 80:
            instance = load_cvrp_instance("A-n80-k10")
        else:
            instance = generate_synthetic_cvrp(n, seed)

        config = {
            "optimizer": {
                "population_size": 128,
                "max_iterations": 150,
                "seed": seed
            }
        }

        t0 = time.perf_counter()
        orchestrator = OptimizerOrchestrator(config)
        orchestrator.rng = np.random.RandomState(seed)
        orchestrator.setup_custom_instance(instance.cost_matrix, instance.demands, instance.vehicle_capacity)

        opt_res = orchestrator.run()
        t1 = time.perf_counter()

        val = validate_solution(
            routes=opt_res.best_routes,
            demands=instance.demands,
            vehicle_capacity=instance.vehicle_capacity,
            num_customers=instance.num_customers,
            cost_matrix=instance.cost_matrix,
            reported_fitness=opt_res.best_fitness
        )

        res_dict = {
            "num_customers": n,
            "instance": instance.name,
            "best_fitness": float(opt_res.best_fitness),
            "vehicle_count": len(opt_res.best_routes),
            "runtime_seconds": float(t1 - t0),
            "valid": val["valid"]
        }
        results.append(res_dict)

    return results
