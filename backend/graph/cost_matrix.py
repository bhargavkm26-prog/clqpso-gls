"""
Stop-to-stop cost matrix generation.

Computes the dense n×n cost matrix between all optimization stops
(depot + customers) using shortest-path distances on the road graph.

The cost matrix is the input to the QPSO optimizer — it bridges
the road-network layer and the VRP optimizer layer.

Blueprint reference: §6 Stop-to-Stop Cost Matrix

Memory: 4n² bytes for float32.
    100 stops →  39 KB
    500 stops → 0.95 MB
  1,000 stops → 3.8 MB
"""

from __future__ import annotations

from typing import Any

import numpy as np
import networkx as nx

from backend.graph.shortest_path import all_pairs_dijkstra, selective_update


class CostMatrix:
    """Dense stop-to-stop cost matrix.

    Stores the shortest-path cost between every pair of
    optimization stops (depot + customers) as a float32 NumPy array.

    Attributes:
        matrix: 2D NumPy array of shape (n_stops, n_stops).
        stops: Ordered list of stop node IDs (index 0 = depot).
        stop_to_idx: Mapping from node ID → matrix index.
        idx_to_stop: Mapping from matrix index → node ID.
    """

    def __init__(
        self,
        graph: nx.DiGraph,
        depot: int,
        customers: list[int],
        weight: str = "travel_time",
    ):
        """Build the cost matrix.

        Args:
            graph: Road network DiGraph with edge weights.
            depot: Depot node ID.
            customers: List of customer node IDs.
            weight: Edge attribute to use as cost.
        """
        self.weight = weight
        self.stops = [depot] + list(customers)
        self.n_stops = len(self.stops)
        self.stop_to_idx = {node: idx for idx, node in enumerate(self.stops)}
        self.idx_to_stop = {idx: node for idx, node in enumerate(self.stops)}

        # Compute all-pairs shortest paths
        self._raw_costs, self._raw_paths = all_pairs_dijkstra(graph, self.stops, weight=weight)

        # Build dense matrix
        self.matrix = self._build_matrix()

        # Store normalization stats for fitness function
        finite_vals = self.matrix[np.isfinite(self.matrix) & (self.matrix > 0)]
        if len(finite_vals) > 0:
            self.min_cost = float(finite_vals.min())
            self.max_cost = float(finite_vals.max())
            self.mean_cost = float(finite_vals.mean())
        else:
            self.min_cost = 0.0
            self.max_cost = 1.0
            self.mean_cost = 0.5

    def _build_matrix(self) -> np.ndarray:
        """Convert dict-of-dicts to dense float32 matrix."""
        matrix = np.full((self.n_stops, self.n_stops), np.inf, dtype=np.float32)

        for i, src in enumerate(self.stops):
            for j, dst in enumerate(self.stops):
                if i == j:
                    matrix[i, j] = 0.0
                elif src in self._raw_costs and dst in self._raw_costs[src]:
                    matrix[i, j] = self._raw_costs[src][dst]

        return matrix

    def cost(self, i: int, j: int) -> float:
        """Get cost between two stops by matrix index.

        Args:
            i: Source stop index (0 = depot).
            j: Target stop index (0 = depot).

        Returns:
            Cost value.
        """
        return float(self.matrix[i, j])

    def cost_by_node(self, src_node: int, dst_node: int) -> float:
        """Get cost between two stops by node ID.

        Args:
            src_node: Source node ID.
            dst_node: Target node ID.

        Returns:
            Cost value.
        """
        i = self.stop_to_idx.get(src_node)
        j = self.stop_to_idx.get(dst_node)
        if i is None or j is None:
            return float("inf")
        return float(self.matrix[i, j])

    def route_cost(self, route_indices: list[int]) -> float:
        """Compute the total cost of a route (sequence of stop indices).

        The route should include depot at start and end:
        [0, c1, c2, ..., cn, 0]

        Args:
            route_indices: Ordered list of stop indices.

        Returns:
            Total route cost. Returns inf if any segment is unreachable.
        """
        total = 0.0
        for k in range(len(route_indices) - 1):
            c = self.cost(route_indices[k], route_indices[k + 1])
            if np.isinf(c):
                return float("inf")
            total += c
        return total

    def get_path(self, src_node: int, dst_node: int) -> list[int]:
        """Get the cached shortest path between two nodes.

        Args:
            src_node: Source node ID.
            dst_node: Target node ID.

        Returns:
            List of node IDs forming the shortest path.
        """
        if src_node in self._raw_paths and dst_node in self._raw_paths[src_node]:
            return self._raw_paths[src_node][dst_node]
        return []

    def update(
        self,
        graph: nx.DiGraph,
        affected_edges: set[tuple[int, int]] | None = None,
    ) -> None:
        """Recompute the cost matrix after traffic changes.

        §24: Recompute affected stop-to-stop costs after edge weight update.

        Args:
            graph: Updated road network graph.
            affected_edges: Set of changed edges (for selective update).
        """
        if affected_edges:
            self._raw_costs, self._raw_paths = selective_update(
                graph, self._raw_costs, self._raw_paths, self.stops, affected_edges, self.weight
            )
        else:
            self._raw_costs, self._raw_paths = all_pairs_dijkstra(graph, self.stops, self.weight)

        self.matrix = self._build_matrix()

        # Update normalization stats
        finite_vals = self.matrix[np.isfinite(self.matrix) & (self.matrix > 0)]
        if len(finite_vals) > 0:
            self.min_cost = float(finite_vals.min())
            self.max_cost = float(finite_vals.max())
            self.mean_cost = float(finite_vals.mean())

    def get_normalized_matrix(self) -> np.ndarray:
        """Get min-max normalized cost matrix.

        §4.1: Normalize so that one unit scale does not dominate.

        Returns:
            Normalized matrix with values in [0, 1].
        """
        if self.max_cost <= self.min_cost:
            return np.zeros_like(self.matrix)

        normalized = (self.matrix - self.min_cost) / (self.max_cost - self.min_cost)
        # Keep diagonal as 0, inf as inf
        np.fill_diagonal(normalized, 0.0)
        normalized[np.isinf(self.matrix)] = np.inf

        return normalized

    def summary(self) -> dict[str, Any]:
        """Get a summary of the cost matrix for logging/API."""
        finite_count = np.sum(np.isfinite(self.matrix) & (self.matrix > 0))
        inf_count = np.sum(np.isinf(self.matrix))
        return {
            "n_stops": self.n_stops,
            "depot_node": self.stops[0],
            "matrix_shape": list(self.matrix.shape),
            "memory_bytes": self.matrix.nbytes,
            "min_cost": self.min_cost,
            "max_cost": self.max_cost,
            "mean_cost": self.mean_cost,
            "finite_pairs": int(finite_count),
            "unreachable_pairs": int(inf_count),
        }

    def __repr__(self) -> str:
        return (
            f"CostMatrix(stops={self.n_stops}, "
            f"shape={self.matrix.shape}, "
            f"memory={self.matrix.nbytes} bytes)"
        )
