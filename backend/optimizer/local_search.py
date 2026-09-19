"""
Local Search Operators (2-opt, Or-opt, SWAP*).

Blueprint reference: §19 Tier 1 Operators, §20 Tier 2 Operators (SWAP*).

Operators are applied to giant tours (customer sequences) or individual
routes, evaluated using the penalty-augmented cost matrix if GLS is active.
"""

from __future__ import annotations

import copy
from typing import Any

import numpy as np

from backend.optimizer.split import SplitResult, split


def two_opt_giant_tour(
    giant_tour: np.ndarray,
    cost_matrix: np.ndarray,
    max_iterations: int = 10,
) -> tuple[np.ndarray, bool]:
    """Apply 2-opt local search on a giant tour.

    Reverses sub-segments of the tour if it reduces the total distance
    between consecutive customers. This is an intra-route/sequencing
    operator.

    Args:
        giant_tour: 1D array of customer indices (0-based).
        cost_matrix: Stop-to-stop cost matrix (index 0 = depot).
        max_iterations: Maximum passes without improvement.

    Returns:
        Tuple of (improved_tour, improved).
    """
    n = len(giant_tour)
    if n <= 2:
        return giant_tour.copy(), False

    tour = giant_tour.copy()
    improved_overall = False

    for _ in range(max_iterations):
        improved = False
        for i in range(n - 2):
            for j in range(i + 2, n):
                # We are checking if reversing tour[i+1...j] improves cost
                # Current edges: (i -> i+1) and (j -> j+1)
                # New edges:     (i -> j)   and (i+1 -> j+1)

                c_i = tour[i] + 1      # +1 because index 0 is depot
                c_i1 = tour[i + 1] + 1
                c_j = tour[j] + 1

                # If j+1 is out of bounds, we consider wrap-around to depot
                if j + 1 < n:
                    c_j1 = tour[j + 1] + 1
                else:
                    # In a giant tour, the ends technically connect to depot
                    # but for pure sequencing, we just compare the segments
                    c_j1 = 0  # Depot

                # Current cost of the two edges being broken
                current_cost = cost_matrix[c_i, c_i1]
                if j + 1 < n:
                    current_cost += cost_matrix[c_j, c_j1]
                else:
                    current_cost += cost_matrix[c_j, 0]

                # New cost of the two new edges
                new_cost = cost_matrix[c_i, c_j]
                if j + 1 < n:
                    new_cost += cost_matrix[c_i1, c_j1]
                else:
                    new_cost += cost_matrix[c_i1, 0]

                # Check if new cost is strictly better (with tolerance)
                if new_cost < current_cost - 1e-6:
                    # Reverse the segment in place
                    tour[i + 1 : j + 1] = tour[i + 1 : j + 1][::-1]
                    improved = True
                    improved_overall = True

        if not improved:
            break

    return tour, improved_overall


def or_opt_giant_tour(
    giant_tour: np.ndarray,
    cost_matrix: np.ndarray,
    max_segment_length: int = 3,
    max_iterations: int = 10,
) -> tuple[np.ndarray, bool]:
    """Apply Or-opt local search on a giant tour.

    Moves contiguous segments of length 1, 2, or 3 to another position
    in the tour if it reduces total cost.

    Args:
        giant_tour: 1D array of customer indices (0-based).
        cost_matrix: Stop-to-stop cost matrix.
        max_segment_length: Max length of segment to relocate (usually 3).
        max_iterations: Maximum passes without improvement.

    Returns:
        Tuple of (improved_tour, improved).
    """
    n = len(giant_tour)
    if n <= 3:
        return giant_tour.copy(), False

    tour = giant_tour.copy()
    improved_overall = False

    for _ in range(max_iterations):
        improved = False
        
        # Try all segment lengths from max down to 1
        for L in range(max_segment_length, 0, -1):
            for i in range(n - L + 1):
                # Segment is tour[i : i+L]
                for j in range(n + 1):
                    # Destination index j (can't insert inside or right next to segment)
                    if j >= i and j <= i + L:
                        continue

                    # The segment to move
                    segment = tour[i : i + L]
                    
                    # Create the new tour
                    # 1. Remove segment
                    temp_tour = np.concatenate([tour[:i], tour[i + L:]])
                    
                    # 2. Adjust insertion point j
                    insert_idx = j if j <= i else j - L
                    
                    # 3. Insert segment
                    new_tour = np.insert(temp_tour, insert_idx, segment)
                    
                    # Cost evaluation (simplified: evaluate full tour cost)
                    # For optimization, we should only evaluate delta cost,
                    # but NumPy is fast enough for small n.
                    if _eval_tour_cost(new_tour, cost_matrix) < _eval_tour_cost(tour, cost_matrix) - 1e-6:
                        tour = new_tour
                        improved = True
                        improved_overall = True
                        break  # Break inner loops, restart search
                
                if improved:
                    break
            
            if improved:
                break
                
        if not improved:
            break

    return tour, improved_overall


