"""
Shortest-path computation on the road graph.

Uses Dijkstra's algorithm (via NetworkX) to compute
shortest paths between any two nodes, weighted by the
current dynamic edge costs.

Blueprint reference: §6 Stop-to-Stop Cost Matrix, §32 Role of Dijkstra
"""

from __future__ import annotations

from typing import Any

import networkx as nx
import numpy as np


def shortest_path_cost(
    graph: nx.DiGraph,
    source: int,
    target: int,
    weight: str = "travel_time",
) -> float:
    """Compute the shortest-path cost between two nodes.

    Args:
        graph: Road network DiGraph.
        source: Source node ID.
        target: Target node ID.
        weight: Edge attribute to use as cost (default: travel_time).

    Returns:
        Shortest-path cost. Returns float('inf') if no path exists.
    """
    try:
        cost = nx.dijkstra_path_length(graph, source, target, weight=weight)
        return float(cost)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return float("inf")


def shortest_path_nodes(
    graph: nx.DiGraph,
    source: int,
    target: int,
    weight: str = "travel_time",
) -> list[int]:
    """Compute the shortest path (list of nodes) between two nodes.

    Args:
        graph: Road network DiGraph.
        source: Source node ID.
        target: Target node ID.
        weight: Edge attribute to use as cost.

    Returns:
        List of node IDs forming the shortest path.
        Returns empty list if no path exists.
    """
    try:
        return nx.dijkstra_path(graph, source, target, weight=weight)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def all_pairs_dijkstra(
    graph: nx.DiGraph,
    nodes: list[int],
    weight: str = "travel_time",
) -> dict[int, dict[int, float]]:
    """Compute shortest-path costs between all pairs of specified nodes.

    Uses Dijkstra from each node. For N stops on a graph with M edges,
    complexity is O(N × (M + V log V)).

    Args:
        graph: Road network DiGraph.
        nodes: List of node IDs to compute distances between.
        weight: Edge attribute to use as cost.

    Returns:
        Nested dict: costs[source][target] = shortest_path_cost.
    """
    costs: dict[int, dict[int, float]] = {}
    node_set = set(nodes)

    for source in nodes:
        try:
            # Compute shortest paths from source to all reachable nodes
            lengths = nx.single_source_dijkstra_path_length(
                graph, source, weight=weight
            )
            costs[source] = {}
            for target in nodes:
                if target == source:
                    costs[source][target] = 0.0
                elif target in lengths:
                    costs[source][target] = float(lengths[target])
                else:
                    costs[source][target] = float("inf")
        except nx.NodeNotFound:
            costs[source] = {t: float("inf") for t in nodes}
            costs[source][source] = 0.0

    return costs


def selective_update(
    graph: nx.DiGraph,
    existing_costs: dict[int, dict[int, float]],
    nodes: list[int],
    affected_edges: set[tuple[int, int]],
    weight: str = "travel_time",
) -> dict[int, dict[int, float]]:
    """Recompute the stop-to-stop cost matrix after edge-weight changes.

    §24 envisions identifying which stop-to-stop pairs are affected by
    the changed edges and recomputing only those.  Implementing that
    correctly requires tracking which edges lie on each cached shortest
    path — a non-trivial bookkeeping overhead.

    **Current behaviour (conservative fallback):** this function performs
    a full ``all_pairs_dijkstra`` recomputation regardless of which edges
    changed.  This is always correct, and on graphs with ≤ 1 000 stops
    the runtime is negligible.  The ``affected_edges`` parameter is
    accepted (and short-circuit-checked for emptiness) so that callers
    do not need to change when a future incremental implementation is
    added.

    Args:
        graph: Road network DiGraph.
        existing_costs: Current cost dictionary (unused in this
            conservative implementation — kept for API compatibility).
        nodes: List of optimization stop nodes.
        affected_edges: Set of (u, v) edges that changed.
            If empty, the existing costs are returned unchanged.
        weight: Edge attribute to use as cost.

    Returns:
        Updated cost dictionary (full recomputation).
    """
    if not affected_edges:
        return existing_costs

    # Conservative full recomputation — always correct.
    return all_pairs_dijkstra(graph, nodes, weight=weight)
