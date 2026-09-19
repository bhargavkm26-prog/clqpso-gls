"""
Phase 4 verification test.

Tests:
1. 2-opt giant tour operator
2. Or-opt giant tour operator
3. SWAP* inter-route operator
4. GLS penalty framework
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from backend.config import load_config, get_graph_config, get_vrp_config
from backend.graph.network import build_graph, place_customers_and_depot
from backend.graph.cost_matrix import CostMatrix
from backend.optimizer.split import split
from backend.optimizer.local_search import (
    two_opt_giant_tour,
    or_opt_giant_tour,
    swap_star,
    _route_cost
)
from backend.optimizer.gls import GuidedLocalSearch


def test_phase4():
    print("=" * 60)
    print("PHASE 4 VERIFICATION TEST")
    print("=" * 60)

    # 1. Setup problem instance
    print("\n[1/4] Setting up problem instance...")
    config = load_config()
    
    # Very small instance to trace operators
    config["vrp"]["num_customers"] = 20
    
    graph_config = get_graph_config(config)
    vrp_config = get_vrp_config(config)

    G = build_graph(graph_config)
    num_customers = min(vrp_config.get("num_customers", 20), G.number_of_nodes() - 1)
    depot, customers, demand_dict = place_customers_and_depot(
        G, num_customers=num_customers, seed=123
    )
    cm = CostMatrix(G, depot, customers)

    demands = np.array([demand_dict[c] for c in customers], dtype=np.float64)
    vehicle_capacity = vrp_config.get("vehicle_capacity", 100)

    # Generate a random initial giant tour
    rng = np.random.RandomState(42)
    giant_tour = np.arange(num_customers)
    rng.shuffle(giant_tour)

    print(f"  ✓ {num_customers} customers generated")

    # 2. Test 2-opt and Or-opt (Intra-route / Giant Tour)
    print("\n[2/4] Testing Intra-route Operators (2-opt, Or-opt)...")
    
    # 2-opt
    two_opt_tour, improved_2opt = two_opt_giant_tour(giant_tour, cm.matrix, max_iterations=20)
    print(f"  ✓ 2-opt improved: {improved_2opt}")
    
    # Or-opt
    or_opt_tour, improved_oropt = or_opt_giant_tour(two_opt_tour, cm.matrix, max_iterations=20)
    print(f"  ✓ Or-opt improved: {improved_oropt}")
    
    # We should have improved significantly from random
    from backend.optimizer.local_search import _eval_tour_cost
    initial_cost = _eval_tour_cost(giant_tour, cm.matrix)
    final_cost = _eval_tour_cost(or_opt_tour, cm.matrix)
    
    print(f"  ✓ Giant tour cost: {initial_cost:.1f} -> {final_cost:.1f}")
    assert final_cost <= initial_cost

    # 3. Test SWAP* (Inter-route)
    print("\n[3/4] Testing Inter-route SWAP*...")
    
    # First, split the optimized giant tour into routes
    split_res = split(or_opt_tour, cm.matrix, demands, vehicle_capacity)
    print(f"  ✓ Initial split: {split_res.num_vehicles} vehicles, cost: {split_res.total_cost:.1f}")
    
    # Apply SWAP*
    swap_res, improved_swap = swap_star(split_res, cm.matrix, demands, vehicle_capacity)
    
    print(f"  ✓ SWAP* improved: {improved_swap}")
    if improved_swap:
        print(f"  ✓ SWAP* cost: {split_res.total_cost:.1f} -> {swap_res.total_cost:.1f}")
        assert swap_res.total_cost <= split_res.total_cost

    # Verify feasibility
    for idx, route in enumerate(swap_res.routes):
        load = sum(demands[c] for c in route)
        assert load <= vehicle_capacity, f"Route {idx} exceeds capacity!"

    # 4. Test GLS Penalty Framework
    print("\n[4/4] Testing GLS Penalty Framework...")
    
    gls = GuidedLocalSearch(n_stops=num_customers + 1, config=config)
    
    # Ensure lambda initializes
    aug_matrix_1 = gls.get_augmented_cost_matrix(cm.matrix)
    assert gls._lambda > 0.0
    print(f"  ✓ GLS lambda initialized: {gls._lambda:.4f}")
    
    # No penalties yet, matrix should be identical
    assert np.allclose(aug_matrix_1, cm.matrix)
    
    # Apply penalties to current best routes
    gls.update_penalties(swap_res.routes, cm.matrix)
    
    # Get augmented matrix again
    aug_matrix_2 = gls.get_augmented_cost_matrix(cm.matrix)
    
    # The augmented matrix should now be strictly >= original matrix
    # and strictly > somewhere
    assert np.all(aug_matrix_2 >= cm.matrix)
    assert np.any(aug_matrix_2 > cm.matrix)
    
    num_penalized = np.sum(gls.penalties > 0)
    print(f"  ✓ GLS penalized {num_penalized} edges in stagnated solution")

    print("\n" + "=" * 60)
    print("✅ ALL PHASE 4 TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_phase4()
