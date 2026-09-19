"""
Phase 3 verification test.

Tests:
1. QPSO Engine initialization
2. Adaptive alpha updates correctly
3. QPSO core position update executes without error
4. Particle bounds are respected [0, 1]
5. Convergence on a small problem instance (n=32)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from backend.config import load_config, get_graph_config, get_vrp_config, get_optimizer_config
from backend.graph.network import build_graph, place_customers_and_depot
from backend.graph.cost_matrix import CostMatrix
from backend.optimizer.fitness import FitnessEvaluator
from backend.optimizer.qpso import QPSOEngine


def test_phase3():
    print("=" * 60)
    print("PHASE 3 VERIFICATION TEST")
    print("=" * 60)

    # 1. Setup problem instance
    print("\n[1/6] Setting up problem instance...")
    config = load_config()
    
    # Use smaller instance for quick convergence testing
    config["vrp"]["num_customers"] = 32
    config["optimizer"]["population_size"] = 40
    config["optimizer"]["max_iterations"] = 100
    
    graph_config = get_graph_config(config)
    vrp_config = get_vrp_config(config)
    opt_config = get_optimizer_config(config)

    G = build_graph(graph_config)
    num_customers = min(vrp_config.get("num_customers", 32), G.number_of_nodes() - 1)
    depot, customers, demand_dict = place_customers_and_depot(
        G, num_customers=num_customers, seed=42
    )
    cm = CostMatrix(G, depot, customers)

    demands = np.array([demand_dict[c] for c in customers], dtype=np.float64)
    vehicle_capacity = vrp_config.get("vehicle_capacity", 100)

    evaluator = FitnessEvaluator(
        cost_matrix=cm.matrix,
        demands=demands,
        vehicle_capacity=vehicle_capacity,
        normalization_stats={"min_cost": cm.min_cost, "max_cost": cm.max_cost},
    )

    print(f"  ✓ {num_customers} customers, {opt_config['population_size']} particles")

    # 2. Engine Initialization
    print("\n[2/6] Testing QPSO Engine Initialization...")
    
    engine = QPSOEngine(
        cost_matrix=cm.matrix,
        demands=demands,
        vehicle_capacity=vehicle_capacity,
        config=opt_config,
        fitness_evaluator=evaluator,
        seed=42,
    )
    
    engine.initialize()
    
    assert engine.population.shape == (opt_config["population_size"], num_customers)
    assert engine.pbest_positions.shape == engine.population.shape
    assert engine.gbest_position.shape == (num_customers,)
    assert engine.gbest_fitness < float("inf")
    assert np.all((engine.population >= 0.0) & (engine.population <= 1.0))
    
    print(f"  ✓ Population initialized: {engine.population.shape}")
    print(f"  ✓ Initial Best Fitness: {engine.gbest_fitness:.6f}")

    # 3. Single Step Execution
    print("\n[3/6] Testing QPSO Single Step...")
    
    initial_fitness = engine.gbest_fitness
    state = engine.step()
    
    assert state.iteration == 1
    assert engine.alpha.shape == (opt_config["population_size"],)
    assert np.all((engine.population >= 0.0) & (engine.population <= 1.0))
    assert engine.gbest_fitness <= initial_fitness
    
    print(f"  ✓ Step executed successfully")
    print(f"  ✓ Alpha updated (mean={state.alpha_mean:.3f})")
    print(f"  ✓ Diversity={state.diversity:.3f}")

    # 4. Convergence Loop
    print("\n[4/6] Testing QPSO Convergence Loop...")
    
    start_fitness = engine.gbest_fitness
    
    while not engine.should_stop():
        state = engine.step()
        
        if state.iteration % 20 == 0:
            print(f"  Iter {state.iteration:>3}: "
                  f"Fitness={state.best_fitness:.6f} "
                  f"Vehicles={state.gbest_vehicles} "
                  f"Cost={state.gbest_cost:.2f} "
                  f"Div={state.diversity:.3f} "
                  f"Alpha={state.alpha_mean:.3f}")

    result = engine.get_result()
    
    assert result.total_iterations <= opt_config["max_iterations"], "Iterations should not exceed max"
    assert result.best_fitness <= start_fitness, "Fitness should not degrade"
    assert len(result.best_routes) == result.best_num_vehicles, "Route count mismatch"
    
    print(f"\n  ✓ Optimization finished in {result.elapsed_ms:.1f} ms")
    print(f"  ✓ Improvement: {start_fitness:.6f} -> {result.best_fitness:.6f}")

    # 5. Gbest Consistency Check
    print("\n[5/6] Testing Gbest Consistency...")
    from backend.optimizer.decoder import random_keys_to_giant_tour
    from backend.optimizer.split import split

    decoded_tour = random_keys_to_giant_tour(engine.gbest_position)
    recalc_split = split(
        decoded_tour, cm.matrix, demands, vehicle_capacity, max_vehicles=opt_config.get("max_vehicles")
    )
    recalc_fitness = evaluator.evaluate(recalc_split)

    # Ensure the fitness matches
    assert np.isclose(recalc_fitness, engine.gbest_fitness), f"Consistency error: {recalc_fitness} != {engine.gbest_fitness}"
    
    # Ensure the total cost matches
    assert np.isclose(recalc_split.total_cost, engine.gbest_split.total_cost), "Consistency error: split total cost mismatch"
    
    print(f"  ✓ Gbest position explicitly decodes to the exact same fitness and split cost")

    # 6. Stagnation Stopping Check
    print("\n[6/6] Testing Stagnation Stopping...")
    # Create a new engine with a very small patience
    opt_config["stopping"] = {"convergence_patience": 5}
    opt_config["max_iterations"] = 100
    engine_stag = QPSOEngine(
        cost_matrix=cm.matrix,
        demands=demands,
        vehicle_capacity=vehicle_capacity,
        config=opt_config,
        fitness_evaluator=evaluator,
        seed=123,
    )
    engine_stag.initialize()
    
    # Force it to stagnate
    iters = 0
    while not engine_stag.should_stop():
        engine_stag.step()
        iters += 1
        
    assert engine_stag.stagnation_counter >= 5, "Engine should have stopped due to stagnation"
    assert iters < 100, "Engine failed to stop early for stagnation"
    
    print(f"  ✓ Engine correctly stopped early at iteration {iters} due to stagnation")
    
    # Final summary
    print("\n" + "=" * 60)
    print("✅ ALL PHASE 3 TESTS PASSED!")
    print("=" * 60)
    print(f"\nBest Fitness: {result.best_fitness:.6f}")
    print(f"Best Cost:    {result.best_total_cost:.2f}")
    print(f"Vehicles:     {result.best_num_vehicles}")


if __name__ == "__main__":
    test_phase3()
