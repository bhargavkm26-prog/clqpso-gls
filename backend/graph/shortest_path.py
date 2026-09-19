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
    """Selectively recompute costs only for pairs affected by edge changes.

    §24: When traffic updates arrive, identify affected edges and only
    recompute the stop-to-stop costs that might have changed.

    For a targeted update, we find which source nodes have paths
    that *could* pass through any affected edge, then recompute
    from those sources.

    For simplicity in this implementation, we recompute from any
    source that is within a reasonable hop distance of an affected edge.
    A full implementation would track path membership.

    Args:
        graph: Road network DiGraph.
        existing_costs: Current cost dictionary.
        nodes: List of optimization stop nodes.
        affected_edges: Set of (u, v) edges that changed.
        weight: Edge attribute to use as cost.

    Returns:
        Updated cost dictionary.
    """
    if not affected_edges:
        return existing_costs

    # Find nodes near affected edges
    affected_nodes = set()
    for u, v in affected_edges:
        affected_nodes.add(u)
        affected_nodes.add(v)

    # Recompute from all sources (conservative but correct)
    # A production system would do incremental updates
    updated = all_pairs_dijkstra(graph, nodes, weight=weight)
    return updated
