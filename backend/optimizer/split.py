"""
Prins Split Decoder — O(n²) baseline DP.

Partitions a giant customer tour into feasible vehicle routes
using dynamic programming on a shortest-path DAG.

Blueprint reference: §10 Step 2 (Prins Split)

Sources:
    - Prins (2004), "A Simple and Effective Evolutionary Algorithm for the
      Vehicle Routing Problem", Computers & Operations Research.

Potential upgrade (not yet implemented):
    - Vidal (2015), "Split Algorithm in O(n) for the Capacitated Vehicle
      Routing Problem", Technical Note.  The O(n) variant uses a
      dominance-based queue to prune the inner loop.  The current
      implementation keeps the simpler O(n²) nested-loop DP which is
      correct and fast enough for instances up to ~200 customers.

The Split decoder constructs a DAG where:
    - Nodes 0..n represent positions in the giant tour
    - Arc (i, j) represents serving customers tour[i+1..j] on one route
    - Arc cost = depot→tour[i+1] + sum(tour[k]→tour[k+1]) + tour[j]→depot
    - Arc is feasible only if total demand of segment ≤ vehicle capacity

The shortest path 0→n gives the optimal partition.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np


class SplitResult(NamedTuple):
    """Result of the Split decoder.

    Attributes:
        routes: List of routes, each route is a list of customer indices
            (0-based, NOT including depot). The depot is implicitly
            at the start and end of each route.
        route_costs: Cost of each individual route.
        total_cost: Total cost across all routes.
        feasible: Whether all routes satisfy capacity constraints.
        num_vehicles: Number of routes/vehicles used.
    """
    routes: list[list[int]]
    route_costs: list[float]
    total_cost: float
    feasible: bool
    num_vehicles: int


def split(
    giant_tour: np.ndarray,
    cost_matrix: np.ndarray,
    demands: np.ndarray,
    vehicle_capacity: float,
    max_vehicles: int | None = None,
) -> SplitResult:
    """Split a giant tour into feasible vehicle routes.

    Implements the baseline Prins Split DP with O(n²) complexity
    (one outer loop over starting positions, one inner loop bounded
    by vehicle capacity).  No dominance-based pruning is applied.

    The cost matrix uses stop indices where:
        - Index 0 = depot
        - Index 1..n = customers (in their original numbering)

    The giant_tour contains customer indices 0..n-1 which map to
    stop indices 1..n in the cost matrix.

    **Limitation:** ``max_vehicles`` is enforced as a post-check on the
    unconstrained DP result.  The DP does not explore alternative
    partitions that might satisfy the fleet limit at higher cost.
    A correct integration would require a 2D DP state ``dp[j][k]``
    (position × route count), deferred to a future upgrade.

    Args:
        giant_tour: 1D array of customer indices (0-based) in visitation order.
            Shape: (n_customers,)
        cost_matrix: 2D array of shape (n_stops, n_stops) where
            index 0 is depot, indices 1..n are customers.
        demands: 1D array of customer demands, shape (n_customers,).
            demands[i] is the demand of customer i.
        vehicle_capacity: Maximum capacity per vehicle.
        max_vehicles: Maximum number of vehicles (None = unlimited).

    Returns:
        SplitResult with optimal route partition.
    """
    n = len(giant_tour)

    if n == 0:
        return SplitResult(
            routes=[], route_costs=[], total_cost=0.0,
            feasible=True, num_vehicles=0
        )

    # Map customer indices to stop indices (customer 0 → stop 1, etc.)
    # stop_order[k] gives the stop index for the k-th customer in the tour
    stop_order = giant_tour + 1  # shift to 1-based stop indices

    DEPOT = 0
    INF = float("inf")

    # DP arrays
    # dp[j] = minimum cost to serve customers tour[0..j-1]
    dp = np.full(n + 1, INF, dtype=np.float64)
    dp[0] = 0.0

    # predecessor[j] = the split point that achieves dp[j]
    predecessor = np.full(n + 1, -1, dtype=np.int64)

    # O(n²) nested-loop DP
    for i in range(n):
        if dp[i] >= INF:
            continue

        # Try extending a route starting after position i
        route_load = 0.0
        route_cost = 0.0

        for j in range(i, n):
            # Add customer at position j to the current route
            cust_stop = int(stop_order[j])
            cust_demand = float(demands[giant_tour[j]])

            route_load += cust_demand

            # Check capacity constraint
            if route_load > vehicle_capacity:
                break  # Cannot extend further — all subsequent will also fail

            # Compute route cost: depot → first + ... + last → depot
            if j == i:
                # First customer in route: depot → cust
                route_cost = float(cost_matrix[DEPOT, cust_stop])
            else:
                # Add link from previous customer to this one
                prev_stop = int(stop_order[j - 1])
                route_cost += float(cost_matrix[prev_stop, cust_stop])

            # Add return to depot
            total_route_cost = route_cost + float(cost_matrix[cust_stop, DEPOT])

            # Check if this split is better
            candidate = dp[i] + total_route_cost
            if candidate < dp[j + 1]:
                dp[j + 1] = candidate
                predecessor[j + 1] = i

    # Reconstruct routes by backtracking through predecessors
    if dp[n] >= INF:
        # No feasible partition found
        return SplitResult(
            routes=[[int(c) for c in giant_tour]],
            route_costs=[INF],
            total_cost=INF,
            feasible=False,
            num_vehicles=1,
        )

    # Backtrack to find split points
    split_points = []
    pos = n
    while pos > 0:
        prev = int(predecessor[pos])
        split_points.append((prev, pos))
        pos = prev

    split_points.reverse()

    # Extract routes
    routes = []
    route_costs = []

    for start, end in split_points:
        route_customers = [int(giant_tour[k]) for k in range(start, end)]
        routes.append(route_customers)

        # Compute route cost
        stops = [DEPOT] + [int(stop_order[k]) for k in range(start, end)] + [DEPOT]
        rc = sum(
            float(cost_matrix[stops[k], stops[k + 1]])
            for k in range(len(stops) - 1)
        )
        route_costs.append(rc)

    total_cost = sum(route_costs)
    num_vehicles = len(routes)

    # Check max vehicles constraint
    feasible = True
    if max_vehicles is not None and num_vehicles > max_vehicles:
        feasible = False

    return SplitResult(
        routes=routes,
        route_costs=route_costs,
        total_cost=total_cost,
        feasible=feasible,
        num_vehicles=num_vehicles,
    )


def evaluate_routes(
    routes: list[list[int]],
    cost_matrix: np.ndarray,
    demands: np.ndarray,
    vehicle_capacity: float,
) -> tuple[float, list[float], list[float], bool]:
    """Evaluate a set of routes for cost and feasibility.

    Args:
        routes: List of routes (each route = list of customer indices).
        cost_matrix: Stop-to-stop cost matrix (index 0 = depot).
        demands: Customer demands array.
        vehicle_capacity: Maximum capacity per vehicle.

    Returns:
        Tuple of (total_cost, route_costs, route_loads, all_feasible).
    """
    DEPOT = 0
    total_cost = 0.0
    route_costs = []
    route_loads = []
    all_feasible = True

    for route in routes:
        if not route:
            continue

        # Build stop sequence: depot → customers → depot
        stops = [DEPOT] + [c + 1 for c in route] + [DEPOT]

        # Route cost
        rc = sum(
            float(cost_matrix[stops[k], stops[k + 1]])
            for k in range(len(stops) - 1)
        )
        route_costs.append(rc)
        total_cost += rc

        # Route load
        load = sum(float(demands[c]) for c in route)
        route_loads.append(load)

        if load > vehicle_capacity:
            all_feasible = False

    return total_cost, route_costs, route_loads, all_feasible
