"""
Research-Grade CVRP Multi-Seed Benchmark Runner.

Orchestrates multi-algorithm (CLQPSO-GLS, Classical PSO, GA, OR-Tools) evaluations
across standard CVRP instances, 5 random seeds, ablation studies, scalability,
and dynamic traffic experiments.
"""

import os
import sys
import time
import json
import csv
import argparse
import logging
import numpy as np
from pathlib import Path
from typing import Any

from backend.benchmarks.instance_loader import load_cvrp_instance, CVRPInstance
from backend.benchmarks.classical_pso import ClassicalPSO
from backend.benchmarks.genetic_algorithm import GeneticAlgorithm
from backend.benchmarks.ortools_reference import solve_with_ortools
from backend.benchmarks.bks import get_bks_value
from backend.benchmarks.metrics import compute_statistics, compute_runtime_statistics, compute_gap
from backend.benchmarks.reproducibility import validate_solution
from backend.benchmarks.ablation import run_ablation_study
from backend.benchmarks.scalability import run_scalability_experiment
from backend.benchmarks.dynamic_traffic_benchmark import run_dynamic_traffic_benchmark
from backend.benchmarks.report_generator import generate_markdown_report
from backend.orchestrator import OptimizerOrchestrator

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RAW_DIR = RESULTS_DIR / "raw"
AGGREGATED_DIR = RESULTS_DIR / "aggregated"

DEFAULT_SEEDS = [42, 123, 456, 789, 999]
DEFAULT_INSTANCES = ["A-n32-k5", "A-n53-k7", "A-n80-k10"]
DEFAULT_ALGORITHMS = ["clqpso", "pso", "ga", "ortools"]

def run_clqpso(instance: CVRPInstance, seed: int, population_size: int = 128, max_iterations: int = 150) -> dict[str, Any]:
    """Execute CLQPSO-GLS on standard CVRP instance."""
    config = {
        "optimizer": {
            "population_size": population_size,
            "max_iterations": max_iterations,
            "seed": seed
        }
    }
    t0 = time.perf_counter()
    orchestrator = OptimizerOrchestrator(config)
    orchestrator.rng = np.random.RandomState(seed)
    orchestrator.setup_custom_instance(instance.cost_matrix, instance.demands, instance.vehicle_capacity)

    opt_res = orchestrator.run()
    t1 = time.perf_counter()

    routes = opt_res.best_routes
    val = validate_solution(
        routes=routes,
        demands=instance.demands,
        vehicle_capacity=instance.vehicle_capacity,
        num_customers=instance.num_customers,
        cost_matrix=instance.cost_matrix,
        reported_fitness=opt_res.best_fitness
    )

    return {
        "algorithm": "CLQPSO-GLS",
        "instance": instance.name,
        "seed": seed,
        "best_fitness": float(opt_res.best_fitness),
        "distance": float(opt_res.best_fitness),
        "travel_time": float(opt_res.best_fitness),
        "congestion_cost": 0.0,
        "vehicle_count": len(routes),
        "runtime_seconds": float(t1 - t0),
        "iterations": max_iterations,
        "convergence": [{"iteration": i+1, "best_fitness": float(f)} for i, f in enumerate(getattr(opt_res, 'history', [opt_res.best_fitness]))],
        "routes": routes,
        "parameters": {"population_size": population_size, "max_iterations": max_iterations},
        "status": "COMPLETED",
        "valid": val["valid"],
        "errors": val["errors"]
    }

