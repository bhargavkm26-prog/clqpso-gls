"""
Google OR-Tools CVRP Reference Solver.

Provides a research-grade baseline CVRP solver using Google OR-Tools.
"""

import time
import numpy as np
from typing import Any
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from backend.benchmarks.instance_loader import CVRPInstance
from backend.benchmarks.reproducibility import validate_solution

def solve_with_ortools(
    instance: CVRPInstance,
    time_limit_seconds: int = 5,
    num_vehicles: int = None
) -> dict[str, Any]:
    """Solve a CVRP instance using Google OR-Tools.
    
    Args:
        instance: Loaded CVRPInstance object.
        time_limit_seconds: Max solver runtime in seconds.
        num_vehicles: Number of vehicles available (defaults to instance.vehicles * 2 for safety).
        
    Returns:
        Structured result dictionary.
    """
    t0 = time.perf_counter()

    dimension = instance.dimension
    cost_matrix = instance.cost_matrix
    demands = instance.all_demands  # length dimension, index 0 is depot
    capacity = int(instance.vehicle_capacity)

    if num_vehicles is None:
        num_vehicles = max(instance.vehicles, int(np.ceil(np.sum(demands) / capacity)) + 2)

    # 1. Index Manager & Routing Model
    manager = pywrapcp.RoutingIndexManager(dimension, num_vehicles, instance.depot_index)
    routing = pywrapcp.RoutingModel(manager)

    # 2. Transit Callback (Distance) - scale by 100 for integer solver precision
    SCALE = 100.0
    int_cost_matrix = (cost_matrix * SCALE).astype(np.int64)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int_cost_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # 3. Capacity Dimension Callback
    int_demands = demands.astype(np.int64)
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return int_demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        [capacity] * num_vehicles,  # vehicle capacity
        True,  # start cumulative to zero
        "Capacity"
    )

    # 4. Search Parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = time_limit_seconds

    # 5. Solve
    solution = routing.SolveWithParameters(search_parameters)
    t1 = time.perf_counter()
    runtime = t1 - t0

    if not solution:
        return {
            "algorithm": "OR-Tools",
            "instance": instance.name,
            "seed": 0,
            "best_fitness": float('inf'),
            "distance": float('inf'),
            "travel_time": float('inf'),
            "congestion_cost": 0.0,
            "vehicle_count": 0,
            "runtime_seconds": runtime,
            "iterations": 0,
            "convergence": [],
            "routes": [],
            "parameters": {"time_limit_seconds": time_limit_seconds},
            "status": "NO_SOLUTION_FOUND",
            "valid": False,
            "errors": ["OR-Tools failed to find a feasible solution."]
        }

    # 6. Extract Routes
    routes = []
    total_distance_int = 0
    used_vehicles = 0

    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        route_nodes = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:  # exclude depot
                # Convert 1-based node (1..N) to 0-based customer index (0..N-1)
                route_nodes.append(node - 1)
            index = solution.Value(routing.NextVar(index))
        
        if route_nodes:
            routes.append(route_nodes)
            used_vehicles += 1
            
    total_distance = float(solution.ObjectiveValue()) / SCALE

    # 7. Solution Validation
    val = validate_solution(
        routes=routes,
        demands=instance.demands,
        vehicle_capacity=instance.vehicle_capacity,
        num_customers=instance.num_customers,
        cost_matrix=cost_matrix,
        reported_fitness=total_distance
    )

    status_str = "OPTIMAL" if routing.status() == 1 else "FEASIBLE"

    return {
        "algorithm": "OR-Tools",
        "instance": instance.name,
        "seed": 0,
        "best_fitness": total_distance,
        "distance": total_distance,
        "travel_time": total_distance,
        "congestion_cost": 0.0,
        "vehicle_count": used_vehicles,
        "runtime_seconds": runtime,
        "iterations": 0,
        "convergence": [{"iteration": 1, "best_fitness": total_distance}],
        "routes": routes,
        "parameters": {
            "time_limit_seconds": time_limit_seconds,
            "metaheuristic": "GUIDED_LOCAL_SEARCH"
        },
        "status": status_str,
        "valid": val["valid"],
        "errors": val["errors"]
    }
