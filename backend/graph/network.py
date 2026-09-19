"""
Road network graph construction.

Supports two modes:
1. OSMnx — download real road network (e.g., Bangalore)
2. Synthetic — generate a grid network for testing/fallback

The graph is stored as a NetworkX DiGraph with edge attributes:
    - distance (meters)
    - speed_limit (km/h)
    - travel_time (seconds)
    - congestion_factor (1.0 = free flow, >1.0 = congested)

Blueprint reference: §4 Road-Network Model, §5 Optimization Stops vs Road Nodes
"""

from __future__ import annotations

import math
import random
from typing import Any

import networkx as nx
import numpy as np


def build_graph(config: dict[str, Any]) -> nx.DiGraph:
    """Build a road network graph based on configuration.

    Args:
        config: Graph configuration from default.yaml.

    Returns:
        NetworkX DiGraph with edge attributes.
    """
    source = config.get("source", "synthetic")

    if source == "osmnx":
        return _build_osmnx_graph(config)
    elif source == "synthetic":
        return _build_synthetic_graph(config)
    elif source == "custom_json":
        raise NotImplementedError("Custom JSON graph loading not yet implemented")
    else:
        raise ValueError(f"Unknown graph source: {source}")


def _build_osmnx_graph(config: dict[str, Any]) -> nx.DiGraph:
    """Download a real road network using OSMnx.

    Requires: pip install osmnx

    OSMnx returns a ``MultiDiGraph`` (parallel edges for different road
    segments between the same intersection pair).  We flatten it to a
    plain ``DiGraph`` so that ``G[u][v]`` returns a single edge-data dict
    — the same access pattern used by traffic.py, shortest_path.py, and
    cost_matrix.py.

    **Parallel-edge rule**: when multiple edges exist for the same (u, v)
    pair, we keep the one with the lowest free-flow ``travel_time``
    (computed from ``length`` and the parsed ``maxspeed``).  All standard
    edge attributes are preserved: distance, speed_limit, travel_time,
    congestion_factor, and status.

    **Speed-unit handling**: OSMnx ``maxspeed`` tags may contain "mph"
    suffixes.  These are detected and converted to km/h.  A documented
    fallback of 40 km/h is used when speed data is missing or unparseable.

    Args:
        config: Must contain 'city' and 'network_type'.

    Returns:
        NetworkX DiGraph with normalized edge attributes.
    """
    try:
        import osmnx as ox
    except ImportError:
        print("WARNING: osmnx not installed. Falling back to synthetic graph.")
        return _build_synthetic_graph(config)

    city = config.get("city", "Koramangala, Bangalore, Karnataka, India")
    network_type = config.get("network_type", "drive")

    print(f"Downloading road network for: {city}")
    G_multi = ox.graph_from_place(city, network_type=network_type)

    # ------------------------------------------------------------------
    # Step 1: Normalize attributes on every edge of the MultiDiGraph
    # ------------------------------------------------------------------
    for u, v, key, data in G_multi.edges(data=True, keys=True):
        # Distance in meters
        if "length" in data:
            data["distance"] = float(data["length"])
        else:
            data["distance"] = 100.0  # default 100 m

        # Speed limit in km/h
        maxspeed = data.get("maxspeed", None)
        if isinstance(maxspeed, list):
            maxspeed = maxspeed[0]
        if maxspeed is not None:
            try:
                raw = str(maxspeed)
                if "mph" in raw.lower():
                    # Convert miles-per-hour → km/h
                    numeric = float(raw.lower().replace("mph", "").strip())
                    data["speed_limit"] = numeric * 1.609344
                else:
                    # Assume km/h (strip optional unit suffix)
                    numeric = float(raw.lower().replace("km/h", "").strip())
                    data["speed_limit"] = numeric
            except (ValueError, TypeError):
                data["speed_limit"] = 40.0  # fallback: unparseable
        else:
            data["speed_limit"] = 40.0  # fallback: missing speed data

        # Free-flow travel time in seconds  (distance_m / speed_m_per_s)
        speed_ms = data["speed_limit"] * 1000.0 / 3600.0  # km/h → m/s
        data["travel_time"] = data["distance"] / max(speed_ms, 0.1)

        # Congestion factor (1.0 = free flow)
        data["congestion_factor"] = 1.0

        # Edge status
        data.setdefault("status", "active")

    # ------------------------------------------------------------------
    # Step 2: Flatten MultiDiGraph → DiGraph
    # For each (u, v) pair keep the edge with the lowest travel_time.
    # ------------------------------------------------------------------
    G = nx.DiGraph()
    G.graph.update(G_multi.graph)
    G.add_nodes_from(G_multi.nodes(data=True))

    for u, v, _key, data in G_multi.edges(data=True, keys=True):
        if G.has_edge(u, v):
            if data["travel_time"] >= G[u][v]["travel_time"]:
                continue  # keep existing faster edge
        G.add_edge(u, v, **data)

    print(f"Graph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def _build_synthetic_graph(config: dict[str, Any]) -> nx.DiGraph:
    """Generate a synthetic grid road network for testing.

    Creates a grid graph simulating city blocks with realistic
    edge attributes (distance, speed, travel time).

    Args:
        config: Must contain 'synthetic' sub-config with
            grid_size, edge_length, speed_limit.

    Returns:
        NetworkX DiGraph with edge attributes.
    """
    synth_config = config.get("synthetic", {})
    grid_size = synth_config.get("grid_size", 20)
    edge_length = synth_config.get("edge_length", 200)  # meters
    base_speed = synth_config.get("speed_limit", 40)  # km/h

    G = nx.DiGraph()

    # Create grid nodes with (x, y) positions
    for row in range(grid_size):
        for col in range(grid_size):
            node_id = row * grid_size + col
            G.add_node(
                node_id,
                x=col * edge_length,
                y=row * edge_length,
                pos=(col * edge_length, row * edge_length),
            )

    # Create edges (4-connected grid, both directions)
    rng = random.Random(42)  # deterministic for reproducibility
    for row in range(grid_size):
        for col in range(grid_size):
            node = row * grid_size + col

            # Right neighbor
            if col < grid_size - 1:
                right = row * grid_size + (col + 1)
                _add_road_edge(G, node, right, edge_length, base_speed, rng)
                _add_road_edge(G, right, node, edge_length, base_speed, rng)

            # Down neighbor
            if row < grid_size - 1:
                down = (row + 1) * grid_size + col
                _add_road_edge(G, node, down, edge_length, base_speed, rng)
                _add_road_edge(G, down, node, edge_length, base_speed, rng)

    # Add some diagonal shortcuts (simulating arterial roads)
    for row in range(0, grid_size - 2, 3):
        for col in range(0, grid_size - 2, 3):
            node = row * grid_size + col
            diag = (row + 2) * grid_size + (col + 2)
            diag_dist = edge_length * math.sqrt(8)  # 2√2 blocks
            arterial_speed = base_speed * 1.5  # faster arterial road
            _add_road_edge(G, node, diag, diag_dist, arterial_speed, rng)
            _add_road_edge(G, diag, node, diag_dist, arterial_speed, rng)

    print(
        f"Synthetic graph: {G.number_of_nodes()} nodes, "
        f"{G.number_of_edges()} edges ({grid_size}×{grid_size} grid)"
    )
    return G


def _add_road_edge(
    G: nx.DiGraph,
    u: int,
    v: int,
    distance: float,
    base_speed: float,
    rng: random.Random,
) -> None:
    """Add a road edge with realistic attributes.

    Adds slight randomness to speed to simulate natural road variation.
    """
    # Slight random variation in speed (±15%)
    speed_variation = 1.0 + rng.uniform(-0.15, 0.15)
    speed = base_speed * speed_variation

    # Travel time = distance / speed
    speed_ms = speed * 1000.0 / 3600.0  # km/h → m/s
    travel_time = distance / max(speed_ms, 0.1)

    G.add_edge(
        u,
        v,
        distance=distance,
        speed_limit=base_speed,
        estimated_speed=speed,
        travel_time=travel_time,
        congestion_factor=1.0,  # free flow
        status="active",
    )


def place_customers_and_depot(
    G: nx.DiGraph,
    num_customers: int,
    depot_index: int = 0,
    seed: int = 42,
) -> tuple[int, list[int], dict[int, int]]:
    """Place depot and customers on graph nodes.

    This implements the critical distinction from §5:
    road graph nodes ≠ optimization stops.

    Args:
        G: Road network graph.
        num_customers: Number of customer stops to place.
        depot_index: Which graph node serves as the depot.
        seed: Random seed for reproducible placement.

    Returns:
        Tuple of (depot_node, customer_nodes, demand_dict)
        where demand_dict maps customer_node → demand.
    """
    rng = random.Random(seed)
    nodes = list(G.nodes())

    if depot_index >= len(nodes):
        depot_index = 0

    depot_node = nodes[depot_index]

    # Select customer nodes (exclude depot)
    available = [n for n in nodes if n != depot_node]
    if num_customers > len(available):
        num_customers = len(available)

    customer_nodes = sorted(rng.sample(available, num_customers))

    # Generate random demands (1-30 units)
    demand_dict = {node: rng.randint(1, 30) for node in customer_nodes}

    print(
        f"Placed depot at node {depot_node}, "
        f"{len(customer_nodes)} customers with demands {min(demand_dict.values())}-{max(demand_dict.values())}"
    )

    return depot_node, customer_nodes, demand_dict


def get_node_positions(G: nx.DiGraph) -> dict[int, tuple[float, float]]:
    """Get (x, y) positions for all nodes (for visualization).

    Returns:
        Dictionary mapping node_id → (x, y).
    """
    positions = {}
    for node, data in G.nodes(data=True):
        if "x" in data and "y" in data:
            positions[node] = (data["x"], data["y"])
        elif "pos" in data:
            positions[node] = data["pos"]
        else:
            positions[node] = (0.0, 0.0)
    return positions
