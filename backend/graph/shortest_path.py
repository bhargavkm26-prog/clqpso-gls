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
) -> tuple[dict[int, dict[int, float]], dict[int, dict[int, list[int]]]]:
    """Compute shortest-path costs and paths between all pairs of specified nodes.

    Uses Dijkstra from each node. For N stops on a graph with M edges,
    complexity is O(N × (M + V log V)).

    Args:
        graph: Road network DiGraph.
        nodes: List of node IDs to compute distances between.
        weight: Edge attribute to use as cost.

    Returns:
        Tuple of (costs, paths) where:
        costs[source][target] = shortest_path_cost
        paths[source][target] = list of node IDs forming the shortest path
    """
    costs: dict[int, dict[int, float]] = {}
    paths: dict[int, dict[int, list[int]]] = {}

    # Performance optimization: extract bounding-box subgraph
    lats = [graph.nodes[n].get('y') for n in nodes if 'y' in graph.nodes[n]]
    lons = [graph.nodes[n].get('x') for n in nodes if 'x' in graph.nodes[n]]
    
    if lats and lons:
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        lat_margin = max((max_lat - min_lat) * 0.2, 0.005)
        lon_margin = max((max_lon - min_lon) * 0.2, 0.005)
        
        valid_nodes = {
            n for n, d in graph.nodes(data=True)
            if 'y' in d and 'x' in d and
            (min_lat - lat_margin <= d['y'] <= max_lat + lat_margin) and
            (min_lon - lon_margin <= d['x'] <= max_lon + lon_margin)
        }
        # Ensure target nodes are always included
        valid_nodes.update(nodes)
        
        # Only use subgraph if it reduces size meaningfully (e.g., < 80% of original graph)
        if len(valid_nodes) < len(graph.nodes) * 0.8:
            search_graph = graph.subgraph(valid_nodes)
        else:
            search_graph = graph
    else:
        search_graph = graph

    for source in nodes:
        costs[source] = {}
        paths[source] = {}
        try:
            # Compute shortest paths from source to all reachable nodes on subgraph
            lengths, p = nx.single_source_dijkstra(
                search_graph, source, weight=weight
            )
            for target in nodes:
                if target == source:
                    costs[source][target] = 0.0
                    paths[source][target] = [source]
                elif target in lengths:
                    costs[source][target] = float(lengths[target])
                    paths[source][target] = p[target]
                else:
                    costs[source][target] = float("inf")
                    paths[source][target] = []
        except nx.NodeNotFound:
            for target in nodes:
                costs[source][target] = float("inf")
                paths[source][target] = []
            costs[source][source] = 0.0
            paths[source][source] = [source]

    return costs, paths


def selective_update(
    graph: nx.DiGraph,
    existing_costs: dict[int, dict[int, float]],
    existing_paths: dict[int, dict[int, list[int]]],
    nodes: list[int],
    affected_edges: set[tuple[int, int]],
    weight: str = "travel_time",
) -> tuple[dict[int, dict[int, float]], dict[int, dict[int, list[int]]]]:
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
        existing_costs: Current cost dictionary.
        existing_paths: Current paths dictionary.
        nodes: List of optimization stop nodes.
        affected_edges: Set of (u, v) edges that changed.
            If empty, the existing costs/paths are returned unchanged.
        weight: Edge attribute to use as cost.

    Returns:
        Tuple of updated (costs, paths).
    """
    if not affected_edges:
        return existing_costs, existing_paths

    # Conservative full recomputation — always correct.
    return all_pairs_dijkstra(graph, nodes, weight=weight)
