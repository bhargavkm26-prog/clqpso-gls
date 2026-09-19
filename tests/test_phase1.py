"""
Phase 1 verification test.

Tests:
1. Synthetic graph builds correctly
2. Traffic scenarios apply correctly
3. Shortest paths compute correctly
4. Cost matrix builds correctly
5. Cost matrix updates after traffic change
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import load_config, get_graph_config, get_vrp_config
from backend.graph.network import build_graph, place_customers_and_depot
from backend.graph.traffic import TrafficManager, generate_default_scenarios
from backend.graph.cost_matrix import CostMatrix


def test_phase1():
    """Run all Phase 1 verification tests."""

    print("=" * 60)
    print("PHASE 1 VERIFICATION TEST")
    print("=" * 60)

    # 1. Load config
    print("\n[1/6] Loading configuration...")
    config = load_config()
    graph_config = get_graph_config(config)
    vrp_config = get_vrp_config(config)
    print(f"  ✓ Config loaded: source={graph_config['source']}")

    # 2. Build graph
    print("\n[2/6] Building synthetic road graph...")
    G = build_graph(graph_config)
    assert G.number_of_nodes() > 0, "Graph has no nodes!"
    assert G.number_of_edges() > 0, "Graph has no edges!"
    print(f"  ✓ {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Verify edge attributes
    sample_edge = list(G.edges(data=True))[0]
    u, v, data = sample_edge
    assert "distance" in data, "Edge missing 'distance'"
    assert "travel_time" in data, "Edge missing 'travel_time'"
    assert "congestion_factor" in data, "Edge missing 'congestion_factor'"
    assert data["congestion_factor"] == 1.0, "Initial congestion should be 1.0"
    print(f"  ✓ Edge ({u}→{v}): dist={data['distance']:.1f}m, time={data['travel_time']:.1f}s")

    # 3. Place customers and depot
    print("\n[3/6] Placing depot and customers...")
    num_customers = min(vrp_config.get("num_customers", 50), G.number_of_nodes() - 1)
    depot, customers, demands = place_customers_and_depot(
        G, num_customers=num_customers, seed=42
    )
    assert depot not in customers, "Depot should not be a customer!"
    assert len(customers) == num_customers, f"Expected {num_customers} customers"
    assert all(d > 0 for d in demands.values()), "All demands must be positive"
    print(f"  ✓ Depot={depot}, {len(customers)} customers, total demand={sum(demands.values())}")

    # 4. Build cost matrix
    print("\n[4/6] Building stop-to-stop cost matrix...")
    cm = CostMatrix(G, depot, customers)
    assert cm.matrix.shape == (num_customers + 1, num_customers + 1)
    assert cm.cost(0, 0) == 0.0, "Self-cost should be 0"

    # Check that at least some paths exist
    reachable = sum(1 for i in range(cm.n_stops) for j in range(cm.n_stops)
                    if i != j and cm.cost(i, j) < float("inf"))
    total_pairs = cm.n_stops * (cm.n_stops - 1)
    reach_pct = 100.0 * reachable / total_pairs if total_pairs > 0 else 0

    print(f"  ✓ {cm}")
    print(f"  ✓ Reachable pairs: {reachable}/{total_pairs} ({reach_pct:.1f}%)")
    print(f"  ✓ Cost range: [{cm.min_cost:.2f}, {cm.max_cost:.2f}]")
    assert reach_pct > 50, f"Too few reachable pairs ({reach_pct:.1f}%)"

    # 5. Traffic scenarios
    print("\n[5/6] Testing traffic scenarios...")
    traffic_mgr = TrafficManager(G)

    # Generate scenario files
    scenario_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "traffic_scenarios")
    scenario_paths = generate_default_scenarios(G, scenario_dir, seed=42)
    assert len(scenario_paths) == 4, "Should generate 4 scenarios"

    # Apply moderate congestion
    scenario = traffic_mgr.load_scenario(scenario_paths[1])  # moderate
    affected = traffic_mgr.apply_scenario(scenario)
    assert len(affected) > 0, "Moderate congestion should affect some edges"

    summary = traffic_mgr.get_traffic_summary()
    print(f"  ✓ Scenario: {summary['scenario']}")
    print(f"  ✓ Affected edges: {summary['affected_edges']}")
    print(f"  ✓ Mean congestion: {summary['mean_congestion']:.3f}")
    print(f"  ✓ Max congestion: {summary['max_congestion']:.2f}")

    # 6. Cost matrix update after traffic change
    print("\n[6/6] Testing cost matrix update after traffic change...")
    cost_before = cm.cost(0, 1)
    cm.update(G, affected_edges=affected)
    cost_after = cm.cost(0, 1)

    print(f"  ✓ Cost (0→1) before: {cost_before:.2f}")
    print(f"  ✓ Cost (0→1) after:  {cost_after:.2f}")

    # Verify normalized matrix
    norm = cm.get_normalized_matrix()
    finite_norm = norm[~(norm == 0) & (norm < float("inf"))]
    if len(finite_norm) > 0:
        assert finite_norm.min() >= 0.0, "Normalized values should be >= 0"
        assert finite_norm.max() <= 1.001, "Normalized values should be <= 1"
        print(f"  ✓ Normalized range: [{finite_norm.min():.4f}, {finite_norm.max():.4f}]")

    # Final summary
    print("\n" + "=" * 60)
    print("✅ ALL PHASE 1 TESTS PASSED!")
    print("=" * 60)
    print(f"\nGraph: {G.number_of_nodes()} road nodes, {G.number_of_edges()} edges")
    print(f"VRP:   {len(customers)} customers, 1 depot")
    print(f"Matrix: {cm.matrix.shape} ({cm.matrix.nbytes} bytes)")
    print(f"Traffic: 4 scenarios generated")


if __name__ == "__main__":
    test_phase1()
