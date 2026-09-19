"""
Statistical Metrics Module for CVRP Benchmarks.

Calculates descriptive statistics (mean, std, min, max, median, runtime stats),
percentage gap to BKS, and non-parametric statistical tests.
"""

import numpy as np
from typing import Any, Sequence
from scipy import stats
from backend.benchmarks.bks import get_bks_value, calculate_gap_percent

def compute_statistics(values: Sequence[float]) -> dict[str, float]:
    """Compute summary statistics for a sequence of numeric values."""
    if not values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "median": 0.0}
    
    arr = np.array(values, dtype=np.float64)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "median": float(np.median(arr))
    }

def compute_runtime_statistics(runtimes: Sequence[float]) -> dict[str, float]:
    """Compute statistics for execution runtimes."""
    stats_dict = compute_statistics(runtimes)
    return {
        "mean_runtime": stats_dict["mean"],
        "min_runtime": stats_dict["min"],
        "max_runtime": stats_dict["max"],
        "std_runtime": stats_dict["std"]
    }

def compute_gap(best_cost: float, instance_name: str) -> dict[str, Any]:
    """Compute gap-to-BKS for an instance.
    
    Returns:
        Dict with 'bks', 'gap_percent', 'verified_flag'.
    """
    bks = get_bks_value(instance_name)
    if bks is None:
        return {"bks": None, "gap_percent": None, "flag": "NO_BKS"}
    
    gap = calculate_gap_percent(best_cost, bks)
    flag = "VALID"
    if gap < -0.01:
        flag = "BELOW_BKS_VERIFY_REQUIRED"
        
    return {
        "bks": bks,
        "gap_percent": float(gap),
        "flag": flag
    }

def wilcoxon_test(data_a: Sequence[float], data_b: Sequence[float]) -> dict[str, Any]:
    """Perform Wilcoxon signed-rank test between two algorithm results."""
    arr_a = np.array(data_a)
    arr_b = np.array(data_b)
    
    if len(arr_a) != len(arr_b) or len(arr_a) < 5:
        return {"statistic": None, "p_value": None, "significant": False, "note": "Sample size < 5 or unequal"}
        
    diffs = arr_a - arr_b
    if np.all(diffs == 0):
        return {"statistic": 0.0, "p_value": 1.0, "significant": False, "note": "Identical results"}
        
    try:
        res = stats.wilcoxon(arr_a, arr_b)
        return {
            "statistic": float(res.statistic),
            "p_value": float(res.pvalue),
            "significant": bool(res.pvalue < 0.05)
        }
    except Exception as e:
        return {"statistic": None, "p_value": None, "significant": False, "note": str(e)}
