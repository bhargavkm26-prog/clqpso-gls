"""
Unit tests for Research-Grade CVRP Benchmark Suite.
"""

import pytest
import numpy as np
from backend.benchmarks.instance_loader import load_cvrp_instance
from backend.benchmarks.bks import get_bks_value, calculate_gap_percent
from backend.benchmarks.reproducibility import validate_solution
from backend.benchmarks.metrics import compute_statistics, compute_gap
from backend.benchmarks.ortools_reference import solve_with_ortools
from backend.benchmarks.classical_pso import ClassicalPSO
from backend.benchmarks.genetic_algorithm import GeneticAlgorithm
from backend.optimizer.fitness import FitnessEvaluator

def test_instance_loader():
    instance = load_cvrp_instance("A-n32-k5")
    assert instance.name == "A-n32-k5"
    assert instance.dimension == 32
    assert instance.num_customers == 31
    assert instance.vehicle_capacity == 100.0
    assert instance.cost_matrix.shape == (32, 32)

def test_bks_lookup():
    bks32 = get_bks_value("A-n32-k5")
    bks53 = get_bks_value("A-n53-k7")
    bks80 = get_bks_value("A-n80-k10")

    assert bks32 == 784
    assert bks53 == 1010
    assert bks80 == 1763

    gap = calculate_gap_percent(784.0, 784.0)
    assert abs(gap) < 1e-5

def test_solution_validator():
    # Setup dummy problem (3 customers: 0, 1, 2)
    demands = np.array([10.0, 20.0, 30.0])
    capacity = 50.0
    num_customers = 3

    cost_matrix = np.zeros((4, 4))
    for i in range(4):
        for j in range(4):
            if i != j:
                cost_matrix[i, j] = 10.0

    # Valid solution: Route 1 [0, 1] (demand 30 <= 50), Route 2 [2] (demand 30 <= 50)
    valid_routes = [[0, 1], [2]]
    val = validate_solution(valid_routes, demands, capacity, num_customers, cost_matrix, reported_fitness=50.0)
    assert val["valid"] is True
    assert len(val["errors"]) == 0

    # Invalid: Duplicate customer
    dup_routes = [[0, 1], [1, 2]]
    val_dup = validate_solution(dup_routes, demands, capacity, num_customers, cost_matrix, reported_fitness=80.0)
    assert val_dup["valid"] is False
    assert any("Duplicate" in err for err in val_dup["errors"])

    # Invalid: Capacity breach
    cap_routes = [[0, 1, 2]]  # demand 60 > 50
    val_cap = validate_solution(cap_routes, demands, capacity, num_customers, cost_matrix, reported_fitness=40.0)
    assert val_cap["valid"] is False
    assert any("capacity violation" in err for err in val_cap["errors"])

def test_metrics_and_gap():
    vals = [10.0, 20.0, 30.0, 40.0, 50.0]
    stats = compute_statistics(vals)
    assert stats["mean"] == 30.0
    assert stats["min"] == 10.0
    assert stats["max"] == 50.0

    gap = compute_gap(784.0, "A-n32-k5")
    assert gap["gap_percent"] == 0.0

def test_ortools_reference():
    instance = load_cvrp_instance("A-n32-k5")
    res = solve_with_ortools(instance, time_limit_seconds=2)
    assert res["algorithm"] == "OR-Tools"
    assert res["valid"] is True
    assert res["best_fitness"] > 0
    assert len(res["routes"]) > 0

def test_baselines_fast_run():
    instance = load_cvrp_instance("A-n32-k5")
    fe = FitnessEvaluator(instance.cost_matrix, instance.demands, instance.vehicle_capacity)
    config = {"population_size": 20, "max_iterations": 5}

    pso = ClassicalPSO(instance.cost_matrix, instance.demands, instance.vehicle_capacity, config, fe, seed=42, instance_name="A-n32-k5")
    res_pso = pso.solve()
    assert res_pso["algorithm"] == "Classical PSO"
    assert res_pso["valid"] is True

    ga = GeneticAlgorithm(instance.cost_matrix, instance.demands, instance.vehicle_capacity, config, fe, seed=42, instance_name="A-n32-k5")
    res_ga = ga.solve()
    assert res_ga["algorithm"] == "Genetic Algorithm"
    assert res_ga["valid"] is True
