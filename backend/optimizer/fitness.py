"""
Multi-objective fitness function for VRP solutions.

Blueprint reference: §12 Fitness Function

Fitness = w_time      × normalized_travel_time
        + w_distance  × normalized_distance
        + w_congestion× normalized_congestion_cost
        + w_vehicles  × vehicle_count_penalty
        + w_violation × constraint_violation

Lower is better.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from backend.optimizer.split import SplitResult


class FitnessEvaluator:
    """Evaluates the fitness of VRP solutions.

    Combines multiple objectives into a single scalar value
    using configurable weights. All components are normalized
    before weighting (§4.1).

    Attributes:
        weights: Objective weight dictionary.
        cost_matrix: Stop-to-stop cost matrix.
        demands: Customer demands array.
        vehicle_capacity: Vehicle capacity.
        max_vehicles: Maximum fleet size (None = unlimited).
    """

    def __init__(
        self,
        cost_matrix: np.ndarray,
        demands: np.ndarray,
        vehicle_capacity: float,
        max_vehicles: int | None = None,
        weights: dict[str, float] | None = None,
        normalization_stats: dict[str, float] | None = None,
    ):
        """Initialize the fitness evaluator.

        Args:
            cost_matrix: Stop-to-stop cost matrix (index 0 = depot).
            demands: Customer demands array.
            vehicle_capacity: Vehicle capacity.
            max_vehicles: Maximum fleet size.
            weights: Objective weights. Defaults to config values.
            normalization_stats: Pre-computed normalization stats
                with keys 'min_cost', 'max_cost', 'mean_cost'.
        """
        self.cost_matrix = cost_matrix
        self.demands = demands
        self.vehicle_capacity = vehicle_capacity
        self.max_vehicles = max_vehicles

        self.weights = weights or {
            "travel_time": 0.4,
            "distance": 0.3,
            "congestion": 0.2,
            "vehicle_count": 0.1,
        }

        # Normalization: use provided stats or compute from matrix
        if normalization_stats:
            self.min_cost = normalization_stats.get("min_cost", 0.0)
            self.max_cost = normalization_stats.get("max_cost", 1.0)
        else:
            finite = cost_matrix[np.isfinite(cost_matrix) & (cost_matrix > 0)]
            self.min_cost = float(finite.min()) if len(finite) > 0 else 0.0
            self.max_cost = float(finite.max()) if len(finite) > 0 else 1.0

        # Penalty coefficient for constraint violations
        self.violation_penalty = 1000.0

    def evaluate(self, split_result: SplitResult) -> float:
        """Evaluate the fitness of a Split result.

        Args:
            split_result: The decoded route partition.

        Returns:
            Scalar fitness value (lower is better).
        """
        if not split_result.feasible:
            return self._infeasible_fitness(split_result)

        # Total route cost (main objective: minimize travel time/cost)
        total_cost = split_result.total_cost

        # Normalize cost to [0, 1] range
        cost_range = self.max_cost - self.min_cost
        if cost_range > 0:
            normalized_cost = (total_cost - self.min_cost * split_result.num_vehicles) / (
                cost_range * split_result.num_vehicles + 1e-10
            )
        else:
            normalized_cost = 0.0

        # Vehicle count penalty (fewer vehicles is better)
        n_customers = len(self.demands)
        min_vehicles = max(1, int(np.ceil(sum(self.demands) / self.vehicle_capacity)))
        vehicle_penalty = max(0, split_result.num_vehicles - min_vehicles) / max(min_vehicles, 1)

        # Combine objectives
        fitness = (
            self.weights.get("travel_time", 0.4) * normalized_cost
            + self.weights.get("vehicle_count", 0.1) * vehicle_penalty
        )

        return fitness

    def evaluate_detailed(self, split_result: SplitResult) -> dict[str, Any]:
        """Evaluate with detailed breakdown for logging/API.

        Args:
            split_result: The decoded route partition.

        Returns:
            Dictionary with fitness breakdown.
        """
        fitness = self.evaluate(split_result)

        # Compute per-route details
        route_details = []
        for i, route in enumerate(split_result.routes):
            load = sum(float(self.demands[c]) for c in route)
            route_details.append({
                "route_id": i,
                "customers": route,
                "num_customers": len(route),
                "load": load,
                "capacity_used": load / self.vehicle_capacity,
                "cost": split_result.route_costs[i] if i < len(split_result.route_costs) else 0,
            })

        return {
            "fitness": fitness,
            "total_cost": split_result.total_cost,
            "num_vehicles": split_result.num_vehicles,
            "feasible": split_result.feasible,
            "routes": route_details,
            "total_demand": float(sum(self.demands)),
            "vehicle_capacity": self.vehicle_capacity,
        }

    def _infeasible_fitness(self, split_result: SplitResult) -> float:
        """Compute fitness for infeasible solutions with penalty.

        §11: Infeasible solutions get explicit violation penalties.
        """
        # Base cost (may be inf for truly broken solutions)
        base = split_result.total_cost if np.isfinite(split_result.total_cost) else self.max_cost * 10

        # Capacity violations
        cap_violation = 0.0
        for route in split_result.routes:
            load = sum(float(self.demands[c]) for c in route)
            excess = max(0, load - self.vehicle_capacity)
            cap_violation += excess / self.vehicle_capacity

        # Fleet size violation
        fleet_violation = 0.0
        if self.max_vehicles is not None:
            excess_vehicles = max(0, split_result.num_vehicles - self.max_vehicles)
            fleet_violation = excess_vehicles / max(self.max_vehicles, 1)

        # Total with penalty
        cost_range = self.max_cost - self.min_cost
        if cost_range > 0:
            normalized_base = base / (cost_range * max(split_result.num_vehicles, 1) + 1e-10)
        else:
            normalized_base = 1.0

        fitness = normalized_base + self.violation_penalty * (cap_violation + fleet_violation)
        return fitness

    def batch_evaluate(self, split_results: list[SplitResult]) -> np.ndarray:
        """Evaluate a batch of solutions.

        Args:
            split_results: List of Split results.

        Returns:
            1D array of fitness values.
        """
        return np.array([self.evaluate(sr) for sr in split_results], dtype=np.float64)