def run_benchmarks(
    instances: list[str] = None,
    seeds: list[int] = None,
    algorithms: list[str] = None,
    run_ablation: bool = True,
    run_scalability: bool = True,
    run_traffic: bool = True,
    population_size: int = 128,
    max_iterations: int = 150
) -> dict[str, Any]:
    """Execute complete research-grade CVRP benchmark framework."""
    if instances is None:
        instances = DEFAULT_INSTANCES
    if seeds is None:
        seeds = DEFAULT_SEEDS
    if algorithms is None:
        algorithms = DEFAULT_ALGORITHMS

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    AGGREGATED_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("==================================================")
    logger.info("CLQPSO-GLS RESEARCH-GRADE BENCHMARK SUITE")
    logger.info("==================================================")
    logger.info(f"Instances: {instances}")
    logger.info(f"Algorithms: {algorithms}")
    logger.info(f"Seeds: {seeds}")

    raw_runs = []
    aggregated_summaries = []
    total_runs = 0
    failed_runs = 0
    invalid_solutions = 0

    for inst_name in instances:
        try:
            instance = load_cvrp_instance(inst_name)
        except Exception as e:
            logger.error(f"Failed to load instance {inst_name}: {e}")
            continue

        inst_raw_dir = RAW_DIR / inst_name
        inst_raw_dir.mkdir(parents=True, exist_ok=True)

        for algo in algorithms:
            algo_key = algo.lower()
            algo_costs = []
            algo_runtimes = []
            algo_valid_flags = []

            # Deterministic solver (OR-Tools)
            if algo_key == "ortools":
                logger.info(f"Running OR-Tools on {inst_name}...")
                try:
                    res = solve_with_ortools(instance, time_limit_seconds=5)
                    raw_runs.append(res)
                    total_runs += 1
                    if not res["valid"]:
                        invalid_solutions += 1

                    raw_path = inst_raw_dir / "OR-Tools_seed0.json"
                    with open(raw_path, "w", encoding="utf-8") as f:
                        json.dump(res, f, indent=2)

                    algo_costs.append(res["best_fitness"])
                    algo_runtimes.append(res["runtime_seconds"])
                    algo_valid_flags.append(res["valid"])
                except Exception as e:
                    logger.error(f"OR-Tools error on {inst_name}: {e}")
                    failed_runs += 1
            else:
                # Stochastic solvers (CLQPSO, Classical PSO, GA) across seeds
                for seed in seeds:
                    total_runs += 1
                    logger.info(f"Running {algo.upper()} on {inst_name} [Seed {seed}]...")
                    try:
                        if algo_key == "clqpso":
                            res = run_clqpso(instance, seed, population_size, max_iterations)
                        elif algo_key == "pso":
                            from backend.optimizer.fitness import FitnessEvaluator
                            fe = FitnessEvaluator(instance.cost_matrix, instance.demands, instance.vehicle_capacity)
                            pso = ClassicalPSO(instance.cost_matrix, instance.demands, instance.vehicle_capacity,
                                              {"population_size": population_size, "max_iterations": max_iterations}, fe, seed, inst_name)
                            res = pso.solve()
                        elif algo_key == "ga":
                            from backend.optimizer.fitness import FitnessEvaluator
                            fe = FitnessEvaluator(instance.cost_matrix, instance.demands, instance.vehicle_capacity)
                            ga = GeneticAlgorithm(instance.cost_matrix, instance.demands, instance.vehicle_capacity,
                                                 {"population_size": population_size, "max_iterations": max_iterations}, fe, seed, inst_name)
                            res = ga.solve()
                        else:
                            continue

                        raw_runs.append(res)
                        if not res["valid"]:
                            invalid_solutions += 1

                        raw_path = inst_raw_dir / f"{res['algorithm']}_seed{seed}.json"
                        with open(raw_path, "w", encoding="utf-8") as f:
                            json.dump(res, f, indent=2)

                        algo_costs.append(res["best_fitness"])
                        algo_runtimes.append(res["runtime_seconds"])
                        algo_valid_flags.append(res["valid"])
                    except Exception as e:
                        logger.error(f"Error running {algo} on {inst_name} seed {seed}: {e}")
                        failed_runs += 1

            if algo_costs:
                stats = compute_statistics(algo_costs)
                rstats = compute_runtime_statistics(algo_runtimes)
                gap_info = compute_gap(stats["min"], inst_name)

                display_algo_name = raw_runs[-1]["algorithm"] if raw_runs else algo.upper()

                summary = {
                    "instance": inst_name,
                    "algorithm": display_algo_name,
                    "mean": stats["mean"],
                    "std": stats["std"],
                    "best": stats["min"],
                    "worst": stats["max"],
                    "median": stats["median"],
                    "mean_runtime": rstats["mean_runtime"],
                    "gap_percent": gap_info["gap_percent"],
                    "valid": all(algo_valid_flags)
                }
                aggregated_summaries.append(summary)

    # Save Aggregated JSON and CSV
    agg_json_path = AGGREGATED_DIR / "results.json"
    with open(agg_json_path, "w", encoding="utf-8") as f:
        json.dump(aggregated_summaries, f, indent=2)

    agg_csv_path = AGGREGATED_DIR / "results.csv"
    with open(agg_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "instance", "algorithm", "mean", "std", "best", "worst", "median", "mean_runtime", "gap_percent", "valid"
        ])
        writer.writeheader()
        for row in aggregated_summaries:
            writer.writerow(row)

    # Optional experiments
    ablation_results = None
    if run_ablation:
        logger.info("Executing 7-Variant Ablation Study...")
        abl_res = run_ablation_study(instance_name=instances[0], seeds=seeds, population_size=population_size, max_iterations=max_iterations)
        ablation_results = abl_res["variants"]

    scalability_results = None
    if run_scalability:
        logger.info("Executing Scalability Experiment (32 to 200 Customers)...")
        scalability_results = run_scalability_experiment(seed=seeds[0])

    traffic_results = None
    if run_traffic:
        logger.info("Executing Category B Bangalore Dynamic Traffic Benchmark...")
        traffic_results = run_dynamic_traffic_benchmark(seed=seeds[0])

    # Generate Report
    report_path = generate_markdown_report(
        benchmark_data=aggregated_summaries,
        ablation_data=ablation_results,
        scalability_data=scalability_results,
        traffic_data=traffic_results
    )

    logger.info("==================================================")
    logger.info("CLQPSO-GLS BENCHMARK COMPLETE")
    logger.info("==================================================")
    logger.info(f"Runs completed: {total_runs - failed_runs} / {total_runs}")
    logger.info(f"Failed runs: {failed_runs}")
    logger.info(f"Invalid solutions: {invalid_solutions}")
    logger.info(f"Aggregated Results: {agg_csv_path}")
    logger.info(f"Benchmark Report: {report_path}")
    logger.info("==================================================")

    return {
        "aggregated": aggregated_summaries,
        "ablation": ablation_results,
        "scalability": scalability_results,
        "traffic": traffic_results,
        "report_path": report_path
    }

def main():
    parser = argparse.ArgumentParser(description="CLQPSO-GLS Research CVRP Benchmark Runner")
    parser.add_argument("--instances", nargs="+", default=DEFAULT_INSTANCES, help="Benchmark instances to evaluate")
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS, help="Random seeds")
    parser.add_argument("--algorithms", nargs="+", default=DEFAULT_ALGORITHMS, help="Algorithms to run (clqpso pso ga ortools)")
    parser.add_argument("--ablation", action="store_true", default=True, help="Run 7-variant ablation study")
    parser.add_argument("--scalability", action="store_true", default=True, help="Run customer scalability study")
    parser.add_argument("--traffic", action="store_true", default=True, help="Run dynamic traffic experiment")

    args = parser.parse_args()
    run_benchmarks(
        instances=args.instances,
        seeds=args.seeds,
        algorithms=args.algorithms,
        run_ablation=args.ablation,
        run_scalability=args.scalability,
        run_traffic=args.traffic
    )

if __name__ == "__main__":
    main()
