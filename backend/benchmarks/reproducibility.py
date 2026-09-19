"""
Reproducibility and Solution Validation Engine.

Ensures every benchmark run has tracked seeds, parameters, and rigorous
solution feasibility validation before accepting results into statistics.
"""

from typing import Any
import numpy as np

def validate_solution(
    routes: list[list[int]],
    demands: np.ndarray,
    vehicle_capacity: float,
    num_customers: int,
    cost_matrix: np.ndarray,
    reported_fitness: float,
    tolerance: float = 1e-2
) -> dict[str, Any]:
    """Validate CVRP solution for feasibility and objective consistency.
    
    Args:
        routes: List of routes, each route is a list of customer indices (0-based: 0..num_customers-1).
        demands: Customer demands array (length num_customers).
        vehicle_capacity: Maximum capacity per vehicle.
        num_customers: Total expected number of customers.
        cost_matrix: Stop-to-stop distance matrix (shape N+1 x N+1).
        reported_fitness: Fitness value reported by optimizer.
        tolerance: Acceptable difference between recalculated cost and reported cost.
        
    Returns:
        Dict with 'valid': bool, 'errors': list[str], 'recalculated_cost': float.
    """
    errors = []

    # 1. Customer Coverage
    all_served = []
    for r in routes:
        all_served.extend(r)

    served_set = set(all_served)
    expected_set = set(range(num_customers))

    if len(all_served) != len(served_set):
        duplicates = [x for x in served_set if all_served.count(x) > 1]
        errors.append(f"Duplicate customer assignment found: {duplicates}")

    missing = expected_set - served_set
    if missing:
        errors.append(f"Missing customer assignments: {sorted(list(missing))}")

    # 2. Capacity Constraint
    for r_idx, route in enumerate(routes):
        route_demand = sum(demands[c] for c in route)
        if route_demand > vehicle_capacity + 1e-5:
            errors.append(
                f"Route {r_idx+1} capacity violation: demand {route_demand:.1f} > capacity {vehicle_capacity}"
            )

    # 3. Recalculate Total Distance
    recalculated_cost = 0.0
    for route in routes:
        if not route:
            continue
        # Depot (0 in matrix) -> first customer (+1 for matrix offset)
        recalculated_cost += cost_matrix[0, route[0] + 1]
        for i in range(len(route) - 1):
            recalculated_cost += cost_matrix[route[i] + 1, route[i + 1] + 1]
        # last customer -> Depot (0 in matrix)
        recalculated_cost += cost_matrix[route[-1] + 1, 0]

    # 4. Objective Consistency (if distance-only fitness)
    if reported_fitness is not None and reported_fitness > 0:
        diff = abs(recalculated_cost - reported_fitness)
        if diff > tolerance and abs(diff / (recalculated_cost + 1e-9)) > 0.05:
            errors.append(
                f"Cost mismatch: recalculated={recalculated_cost:.2f}, reported={reported_fitness:.2f} (diff={diff:.2f})"
            )

    is_valid = (len(errors) == 0)
    return {
        "valid": is_valid,
        "errors": errors,
        "recalculated_cost": float(recalculated_cost)
    }

def get_run_metadata(seed: int, population_size: int, iterations: int, extra_params: dict[str, Any] = None) -> dict[str, Any]:
    """Build standardized reproducibility metadata dictionary."""
    meta = {
        "seed": seed,
        "population_size": population_size,
        "iterations": iterations,
        "numpy_version": np.__version__,
    }
    if extra_params:
        meta.update(extra_params)
    return meta
