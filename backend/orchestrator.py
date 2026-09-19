"""
CLQPSO-GLS Orchestrator.

Ties together all algorithm components:
- Graph & Traffic management
- Chaotic Initialization
- QPSO Core Engine
- Guided Local Search (GLS)
- Local Search Operators (2-opt, Or-opt, SWAP*)
- Lévy Flight Stagnation Escape

Supports dynamic traffic updates mid-optimization.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np

from backend.graph.network import build_graph, place_customers_and_depot
from backend.graph.traffic import TrafficManager
from backend.graph.cost_matrix import CostMatrix
from backend.optimizer.fitness import FitnessEvaluator
from backend.optimizer.qpso import QPSOEngine, QPSOResult
from backend.optimizer.initialization import logistic_tent_map
from backend.optimizer.levy import LevyFlight
from backend.optimizer.gls import GuidedLocalSearch
from backend.optimizer.local_search import (
    two_opt_giant_tour,
    or_opt_giant_tour,
    swap_star
)
from backend.optimizer.decoder import giant_tour_to_random_keys

logger = logging.getLogger(__name__)


class OptimizerOrchestrator:
    """Main execution orchestrator for CLQPSO-GLS."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the orchestrator with full config."""
        self.config = config
        self.rng = np.random.RandomState(config.get("optimizer", {}).get("seed", 42))

        # Core state
        self.graph = None
        self.traffic_manager = None
        self.cost_matrix_manager = None
        self.depot = None
        self.customers = []
        self.demands = np.array([])
        self.vehicle_capacity = 0.0

        # Optimizer components
        self.qpso = None
        self.gls = None
        self.levy = None
        self.fitness_evaluator = None

        # Configuration variables
        opt_config = self.config.get("optimizer", {})
        self.use_chaotic_init = opt_config.get("use_chaotic_init", True)
        self.local_search_frequency = opt_config.get("local_search_frequency", 10)
        self.levy_patience = opt_config.get("levy", {}).get("patience", 15)
        self.levy_jump_fraction = opt_config.get("levy", {}).get("jump_fraction", 0.3)

    def setup_problem(
        self,
        num_customers: int | None = None,
        scenario_file: str | None = None,
        depot_coords: tuple[float, float] | None = None,
        customer_coords: list[tuple[float, float]] | None = None,
        vehicle_capacity: float | None = None,
        max_vehicles: int | None = None
    ) -> None:
        """Initialize the graph, traffic, and cost matrix."""
        logger.info("Setting up problem instance...")
        
        # 1. Build Graph
        if self.graph is None:
            graph_config = self.config.get("graph", {})
            self.graph = build_graph(graph_config)
        
        # 2. Place Customers
        vrp_config = self.config.get("vrp", {})
        
        if depot_coords and customer_coords:
            # Snap coordinates to nearest graph nodes
            # coords are (lat, lng). Graph nodes have 'x' (lng) and 'y' (lat).
            def find_nearest_node(lat, lng):
                best_node = None
                best_dist = float('inf')
                for n, data in self.graph.nodes(data=True):
                    # use simple euclidean for snapping on synthetic, or approximate for lat/lng
                    dy = data.get('y', 0) - lat
                    dx = data.get('x', 0) - lng
                    dist = dx*dx + dy*dy
                    if dist < best_dist:
                        best_dist = dist
                        best_node = n
                return best_node

            self.depot = find_nearest_node(depot_coords[0], depot_coords[1])
            self.customers = []
            for lat, lng in customer_coords:
                node = find_nearest_node(lat, lng)
                if node is not None and node not in self.customers and node != self.depot:
                    self.customers.append(node)
                    
            # Generate random demands 1-30 for each selected customer
            demand_dict = {c: self.rng.randint(1, 30) for c in self.customers}
            self.demands = np.array([demand_dict[c] for c in self.customers], dtype=np.float64)
            num_customers = len(self.customers)
        else:
            if num_customers is None:
                num_customers = vrp_config.get("num_customers", 50)
                
            num_customers = min(num_customers, self.graph.number_of_nodes() - 1)
            self.depot, self.customers, demand_dict = place_customers_and_depot(
                self.graph, num_customers=num_customers, seed=self.rng.randint(0, 10000)
            )
            self.demands = np.array([demand_dict[c] for c in self.customers], dtype=np.float64)
            
        self.vehicle_capacity = vehicle_capacity if vehicle_capacity is not None else vrp_config.get("vehicle_capacity", 100.0)
        
        if max_vehicles is not None:
            if "vrp" not in self.config:
                self.config["vrp"] = {}
            self.config["vrp"]["max_vehicles"] = max_vehicles

        # 3. Traffic Manager
        if scenario_file is None:
            scenario_file = "baseline.json"
            
        self.traffic_manager = TrafficManager(self.graph)
        scenario = self.traffic_manager.load_scenario(scenario_file)
        self.traffic_manager.apply_scenario(scenario)

        # 4. Cost Matrix
        self.cost_matrix_manager = CostMatrix(self.graph, self.depot, self.customers)
        logger.info(f"Problem setup complete: {num_customers} customers.")

    def _init_optimizer_components(self) -> None:
        """Initialize QPSO, GLS, and Levy flight components."""
        opt_config = self.config.get("optimizer", {})
        
        # Fitness Evaluator
        self.fitness_evaluator = FitnessEvaluator(
            cost_matrix=self.cost_matrix_manager.matrix,
            demands=self.demands,
            vehicle_capacity=self.vehicle_capacity,
            normalization_stats={
                "min_cost": self.cost_matrix_manager.min_cost,
                "max_cost": self.cost_matrix_manager.max_cost
            }
        )

        # GLS
        self.gls = GuidedLocalSearch(
            n_stops=len(self.customers) + 1,
            config=opt_config
        )

        # Lévy Flight
        self.levy = LevyFlight(config=opt_config, seed=self.rng.randint(0, 10000))

        # QPSO Engine
        self.qpso = QPSOEngine(
            cost_matrix=self.cost_matrix_manager.matrix,
            demands=self.demands,
            vehicle_capacity=self.vehicle_capacity,
            config=opt_config,
            fitness_evaluator=self.fitness_evaluator,
            seed=self.rng.randint(0, 10000)
        )

        # Chaotic Init
        initial_pop = None
        if self.use_chaotic_init:
            initial_pop = logistic_tent_map(
                size=(self.qpso.N, self.qpso.n_customers)
            )

        self.qpso.initialize(initial_population=initial_pop)
        logger.info("Optimizer components initialized.")

    def step(self) -> QPSOState:
        """Perform one complete orchestrated iteration.
        
        Includes the core QPSO step, stagnation checks, GLS penalties,
        Lévy flight recovery, and periodic local search.
        """
        if self.qpso is None:
            self._init_optimizer_components()
            
        # 1. Standard QPSO step
        state = self.qpso.step()
        levy_triggered = False

        # 2. Check for Stagnation
        if self.qpso.stagnation_counter >= self.levy_patience:
            # 3a. Update GLS penalties on the stagnated solution
            if self.gls.enabled:
                self.gls.update_penalties(
                    self.qpso.gbest_split.routes,
                    self.cost_matrix_manager.matrix
                )
            
            # 3b. Apply Lévy Flight to worst particles
            num_jump = int(self.qpso.N * self.levy_jump_fraction)
            self.qpso.population = self.levy.apply_jump(
                self.qpso.population,
                num_particles_to_jump=num_jump,
                fitness=self.qpso.fitness
            )
            
            # Re-evaluate population after jump
            self.qpso._evaluate_population()
            self.qpso._update_bests()
            
            # Reset stagnation counter
            self.qpso.stagnation_counter = 0
            levy_triggered = True
            
            # Update history state flag
            self.qpso.convergence_history[-1].levy_triggered = True

        # 4. Periodic Local Search on the Global Best
        if state.iteration % self.local_search_frequency == 0:
            self._apply_local_search_to_gbest()

        # Logging
        if state.iteration % 20 == 0:
            logger.info(
                f"Iter {state.iteration:>4} | "
                f"Cost: {self.qpso.gbest_split.total_cost:.1f} | "
                f"Vehicles: {self.qpso.gbest_split.num_vehicles} | "
                f"Div: {state.diversity:.3f} | "
                f"Lévy: {levy_triggered}"
            )
            
        return state

    def run(self) -> QPSOResult:
        """Run the full CLQPSO-GLS optimization loop."""
        if self.qpso is None:
            self._init_optimizer_components()

        logger.info("Starting optimization loop...")
        
        while not self.qpso.should_stop():
            self.step()

        logger.info("Optimization complete.")
        return self.qpso.get_result()

    def update_traffic_scenario(self, scenario_file: str) -> None:
        """Apply a dynamic traffic update and re-evaluate the swarm.
        
        This handles the SIH requirement for dynamic scenario shifts.
        """
        logger.info(f"Traffic update received: {scenario_file}")
        
        # Update graph edge weights
        scenario = self.traffic_manager.load_scenario(scenario_file)
        self.traffic_manager.apply_scenario(scenario)
        
        # Recompute cost matrix
        self.cost_matrix_manager.update(self.graph, self.traffic_manager.affected_edges)
        
        if self.qpso is not None:
            logger.info("Re-evaluating swarm with new cost matrix...")
            
            # Update evaluator and QPSO references
            self.fitness_evaluator.cost_matrix = self.cost_matrix_manager.matrix
            self.fitness_evaluator.min_cost = self.cost_matrix_manager.min_cost
            self.fitness_evaluator.max_cost = self.cost_matrix_manager.max_cost
            
            self.qpso.cost_matrix = self.cost_matrix_manager.matrix
            
            # Re-evaluate all particles
            self.qpso._evaluate_population()
            
            # Reset bests to reflect new realities (what was good might be bad now)
            self.qpso.pbest_positions = self.qpso.population.copy()
            self.qpso.pbest_fitness = self.qpso.fitness.copy()
            
            best_idx = np.argmin(self.qpso.fitness)
            self.qpso.gbest_position = self.qpso.population[best_idx].copy()
            self.qpso.gbest_fitness = float(self.qpso.fitness[best_idx])
            self.qpso.gbest_split = self.qpso.split_results[best_idx]
            
            self.qpso.stagnation_counter = 0

    def _apply_local_search_to_gbest(self) -> None:
        """Apply 2-opt, Or-opt, and SWAP* to the global best solution."""
        if not self.qpso.gbest_split:
            return

        # We use the augmented cost matrix if GLS is enabled
        cost_mat = self.gls.get_augmented_cost_matrix(self.cost_matrix_manager.matrix)

        improved_overall = False
        current_split = self.qpso.gbest_split
        
        # Convert routes back to giant tour for intra-route operators
        giant_tour = np.concatenate(current_split.routes).astype(int)

        # 1. 2-opt
        tour, imp_2opt = two_opt_giant_tour(giant_tour, cost_mat, max_iterations=5)
        
        # 2. Or-opt
        tour, imp_oropt = or_opt_giant_tour(tour, cost_mat, max_segment_length=3, max_iterations=5)

        if imp_2opt or imp_oropt:
            improved_overall = True
            # Re-split to evaluate exact fitness impact
            from backend.optimizer.split import split
            current_split = split(
                tour,
                self.cost_matrix_manager.matrix,  # Always use true cost for actual fitness/split
                self.demands,
                self.vehicle_capacity,
                self.qpso.max_vehicles
            )

        # 3. SWAP* (Inter-route)
        new_split, imp_swap = swap_star(
            current_split,
            cost_mat,
            self.demands,
            self.vehicle_capacity
        )
        
        if imp_swap:
            improved_overall = True
            current_split = new_split
            tour = np.concatenate(current_split.routes).astype(int)

        if improved_overall:
            # Re-evaluate fitness using the un-augmented matrix for true fitness
            new_fitness = self.fitness_evaluator.evaluate(current_split)
            
            # If the true fitness improved, inject it back into the swarm
            # We inject it over the worst particle to maintain global best
            if new_fitness < self.qpso.gbest_fitness:
                worst_idx = np.argmax(self.qpso.fitness)
                
                # Inject (handles random key re-encoding)
                self.qpso.inject_improved_solution(
                    particle_idx=worst_idx,
                    improved_tour=tour,
                    improved_split=current_split,
                    improved_fitness=new_fitness
                )
                logger.debug(f"Local Search improved gbest fitness to {new_fitness:.4f}")