def _eval_tour_cost(tour: np.ndarray, cost_matrix: np.ndarray) -> float:
    """Evaluate the sequential distance of a giant tour."""
    cost = 0.0
    stops = tour + 1  # 0 is depot
    for k in range(len(stops) - 1):
        cost += cost_matrix[stops[k], stops[k + 1]]
    return cost


def swap_star(
    split_result: SplitResult,
    cost_matrix: np.ndarray,
    demands: np.ndarray,
    vehicle_capacity: float,
) -> tuple[SplitResult, bool]:
    """Apply the SWAP* inter-route operator.

    Upgrade 1: SWAP* (Vidal 2022).
    Exchanges customers between different routes without preserving their
    exact insertion points. It finds the best insertion point in the target
    route for each swapped customer, decoupling extraction and insertion.

    This is an inter-route operator that explores neighborhoods inaccessible
    to 2-opt and Or-opt.

    Args:
        split_result: Current feasible routes.
        cost_matrix: Stop-to-stop cost matrix.
        demands: Customer demands.
        vehicle_capacity: Maximum capacity.

    Returns:
        Tuple of (new_split_result, improved).
    """
    if split_result.num_vehicles <= 1:
        return split_result, False

    routes = copy.deepcopy(split_result.routes)
    route_costs = list(split_result.route_costs)
    route_loads = [sum(demands[c] for c in r) for r in routes]
    total_cost = split_result.total_cost
    improved_overall = False

    # Try swapping one customer from Route A with one from Route B
    for i in range(len(routes)):
        for j in range(i + 1, len(routes)):
            route_a = routes[i]
            route_b = routes[j]
            load_a = route_loads[i]
            load_b = route_loads[j]
            
            if not route_a or not route_b:
                continue
                
            improved_in_pair = True
            iter_count = 0
            while improved_in_pair and iter_count < 20:
                iter_count += 1
                improved_in_pair = False
                
                best_delta = 0.0
                best_swap = None
                
                # Check all pairs (c_a, c_b)
                for idx_a, c_a in enumerate(route_a):
                    for idx_b, c_b in enumerate(route_b):
                        dem_a = demands[c_a]
                        dem_b = demands[c_b]
                        
                        # Check capacity if we swapped them
                        new_load_a = load_a - dem_a + dem_b
                        new_load_b = load_b - dem_b + dem_a
                        
                        if new_load_a > vehicle_capacity or new_load_b > vehicle_capacity:
                            continue
                            
                        # Evaluate best insertion of c_b into Route A (without c_a)
                        temp_route_a = route_a[:idx_a] + route_a[idx_a+1:]
                        delta_a, best_pos_a = _best_insertion(temp_route_a, c_b, cost_matrix)
                        # The cost removed by taking c_a out
                        rem_a = _removal_cost(route_a, idx_a, cost_matrix)
                        
                        # Evaluate best insertion of c_a into Route B (without c_b)
                        temp_route_b = route_b[:idx_b] + route_b[idx_b+1:]
                        delta_b, best_pos_b = _best_insertion(temp_route_b, c_a, cost_matrix)
                        # The cost removed by taking c_b out
                        rem_b = _removal_cost(route_b, idx_b, cost_matrix)
                        
                        # Net change in cost across both routes
                        # (Cost added) - (Cost removed)
                        net_delta = (delta_a - rem_a) + (delta_b - rem_b)
                        
                        if net_delta < best_delta - 1e-6:
                            best_delta = net_delta
                            best_swap = (idx_a, c_a, best_pos_a, idx_b, c_b, best_pos_b)
                
                # Apply the best swap found for this pair of routes
                if best_swap:
                    idx_a, c_a, pos_a, idx_b, c_b, pos_b = best_swap
                    
                    # Perform swap
                    temp_a = route_a[:idx_a] + route_a[idx_a+1:]
                    temp_a.insert(pos_a, c_b)
                    
                    temp_b = route_b[:idx_b] + route_b[idx_b+1:]
                    temp_b.insert(pos_b, c_a)
                    
                    routes[i] = temp_a
                    routes[j] = temp_b
                    
                    # Update loads and costs
                    route_loads[i] = load_a - demands[c_a] + demands[c_b]
                    route_loads[j] = load_b - demands[c_b] + demands[c_a]
                    load_a = route_loads[i]
                    load_b = route_loads[j]
                    
                    # Route cost requires full evaluation for accuracy
                    route_costs[i] = _route_cost(routes[i], cost_matrix)
                    route_costs[j] = _route_cost(routes[j], cost_matrix)
                    
                    improved_in_pair = True
                    improved_overall = True

    if improved_overall:
        # We need to flatten the routes back to a giant tour and re-split
        # to ensure the SplitResult object is perfectly consistent and
        # any implicit DP benefits are realized.
        giant_tour = []
        for r in routes:
            giant_tour.extend(r)
            
        new_result = split(np.array(giant_tour), cost_matrix, demands, vehicle_capacity)
        return new_result, True

    return split_result, False


