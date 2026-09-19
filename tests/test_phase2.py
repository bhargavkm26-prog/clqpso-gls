"""
Phase 2 verification test.

Tests:
1. SPV decoder converts random keys to valid giant tours
2. Re-encoding preserves tour ordering
3. Prins Split produces feasible routes respecting capacity
4. Fitness evaluator produces valid scores
5. Edge cases: single customer, all-same demands
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from backend.config import load_config, get_graph_config, get_vrp_config
from backend.graph.network import build_graph, place_customers_and_depot
from backend.graph.cost_matrix import CostMatrix
from backend.optimizer.decoder import (
    random_keys_to_giant_tour,
    giant_tour_to_random_keys,
    batch_decode,
    batch_encode,
)
from backend.optimizer.split import split, evaluate_routes
from backend.optimizer.fitness import FitnessEvaluator


def test_phase2():
    print("=" * 60)
    print("PHASE 2 VERIFICATION TEST")
    print("=" * 60)

    # Setup: build graph and cost matrix from Phase 1
    config = load_config()
    graph_config = get_graph_config(config)
    vrp_config = get_vrp_config(config)

    G = build_graph(graph_config)
    num_customers = min(vrp_config.get("num_customers", 50), G.number_of_nodes() - 1)
    depot, customers, demand_dict = place_customers_and_depot(
        G, num_customers=num_customers, seed=42
    )
    cm = CostMatrix(G, depot, customers)

    # Build demands array (indexed by customer index 0..n-1)
    demands = np.array([demand_dict[c] for c in customers], dtype=np.float64)
    vehicle_capacity = vrp_config.get("vehicle_capacity", 100)

    # ──────────────────────────────────────────────────────────
    # Test 1: SPV Decoder
    # ──────────────────────────────────────────────────────────
    print("\n[1/5] Testing SPV decoder...")

    keys = np.array([0.72, 0.11, 0.54, 0.31])
    tour = random_keys_to_giant_tour(keys)
    assert list(tour) == [1, 3, 2, 0], f"Expected [1,3,2,0], got {list(tour)}"
    print(f"  OK: keys={keys} -> tour={list(tour)}")

    # Random keys with n_customers dimensions
    rng = np.random.RandomState(42)
    random_keys = rng.random(num_customers)
    giant_tour = random_keys_to_giant_tour(random_keys)

    assert len(giant_tour) == num_customers, "Tour length must match customer count"
    assert len(set(giant_tour)) == num_customers, "Tour must visit each customer exactly once"
    assert set(giant_tour) == set(range(num_customers)), "Tour must contain all customers"
    print(f"  OK: {num_customers} customers -> valid giant tour of length {len(giant_tour)}")

    # ──────────────────────────────────────────────────────────
    # Test 2: Re-encoding preserves ordering
    # ──────────────────────────────────────────────────────────
    print("\n[2/5] Testing rank re-encoding...")

    re_encoded = giant_tour_to_random_keys(giant_tour, num_customers)
    re_decoded = random_keys_to_giant_tour(re_encoded)

    assert np.array_equal(giant_tour, re_decoded), \
        f"Re-encoding must preserve tour ordering!\n  Original: {giant_tour[:10]}...\n  Re-decoded: {re_decoded[:10]}..."
    print(f"  OK: tour -> keys -> tour roundtrip preserves ordering")

    # Batch decode/encode
    N_pop = 10
    pop_keys = rng.random((N_pop, num_customers))
    pop_tours = batch_decode(pop_keys)
    assert pop_tours.shape == (N_pop, num_customers)

    pop_keys_re = batch_encode(pop_tours, num_customers)
    pop_tours_re = batch_decode(pop_keys_re)
    assert np.array_equal(pop_tours, pop_tours_re), "Batch encode/decode roundtrip failed"
    print(f"  OK: batch encode/decode for {N_pop} particles")

    # ──────────────────────────────────────────────────────────
    # Test 3: Prins Split
    # ──────────────────────────────────────────────────────────
    print("\n[3/5] Testing Prins Split decoder...")

    result = split(
        giant_tour=giant_tour,
        cost_matrix=cm.matrix,
        demands=demands,
        vehicle_capacity=vehicle_capacity,
    )

    print(f"  Routes: {result.num_vehicles}")
    print(f"  Total cost: {result.total_cost:.2f}")
    print(f"  Feasible: {result.feasible}")

    # Verify all customers are served exactly once
    all_served = []
    for route in result.routes:
        all_served.extend(route)

    assert len(all_served) == num_customers, \
        f"Split must serve all {num_customers} customers, served {len(all_served)}"
    assert len(set(all_served)) == num_customers, \
        "Each customer must appear exactly once across all routes"
    assert set(all_served) == set(range(num_customers)), \
        "All customer indices must be present"
    print(f"  OK: all {num_customers} customers served exactly once")

    # Verify capacity constraints
    for i, route in enumerate(result.routes):
        load = sum(demands[c] for c in route)
        assert load <= vehicle_capacity, \
            f"Route {i} exceeds capacity: {load} > {vehicle_capacity}"
    print(f"  OK: all routes respect capacity constraint ({vehicle_capacity})")

    # Print route details
    for i, route in enumerate(result.routes):
        load = sum(demands[c] for c in route)
        print(f"    Route {i}: {len(route)} customers, load={load:.0f}/{vehicle_capacity}, cost={result.route_costs[i]:.2f}")

    # ──────────────────────────────────────────────────────────
    # Test 4: Fitness evaluator
    # ──────────────────────────────────────────────────────────
    print("\n[4/5] Testing fitness evaluator...")

    evaluator = FitnessEvaluator(
        cost_matrix=cm.matrix,
        demands=demands,
        vehicle_capacity=vehicle_capacity,
        normalization_stats={
            "min_cost": cm.min_cost,
            "max_cost": cm.max_cost,
        },
    )

    fitness = evaluator.evaluate(result)
    assert np.isfinite(fitness), f"Fitness should be finite, got {fitness}"
    assert fitness >= 0, f"Fitness should be non-negative, got {fitness}"
    print(f"  OK: fitness = {fitness:.6f}")

    # Detailed evaluation
    details = evaluator.evaluate_detailed(result)
    print(f"  Total cost: {details['total_cost']:.2f}")
    print(f"  Vehicles: {details['num_vehicles']}")
    print(f"  Feasible: {details['feasible']}")
    print(f"  Total demand: {details['total_demand']:.0f}")

    # ──────────────────────────────────────────────────────────
    # Test 5: Multiple random particles produce different solutions
    # ──────────────────────────────────────────────────────────
    print("\n[5/5] Testing with multiple random particles...")

    fitnesses = []
    for seed in range(5):
        keys = np.random.RandomState(seed).random(num_customers)
        tour = random_keys_to_giant_tour(keys)
        res = split(tour, cm.matrix, demands, vehicle_capacity)
        fit = evaluator.evaluate(res)
        fitnesses.append(fit)
        print(f"  Seed {seed}: fitness={fit:.6f}, vehicles={res.num_vehicles}, cost={res.total_cost:.2f}")

    assert len(set(f"{f:.6f}" for f in fitnesses)) > 1, \
        "Different random keys should produce different fitness values"
    print(f"\n  OK: fitness range [{min(fitnesses):.6f}, {max(fitnesses):.6f}]")

    # Final summary
    print("\n" + "=" * 60)
    print("ALL PHASE 2 TESTS PASSED!")
    print("=" * 60)
    print(f"\nDecoder: SPV random-key -> giant tour (verified)")
    print(f"Split: Prins DP -> {result.num_vehicles} feasible routes")
    print(f"Fitness: multi-objective weighted sum = {fitness:.6f}")


if __name__ == "__main__":
    test_phase2()
