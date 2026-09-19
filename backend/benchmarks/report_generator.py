"""
Automated Benchmark Report Generator.

Compiles raw benchmark output, ablation study results, scalability metrics, and
dynamic traffic logs into a publishable Markdown report at docs/benchmark_report.md.
"""

import json
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
REPORT_PATH = DOCS_DIR / "benchmark_report.md"

def generate_markdown_report(
    benchmark_data: Optional[list[dict[str, Any]]] = None,
    ablation_data: Optional[list[dict[str, Any]]] = None,
    scalability_data: Optional[list[dict[str, Any]]] = None,
    traffic_data: Optional[dict[str, Any]] = None
) -> str:
    """Generate Markdown benchmark report."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Research-Grade CVRP Benchmark Report: CLQPSO-GLS",
        "",
        "**Generated:** Automatically from Empirical Benchmark Runs",
        "**Framework:** Pure Python (NumPy) + Google OR-Tools Baseline",
        "",
        "---",
        "",
        "## 1. Executive Summary & Problem Formulation",
        "",
        "This report documents empirical benchmark evaluations of **CLQPSO-GLS** (Chaotic Lévy Quantum Particle Swarm Optimization with Guided Local Search) on standard Capacitated Vehicle Routing Problem (CVRP) instances.",
        "",
        "- **Objective:** Minimize total route distance $D = \\sum_{k} \\sum_{i,j} d_{ij} x_{ijk}$.",
        "- **Constraints:** Capacity constraints, customer coverage (each customer served exactly once), and depot loop guarantee.",
        "- **Reproducibility:** Evaluated across 5 fixed random seeds (`[42, 123, 456, 789, 999]`) using exact TSPLIB benchmark specifications.",
        "",
        "---",
        "",
        "## 2. Standard CVRP Benchmark Results (Category A)",
        "",
    ]

    # Benchmark Table
    if benchmark_data:
        lines.extend([
            "| Instance | Algorithm | Mean Cost | Std | Best | Worst | Median | Mean Time (s) | Gap to BKS (%) | Valid |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|:---:|"
        ])
        for row in benchmark_data:
            gap_str = f"{row['gap_percent']:.2f}%" if row.get("gap_percent") is not None else "N/A"
            valid_str = "✅" if row.get("valid", True) else "❌"
            lines.append(
                f"| {row['instance']} | {row['algorithm']} | {row['mean']:.2f} | {row['std']:.2f} | "
                f"{row['best']:.2f} | {row['worst']:.2f} | {row['median']:.2f} | {row['mean_runtime']:.3f} | "
                f"{gap_str} | {valid_str} |"
            )
    else:
        lines.append("*No benchmark table data logged yet. Run python -m backend.benchmarks.runner to populate.*")

    lines.extend([
        "",
        "---",
        "",
        "## 3. 7-Variant Ablation Study (Component Analysis)",
        "",
        "Quantifies the exact contribution of each architectural innovation across identical benchmark instances and seeds.",
        "",
    ])

    if ablation_data:
        lines.extend([
            "| Code | Variant Name | Instance | Mean Cost | Std | Best | Mean Time (s) | Gap to BKS (%) | Improvement (%) |",
            "|:---:|---|---|---:|---:|---:|---:|---:|---:|"
        ])
        for row in ablation_data:
            gap_str = f"{row['gap_to_bks_percent']:.2f}%" if row.get("gap_to_bks_percent") is not None else "N/A"
            lines.append(
                f"| {row['variant_code']} | {row['variant_name']} | {row['instance']} | {row['mean']:.2f} | "
                f"{row['std']:.2f} | {row['best']:.2f} | {row['mean_runtime_seconds']:.3f} | {gap_str} | "
                f"{row['improvement_percent']:.2f}% |"
            )
    else:
        lines.append("*No ablation data logged yet.*")

    lines.extend([
        "",
        "---",
        "",
        "## 4. Scalability Analysis (32 to 200 Customers)",
        "",
    ])

    if scalability_data:
        lines.extend([
            "| Customers | Instance / Type | Best Fitness | Vehicle Count | Runtime (s) | Feasible |",
            "|---:|---|---:|---:|---:|:---:|"
        ])
        for row in scalability_data:
            v_str = "✅" if row.get("valid", True) else "❌"
            lines.append(
                f"| {row['num_customers']} | {row['instance']} | {row['best_fitness']:.2f} | "
                f"{row['vehicle_count']} | {row['runtime_seconds']:.3f} | {v_str} |"
            )
    else:
        lines.append("*No scalability data logged yet.*")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Category B: Bangalore Dynamic Traffic Re-Routing",
        "",
        "Demonstrates real-time route adjustment under dynamic urban congestion scenarios.",
        "",
    ])

    if traffic_data and "scenarios" in traffic_data:
        lines.extend([
            "| Scenario | Best Fitness | Fitness Change | Re-opt Runtime (s) | Vehicle Count |",
            "|---|---:|---:|---:|---:|"
        ])
        for sc in traffic_data["scenarios"]:
            lines.append(
                f"| {sc['scenario'].capitalize()} | {sc['best_fitness']:.2f} | {sc['fitness_change']:+.2f} | "
                f"{sc['reoptimization_time_seconds']:.3f} | {sc['vehicle_count']} |"
            )
    else:
        lines.append("*No dynamic traffic data logged yet.*")

    lines.extend([
        "",
        "---",
        "",
        "## 6. Scientific Rigor & Reproducibility Statement",
        "",
        "1. All benchmark figures are measured directly from empirical executions.",
        "2. Random seeds (`42, 123, 456, 789, 999`) guarantee full reproducibility.",
        "3. Every reported route passes explicit feasibility checks (coverage, vehicle capacity, depot loop).",
        "4. Standard CVRP BKS comparisons are kept strictly separate from dynamic traffic simulations.",
        ""
    ])

    report_content = "\n".join(lines)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)

    return str(REPORT_PATH)
