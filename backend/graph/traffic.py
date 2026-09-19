"""
Dynamic traffic edge weight manager.

Manages traffic state updates on the road graph.
Supports loading traffic scenarios from JSON files and
applying them to edge weights.

Blueprint reference: §4.1 Dynamic edge cost, §24 Dynamic Traffic Re-Optimization
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np


class TrafficManager:
    """Manages dynamic traffic state on a road graph.

    The traffic manager applies congestion factors to edges,
    recomputes travel times, and tracks which edges changed
    for efficient cost matrix updates.

    Attributes:
        graph: The road network DiGraph.
        current_scenario: Name of the currently active traffic scenario.
        affected_edges: Set of (u, v) edges modified in the last update.
    """

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self.current_scenario: str = "baseline"
        self.affected_edges: set[tuple[int, int]] = set()
        self._baseline_travel_times: dict[tuple[int, int], float] = {}

        # Cache baseline travel times for reset
        for u, v, data in graph.edges(data=True):
            self._baseline_travel_times[(u, v)] = data.get("travel_time", 1.0)

        # Cache per-attribute min/max for normalization (§4.1)
        self._update_edge_stats()

    def load_scenario(self, scenario_path: str | Path) -> dict[str, Any]:
        """Load a traffic scenario from a JSON file.

        Args:
            scenario_path: Path to the traffic scenario JSON file.

        Returns:
            The parsed scenario data.
        """
        with open(scenario_path, "r", encoding="utf-8") as f:
            scenario = json.load(f)
        return scenario

    def apply_scenario(self, scenario: dict[str, Any]) -> set[tuple[int, int]]:
        """Apply a traffic scenario to the road graph.

        Updates congestion_factor and travel_time for affected edges.
        Returns the set of edges that changed.

        A scenario JSON looks like:
        {
            "name": "moderate_congestion",
            "description": "Rush hour traffic on main roads",
            "edge_updates": [
                {"source": 5, "target": 6, "congestion_factor": 1.8},
                {"source": 10, "target": 11, "congestion_factor": 2.5},
                ...
            ],
            "region_updates": [
                {
                    "center_node": 50,
                    "radius_hops": 3,
                    "congestion_factor": 1.5
                }
            ]
        }

        Args:
            scenario: Parsed scenario dictionary.

        Returns:
            Set of (u, v) tuples for edges that were modified.
        """
        self.affected_edges = set()
        self.current_scenario = scenario.get("name", "unknown")

        # Reset all edges to baseline first
        self._reset_to_baseline()

        # Apply specific edge updates
        edge_updates = scenario.get("edge_updates", [])
        for update in edge_updates:
            source = update["source"]
            target = update["target"]
            congestion = update.get("congestion_factor", 1.0)

            if self.graph.has_edge(source, target):
                self._apply_congestion(source, target, congestion)
                self.affected_edges.add((source, target))

        # Apply region-based updates (all edges within N hops of center)
        region_updates = scenario.get("region_updates", [])
        for region in region_updates:
            center = region["center_node"]
            radius = region.get("radius_hops", 3)
            congestion = region.get("congestion_factor", 1.5)

            if center not in self.graph:
                continue

            # BFS to find all nodes within radius hops
            nearby_nodes = set()
            visited = {center}
            queue = [(center, 0)]
            while queue:
                node, depth = queue.pop(0)
                nearby_nodes.add(node)
                if depth < radius:
                    for neighbor in self.graph.successors(node):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append((neighbor, depth + 1))

            # Apply congestion to all edges between nearby nodes
            for u in nearby_nodes:
                for v in self.graph.successors(u):
                    if v in nearby_nodes:
                        self._apply_congestion(u, v, congestion)
                        self.affected_edges.add((u, v))

        print(
            f"Traffic scenario '{self.current_scenario}': "
            f"{len(self.affected_edges)} edges affected"
        )

        # Refresh normalization bounds for get_edge_cost()
        self._update_edge_stats()

        return self.affected_edges

    def _apply_congestion(self, u: int, v: int, congestion_factor: float) -> None:
        """Apply congestion to a single edge.

        travel_time_congested = travel_time_baseline × congestion_factor

        §4.1: congestion_factor > 1.0 means slower than free flow.
        """
        data = self.graph[u][v]
        baseline_tt = self._baseline_travel_times.get((u, v), data.get("travel_time", 1.0))
        data["congestion_factor"] = congestion_factor
        data["travel_time"] = baseline_tt * congestion_factor

    def _reset_to_baseline(self) -> None:
        """Reset all edges to baseline (free-flow) conditions."""
        for (u, v), baseline_tt in self._baseline_travel_times.items():
            if self.graph.has_edge(u, v):
                data = self.graph[u][v]
                data["congestion_factor"] = 1.0
                data["travel_time"] = baseline_tt

    def _update_edge_stats(self) -> None:
        """Cache per-attribute min/max across all edges for normalization.

        Called once at construction and after every ``apply_scenario`` so
        that ``get_edge_cost`` can perform min-max normalization as
        specified by §4.1.
        """
        tt_vals = []
        dist_vals = []
        cong_vals = []
        for _u, _v, data in self.graph.edges(data=True):
            tt_vals.append(data.get("travel_time", 1.0))
            dist_vals.append(data.get("distance", 1.0))
            cong_vals.append(data.get("congestion_factor", 1.0))

        def _minmax(vals: list[float]) -> tuple[float, float]:
            lo, hi = min(vals), max(vals)
            return (lo, hi) if hi > lo else (lo, lo + 1.0)

        self._tt_min, self._tt_max = _minmax(tt_vals)
        self._dist_min, self._dist_max = _minmax(dist_vals)
        self._cong_min, self._cong_max = _minmax(cong_vals)

    def get_edge_cost(
        self,
        u: int,
        v: int,
        weights: dict[str, float] | None = None,
    ) -> float:
        """Compute the normalized weighted composite cost for a single edge.

        §4.1 Dynamic edge cost (blueprint):
            C_ij = w_time * T_norm + w_distance * D_norm + w_congestion * Q_norm

        Each component is **min-max normalized** to [0, 1] using the
        current graph-wide attribute ranges (updated after every scenario).

        .. note::

            This composite is intended for multi-objective fitness
            evaluation.  Dijkstra shortest-paths operate on the raw
            ``travel_time`` attribute (seconds, already scaled by
            ``congestion_factor``) — see ``shortest_path.py``.

        Args:
            u: Source node.
            v: Target node.
            weights: Objective weights dict with keys
                'travel_time', 'distance', 'congestion'.

        Returns:
            Weighted normalized edge cost (dimensionless).
        """
        if not self.graph.has_edge(u, v):
            return float("inf")

        if weights is None:
            weights = {
                "travel_time": 0.4,
                "distance": 0.3,
                "congestion": 0.2,
            }

        data = self.graph[u][v]

        t_norm = (data.get("travel_time", 1.0) - self._tt_min) / (self._tt_max - self._tt_min)
        d_norm = (data.get("distance", 1.0) - self._dist_min) / (self._dist_max - self._dist_min)
        q_norm = (data.get("congestion_factor", 1.0) - self._cong_min) / (self._cong_max - self._cong_min)

        cost = (
            weights.get("travel_time", 0.4) * t_norm
            + weights.get("distance", 0.3) * d_norm
            + weights.get("congestion", 0.2) * q_norm
        )
        return cost

    def get_traffic_summary(self) -> dict[str, Any]:
        """Get a summary of current traffic state for the API."""
        congestion_factors = []
        for u, v, data in self.graph.edges(data=True):
            congestion_factors.append(data.get("congestion_factor", 1.0))

        cf_array = np.array(congestion_factors)
        return {
            "scenario": self.current_scenario,
            "total_edges": len(congestion_factors),
            "affected_edges": len(self.affected_edges),
            "mean_congestion": float(cf_array.mean()),
            "max_congestion": float(cf_array.max()),
            "congested_edges": int(np.sum(cf_array > 1.1)),
        }


def generate_default_scenarios(
    graph: nx.DiGraph,
    output_dir: str | Path,
    seed: int = 42,
) -> list[Path]:
    """Generate default traffic scenario JSON files.

    Creates 4 scenarios: baseline, moderate, disruption, recovery.

    Args:
        graph: The road network graph.
        output_dir: Directory to write JSON files.
        seed: Random seed.

    Returns:
        List of paths to generated scenario files.
    """
    import random as rng_module

    rng = rng_module.Random(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    nodes = list(graph.nodes())
    edges = list(graph.edges())

    scenarios = []

    # 1. Baseline — free flow
    baseline = {
        "name": "baseline",
        "description": "Normal traffic conditions — free flow on all roads.",
        "edge_updates": [],
        "region_updates": [],
    }
    path = output_dir / "baseline.json"
    _write_scenario(path, baseline)
    scenarios.append(path)

    # 2. Moderate congestion — rush hour on ~20% of edges
    num_congested = max(1, len(edges) // 5)
    congested_edges = rng.sample(edges, min(num_congested, len(edges)))
    moderate = {
        "name": "moderate_congestion",
        "description": "Rush hour: ~20% of roads experience moderate delays.",
        "edge_updates": [
            {
                "source": int(u),
                "target": int(v),
                "congestion_factor": round(rng.uniform(1.3, 2.0), 2),
            }
            for u, v in congested_edges
        ],
        "region_updates": [],
    }
    path = output_dir / "moderate.json"
    _write_scenario(path, moderate)
    scenarios.append(path)

    # 3. Major disruption — severe congestion cascading from a center
    if len(nodes) > 10:
        closure_center = rng.choice(nodes[len(nodes) // 4 : 3 * len(nodes) // 4])
    else:
        closure_center = nodes[0]

    disruption = {
        "name": "major_disruption",
        "description": "Severe congestion near city center with cascading delays.",
        "edge_updates": [],
        "region_updates": [
            {
                "center_node": int(closure_center),
                "radius_hops": 4,
                "congestion_factor": 3.0,
            },
            {
                "center_node": int(closure_center),
                "radius_hops": 8,
                "congestion_factor": 1.8,
            },
        ],
    }
    path = output_dir / "disruption.json"
    _write_scenario(path, disruption)
    scenarios.append(path)

    # 4. Recovery — partial recovery, some lingering congestion
    num_lingering = max(1, len(edges) // 10)
    lingering_edges = rng.sample(edges, min(num_lingering, len(edges)))
    recovery = {
        "name": "recovery",
        "description": "Post-disruption recovery: most roads clear, some lingering delays.",
        "edge_updates": [
            {
                "source": int(u),
                "target": int(v),
                "congestion_factor": round(rng.uniform(1.1, 1.4), 2),
            }
            for u, v in lingering_edges
        ],
        "region_updates": [],
    }
    path = output_dir / "recovery.json"
    _write_scenario(path, recovery)
    scenarios.append(path)

    print(f"Generated {len(scenarios)} traffic scenarios in {output_dir}")
    return scenarios


def _write_scenario(path: Path, scenario: dict) -> None:
    """Write a scenario to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scenario, f, indent=2)
