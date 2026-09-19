"""
TSPLIB CVRP Instance Loader.

Parses standard CVRP benchmark files (.vrp) and returns a structured object
containing nodes, coordinates, demands, capacity, and Euclidean cost matrix.
"""

import os
from pathlib import Path
from dataclasses import dataclass
import numpy as np

INSTANCES_DIR = Path(__file__).resolve().parent / "instances"

@dataclass
class CVRPInstance:
    name: str
    dimension: int
    num_customers: int
    vehicle_capacity: float
    vehicles: int
    depot_index: int
    depot_coord: tuple[float, float]
    coords: np.ndarray  # shape (dimension, 2) where row 0 is depot
    demands: np.ndarray  # shape (num_customers,) for customers 1..n
    all_demands: np.ndarray # shape (dimension,) including depot 0
    cost_matrix: np.ndarray  # shape (dimension, dimension)

def load_cvrp_instance(name_or_path: str) -> CVRPInstance:
    """Load a standard CVRP benchmark instance.
    
    Args:
        name_or_path: Instance name (e.g., 'A-n32-k5') or full file path.
        
    Returns:
        CVRPInstance structured dataclass.
    """
    path = Path(name_or_path)
    if not path.exists():
        path = INSTANCES_DIR / f"{name_or_path}.vrp"
        if not path.exists():
            path = INSTANCES_DIR / name_or_path
            
    if not path.exists():
        raise FileNotFoundError(f"CVRP benchmark instance not found: {name_or_path}")

    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    name = path.stem
    dimension = 0
    capacity = 100.0
    vehicles = 5

    coord_section = False
    demand_section = False
    coords_dict = {}
    demands_dict = {}

    for line in lines:
        if line.startswith("NAME"):
            name = line.split(":")[-1].strip()
        elif line.startswith("DIMENSION"):
            dimension = int(line.split(":")[-1].strip())
        elif line.startswith("CAPACITY"):
            capacity = float(line.split(":")[-1].strip())
        elif line.startswith("COMMENT") and "trucks:" in line:
            # Extract vehicle count if present
            try:
                part = line.split("trucks:")[-1]
                vehicles = int(part.split(",")[0].strip())
            except Exception:
                pass
        elif line == "NODE_COORD_SECTION":
            coord_section = True
            demand_section = False
            continue
        elif line == "DEMAND_SECTION":
            coord_section = False
            demand_section = True
            continue
        elif line == "DEPOT_SECTION":
            coord_section = False
            demand_section = False
            continue
        elif line == "EOF":
            break

        if coord_section:
            parts = line.split()
            if len(parts) >= 3:
                node_id = int(parts[0])
                x, y = float(parts[1]), float(parts[2])
                coords_dict[node_id] = (x, y)
        elif demand_section:
            parts = line.split()
            if len(parts) >= 2:
                node_id = int(parts[0])
                d = float(parts[1])
                demands_dict[node_id] = d

    if dimension == 0:
        dimension = len(coords_dict)

    # 1-indexed to 0-indexed matrix construction (Node 1 = Depot = Index 0)
    coords = np.zeros((dimension, 2), dtype=np.float64)
    all_demands = np.zeros(dimension, dtype=np.float64)

    for nid in range(1, dimension + 1):
        idx = nid - 1
        coords[idx] = coords_dict.get(nid, (0.0, 0.0))
        all_demands[idx] = demands_dict.get(nid, 0.0)

    num_customers = dimension - 1
    customer_demands = all_demands[1:]

    # Compute Euclidean distance matrix (float64)
    cost_matrix = np.zeros((dimension, dimension), dtype=np.float64)
    for i in range(dimension):
        for j in range(dimension):
            if i != j:
                dx = coords[i, 0] - coords[j, 0]
                dy = coords[i, 1] - coords[j, 1]
                cost_matrix[i, j] = np.sqrt(dx * dx + dy * dy)

    return CVRPInstance(
        name=name,
        dimension=dimension,
        num_customers=num_customers,
        vehicle_capacity=capacity,
        vehicles=vehicles,
        depot_index=0,
        depot_coord=(coords[0, 0], coords[0, 1]),
        coords=coords,
        demands=customer_demands,
        all_demands=all_demands,
        cost_matrix=cost_matrix
    )
