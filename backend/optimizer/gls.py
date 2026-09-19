"""
Guided Local Search (GLS) Penalty Framework.

Blueprint reference: §15 Guided Local Search (GLS) Component

GLS helps the optimizer escape local optima by augmenting the cost matrix
with penalties for features (edges) that are over-utilized in sub-optimal
solutions.
"""

from __future__ import annotations

from typing import Any

import numpy as np


class GuidedLocalSearch:
    """Manages the GLS penalty framework and augmented cost matrix.

    Features in this context are directed edges between stops (i, j).
    When the optimizer stagnates, edges present in the current best solution
    are penalized based on their cost and current penalty counter.
    """

    def __init__(self, n_stops: int, config: dict[str, Any]):
        """Initialize GLS.

        Args:
            n_stops: Total number of stops (depot + customers).
            config: GLS configuration from default.yaml.
        """
        self.n_stops = n_stops
        
        # Penalties: p_ij for each directed edge
        self.penalties = np.zeros((n_stops, n_stops), dtype=np.float32)
        
        gls_config = config.get("gls", {})
        self.alpha_gls = gls_config.get("alpha_gls", 0.3)
        self.enabled = gls_config.get("enabled", True)
        
        # We need a scaling factor for lambda. It is updated on first call.
        self._lambda = 0.0
        self._lambda_initialized = False

    def get_augmented_cost_matrix(self, base_cost_matrix: np.ndarray) -> np.ndarray:
        """Get the cost matrix augmented with current penalties.

        C'_ij = C_ij + lambda * p_ij

        Args:
            base_cost_matrix: Original stop-to-stop cost matrix.

        Returns:
            Augmented cost matrix.
        """
        if not self.enabled:
            return base_cost_matrix
            
        if not self._lambda_initialized:
            # Initialize lambda based on average edge cost in the initial matrix
            finite_costs = base_cost_matrix[np.isfinite(base_cost_matrix) & (base_cost_matrix > 0)]
            avg_cost = finite_costs.mean() if len(finite_costs) > 0 else 1.0
            
            # The lambda scaling formula and alpha_gls=0.3 are configurable 
            # engineering choices for this project, not values directly taken from the paper.
            self._lambda = self.alpha_gls * (avg_cost / max(1, self.n_stops))
            self._lambda_initialized = True

        return base_cost_matrix + self._lambda * self.penalties

    def update_penalties(
        self,
        routes: list[list[int]],
        base_cost_matrix: np.ndarray,
    ) -> None:
        """Update penalties based on the current best solution.

        Called when QPSO stagnates. Identifies features (edges) with max
        utility and increments their penalty.

        Utility(i, j) = C_ij / (1 + p_ij)

        Args:
            routes: List of routes in the current best solution.
            base_cost_matrix: Original cost matrix.
        """
        if not self.enabled:
            return
            
        # Extract all edges (features) in the current solution
        edges = set()
        DEPOT = 0
        
        for route in routes:
            if not route:
                continue
            stops = [DEPOT] + [c + 1 for c in route] + [DEPOT]
            for k in range(len(stops) - 1):
                edges.add((stops[k], stops[k + 1]))

        if not edges:
            return

        # Calculate utility for all present edges
        max_utility = -1.0
        max_utility_edges = []

        for u, v in edges:
            cost = base_cost_matrix[u, v]
            if np.isinf(cost):
                continue
                
            penalty = self.penalties[u, v]
            utility = cost / (1.0 + penalty)

            # Find maximum utility (within a small tolerance for ties)
            if utility > max_utility + 1e-6:
                max_utility = utility
                max_utility_edges = [(u, v)]
            elif utility > max_utility - 1e-6:
                max_utility_edges.append((u, v))

        # Increment penalty for edges with maximum utility
        for u, v in max_utility_edges:
            self.penalties[u, v] += 1.0