def _removal_cost(route: list[int], idx: int, cost_matrix: np.ndarray) -> float:
    """Calculate the cost reduction from removing route[idx]."""
    DEPOT = 0
    prev_node = route[idx - 1] + 1 if idx > 0 else DEPOT
    curr_node = route[idx] + 1
    next_node = route[idx + 1] + 1 if idx < len(route) - 1 else DEPOT
    
    current_cost = cost_matrix[prev_node, curr_node] + cost_matrix[curr_node, next_node]
    new_cost = cost_matrix[prev_node, next_node]
    
    return current_cost - new_cost


def _best_insertion(route: list[int], customer: int, cost_matrix: np.ndarray) -> tuple[float, int]:
    """Find the best insertion position and its delta cost."""
    DEPOT = 0
    c_node = customer + 1
    
    if not route:
        return cost_matrix[DEPOT, c_node] + cost_matrix[c_node, DEPOT], 0
        
    best_delta = float('inf')
    best_pos = -1
    
    for i in range(len(route) + 1):
        prev_node = route[i - 1] + 1 if i > 0 else DEPOT
        next_node = route[i] + 1 if i < len(route) else DEPOT
        
        # Breaking prev -> next, adding prev -> c -> next
        broken_cost = cost_matrix[prev_node, next_node]
        added_cost = cost_matrix[prev_node, c_node] + cost_matrix[c_node, next_node]
        
        delta = added_cost - broken_cost
        if delta < best_delta:
            best_delta = delta
            best_pos = i
            
    return best_delta, best_pos


def _route_cost(route: list[int], cost_matrix: np.ndarray) -> float:
    """Evaluate full cost of a single route."""
    DEPOT = 0
    stops = [DEPOT] + [c + 1 for c in route] + [DEPOT]
    cost = 0.0
    for k in range(len(stops) - 1):
        cost += cost_matrix[stops[k], stops[k + 1]]
    return cost
