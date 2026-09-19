"""
Ablation Study Engine for CLQPSO-GLS.

Measures the exact incremental contribution of each component across 7 variants:
A: Base QPSO
B: + Chaotic Initialization
C: + Adaptive Alpha
D: + Lévy Flight Recovery
E: + GLS (2-opt, Or-opt)
F: + SWAP* Inter-Route Operator
G: Full CLQPSO-GLS
"""

import time
import json
import csv
import numpy as np
from pathlib import Path
from typing import Any

from backend.benchmarks.instance_loader import load_cvrp_instance, CVRPInstance
from backend.benchmarks.metrics import compute_statistics, compute_gap
from backend.benchmarks.reproducibility import validate_solution
from backend.orchestrator import OptimizerOrchestrator

RESULTS_DIR = Path(__file__).resolve().parent / "results" / "ablation"

VARIANTS = [
    {"name": "Base QPSO", "code": "A", "chaotic": False, "alpha": "constant", "levy": False, "gls": False, "swap_star": False},
    {"name": "+ Chaotic Init", "code": "B", "chaotic": True, "alpha": "constant", "levy": False, "gls": False, "swap_star": False},
    {"name": "+ Adaptive Alpha", "code": "C", "chaotic": True, "alpha": "per_particle", "levy": False, "gls": False, "swap_star": False},
    {"name": "+ Levy Flight", "code": "D", "chaotic": True, "alpha": "per_particle", "levy": True, "gls": False, "swap_star": False},
    {"name": "+ GLS (2-opt/Or-opt)", "code": "E", "chaotic": True, "alpha": "per_particle", "levy": True, "gls": True, "swap_star": False},
    {"name": "+ SWAP*", "code": "F", "chaotic": True, "alpha": "per_particle", "levy": True, "gls": True, "swap_star": True},
    {"name": "Full CLQPSO-GLS", "code": "G", "chaotic": True, "alpha": "per_particle", "levy": True, "gls": True, "swap_star": True}
]

def run_ablation_study(
    instance_name: str = "A-n32-k5",
    seeds: list[int] = None,
    population_size: int = 128,
    max_iterations: int = 150
) -> dict[str, Any]:
    """Run 7-variant ablation study on a CVRP benchmark instance across seeds."""
    if seeds is None:
        seeds = [42, 123, 456, 789, 999]

    instance = load_cvrp_instance(instance_name)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    variant_summaries = []
    prev_mean_cost = None

    for var in VARIANTS:
        costs = []
        runtimes = []
        valid_runs = 0

        for seed in seeds:
            config = {
                "optimizer": {
                    "population_size": population_size,
                    "max_iterations": max_iterations,
                    "seed": seed,
                    "use_chaotic_init": var["chaotic"],
                    "alpha_mode": var["alpha"],
                    "use_levy": var["levy"],
                    "use_gls": var["gls"],
                    "use_swap_star": var["swap_star"],
                }
            }

            t0 = time.perf_counter()
            orchestrator = OptimizerOrchestrator(config)
            orchestrator.rng = np.random.RandomState(seed)
            orchestrator.setup_custom_instance(instance.cost_matrix, instance.demands, instance.vehicle_capacity)

            # Configure variant switches
            if not var["gls"]:
                orchestrator.config["optimizer"]["gls"] = {"enabled": False}

            opt_res = orchestrator.run()
            t1 = time.perf_counter()

            val = validate_solution(
                routes=opt_res.best_routes,
                demands=instance.demands,
                vehicle_capacity=instance.vehicle_capacity,
                num_customers=instance.num_customers,
                cost_matrix=instance.cost_matrix,
                reported_fitness=opt_res.best_fitness
            )

            if val["valid"]:
                valid_runs += 1

            costs.append(float(opt_res.best_fitness))
            runtimes.append(float(t1 - t0))

        stats = compute_statistics(costs)
        gap_info = compute_gap(stats["best"] if "best" in stats else stats["min"], instance_name)

        curr_mean = stats["mean"]
        if prev_mean_cost is None:
            improvement_percent = 0.0
        else:
            improvement_percent = ((prev_mean_cost - curr_mean) / prev_mean_cost) * 100.0
        prev_mean_cost = curr_mean

        variant_summary = {
            "variant_code": var["code"],
            "variant_name": var["name"],
            "instance": instance_name,
            "seeds": seeds,
            "mean": stats["mean"],
            "std": stats["std"],
            "best": stats["min"],
            "worst": stats["max"],
            "median": stats["median"],
            "mean_runtime_seconds": float(np.mean(runtimes)),
            "gap_to_bks_percent": gap_info["gap_percent"],
            "improvement_percent": float(improvement_percent),
            "valid_runs": valid_runs,
            "total_runs": len(seeds)
        }
        variant_summaries.append(variant_summary)

    # Save to JSON and CSV
    json_path = RESULTS_DIR / "ablation_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(variant_summaries, f, indent=2)

    csv_path = RESULTS_DIR / "ablation_results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "variant_code", "variant_name", "instance", "mean", "std", "best", "worst",
            "median", "mean_runtime_seconds", "gap_to_bks_percent", "improvement_percent"
        ])
        writer.writeheader()
        for row in variant_summaries:
            row_copy = {k: v for k, v in row.items() if k in writer.fieldnames}
            writer.writerow(row_copy)

    return {
        "instance": instance_name,
        "variants": variant_summaries,
        "json_path": str(json_path),
        "csv_path": str(csv_path)
    }

if __name__ == "__main__":
    run_ablation_study()
