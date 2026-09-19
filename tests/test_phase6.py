"""
Phase 6 verification test.

Tests:
1. Orchestrator initialization and setup
2. Full execution loop (QPSO + GLS + Local Search + Lévy Flight)
3. Dynamic traffic update mid-optimization
"""

import sys
import os
import logging
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import load_config
from backend.orchestrator import OptimizerOrchestrator

logging.basicConfig(level=logging.INFO, format="%(message)s")


def test_phase6():
    print("=" * 60)
    print("PHASE 6 VERIFICATION TEST (Orchestrator)")
    print("=" * 60)

    # 1. Configuration
    config = load_config()
    # Fast test configuration
    config["vrp"]["num_customers"] = 25
    config["optimizer"]["population_size"] = 30
    config["optimizer"]["max_iterations"] = 150
    config["optimizer"]["local_search_frequency"] = 25
    config["optimizer"]["levy"]["patience"] = 10
    config["optimizer"]["gls"]["enabled"] = True

    # Ensure scenarios exist
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "scenarios")
    os.makedirs(data_dir, exist_ok=True)
    
    # 2. Initialization
    print("\n[1/3] Initializing Orchestrator...")
    orchestrator = OptimizerOrchestrator(config)
    
    # Pre-generate graph to generate scenarios
    graph_config = config.get("graph", {})
    from backend.graph.network import build_graph
    temp_graph = build_graph(graph_config)
    
    # Generate scenarios
    from backend.graph.traffic import generate_default_scenarios
    generate_default_scenarios(temp_graph, data_dir)

    orchestrator.setup_problem(num_customers=25, scenario_file=os.path.join(data_dir, "baseline.json"))
    
    assert orchestrator.graph is not None
    assert orchestrator.cost_matrix_manager is not None
    assert len(orchestrator.customers) == 25
    print("  ✓ Orchestrator initialized successfully")

    # 3. Partial Run (Before Traffic Update)
    print("\n[2/3] Running Optimization (Baseline)...")
    
    orchestrator._init_optimizer_components()
    
    # Run for 50 iterations manually
    for _ in range(50):
        state = orchestrator.qpso.step()
        if orchestrator.qpso.stagnation_counter >= orchestrator.levy_patience:
            orchestrator.gls.update_penalties(
                orchestrator.qpso.gbest_split.routes,
                orchestrator.cost_matrix_manager.matrix
            )
            num_jump = int(orchestrator.qpso.N * orchestrator.levy_jump_fraction)
            orchestrator.qpso.population = orchestrator.levy.apply_jump(
                orchestrator.qpso.population, num_particles_to_jump=num_jump
            )
            orchestrator.qpso._evaluate_population()
            orchestrator.qpso._update_bests()
            orchestrator.qpso.stagnation_counter = 0
            
        if state.iteration % orchestrator.local_search_frequency == 0:
            orchestrator._apply_local_search_to_gbest()
            
    best_fitness_before = orchestrator.qpso.gbest_fitness
    best_cost_before = orchestrator.qpso.gbest_split.total_cost
    
    print(f"  ✓ Reached Iteration 50")
    print(f"  ✓ Baseline Cost: {best_cost_before:.2f}")

    # 4. Traffic Update Mid-Optimization
    print("\n[3/3] Simulating Traffic Disruption & Resuming...")
    
    orchestrator.update_traffic_scenario(os.path.join(data_dir, "disruption.json"))
    
    # The swarm should have been re-evaluated
    assert orchestrator.qpso.gbest_fitness != best_fitness_before, "Fitness didn't change after traffic update!"
    
    # Resume optimization
    for _ in range(50):
        state = orchestrator.qpso.step()
        if orchestrator.qpso.stagnation_counter >= orchestrator.levy_patience:
            orchestrator.gls.update_penalties(
                orchestrator.qpso.gbest_split.routes,
                orchestrator.cost_matrix_manager.matrix
            )
            num_jump = int(orchestrator.qpso.N * orchestrator.levy_jump_fraction)
            orchestrator.qpso.population = orchestrator.levy.apply_jump(
                orchestrator.qpso.population, num_particles_to_jump=num_jump
            )
            orchestrator.qpso._evaluate_population()
            orchestrator.qpso._update_bests()
            orchestrator.qpso.stagnation_counter = 0
            
        if state.iteration % orchestrator.local_search_frequency == 0:
            orchestrator._apply_local_search_to_gbest()
            
    res = orchestrator.qpso.get_result()
    
    print(f"  ✓ Reached Iteration 100")
    print(f"  ✓ Disrupted Cost: {res.best_total_cost:.2f}")
    
    assert res.total_iterations == 100

    print("\n" + "=" * 60)
    print("✅ ALL PHASE 6 TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_phase6()
