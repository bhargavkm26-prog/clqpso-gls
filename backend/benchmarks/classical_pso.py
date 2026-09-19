"""
Classical Particle Swarm Optimization Baseline.

Standard PSO implementation for CVRP benchmark comparison using the same
random-key + Prins Split decoder as CLQPSO-GLS.
"""

import time
import numpy as np
from typing import Any
from backend.optimizer.decoder import random_keys_to_giant_tour
from backend.optimizer.split import split
from backend.optimizer.fitness import FitnessEvaluator
from backend.benchmarks.reproducibility import validate_solution

class ClassicalPSO:
    """Standard PSO implementation for CVRP benchmark comparison."""
    
    def __init__(
        self,
        cost_matrix: np.ndarray,
        demands: np.ndarray,
        vehicle_capacity: float,
        config: dict[str, Any],
        fitness_evaluator: FitnessEvaluator,
        seed: int = 42,
        instance_name: str = "custom"
    ):
        self.cost_matrix = cost_matrix
        self.demands = demands
        self.vehicle_capacity = vehicle_capacity
        self.config = config
        self.fitness_evaluator = fitness_evaluator
        self.seed = seed
        self.instance_name = instance_name
        self.rng = np.random.RandomState(seed)
        
        self.n_customers = len(demands)
        self.N = config.get("population_size", 128)
        self.max_iter = config.get("max_iterations", 200)
        
        # Standard PSO params
        self.w = 0.729
        self.c1 = 1.49445
        self.c2 = 1.49445
        
        self.iteration = 0
        self.gbest_fitness = float('inf')
        self.gbest_position = None
        self.gbest_split = None
        
        self.population = self.rng.uniform(0, 1, (self.N, self.n_customers))
        self.velocities = self.rng.uniform(-0.1, 0.1, (self.N, self.n_customers))
        
        self.pbest_positions = self.population.copy()
        self.pbest_fitness = np.full(self.N, float('inf'))
        self.split_results = [None] * self.N
        
        self.convergence_history: list[dict[str, Any]] = []
        self.start_time = time.perf_counter()
        
        self._evaluate()
        self.convergence_history.append({"iteration": 0, "best_fitness": float(self.gbest_fitness)})

    def _evaluate(self):
        for i in range(self.N):
            giant_tour = random_keys_to_giant_tour(self.population[i])
            sp = split(giant_tour, self.cost_matrix, self.demands, self.vehicle_capacity, 999)
            self.split_results[i] = sp
            cost = float(sp.total_cost)
            
            if cost < self.pbest_fitness[i]:
                self.pbest_fitness[i] = cost
                self.pbest_positions[i] = self.population[i].copy()
                
            if cost < self.gbest_fitness:
                self.gbest_fitness = cost
                self.gbest_position = self.population[i].copy()
                self.gbest_split = sp

    def step(self):
        r1 = self.rng.uniform(0, 1, (self.N, self.n_customers))
        r2 = self.rng.uniform(0, 1, (self.N, self.n_customers))
        
        cognitive = self.c1 * r1 * (self.pbest_positions - self.population)
        social = self.c2 * r2 * (self.gbest_position - self.population)
        
        self.velocities = self.w * self.velocities + cognitive + social
        self.population = self.population + self.velocities
        
        # Keep bounds [0, 1]
        self.population = np.clip(self.population, 0, 1)
        
        self._evaluate()
        self.iteration += 1
        self.convergence_history.append({"iteration": self.iteration, "best_fitness": float(self.gbest_fitness)})

    def should_stop(self) -> bool:
        return self.iteration >= self.max_iter

    def solve(self) -> dict[str, Any]:
        """Run algorithm to completion and return result dictionary."""
        while not self.should_stop():
            self.step()
        return self.get_result()

    def get_result(self) -> dict[str, Any]:
        elapsed = time.perf_counter() - self.start_time
        routes = self.gbest_split.routes if self.gbest_split else []
        
        val = validate_solution(
            routes=routes,
            demands=self.demands,
            vehicle_capacity=self.vehicle_capacity,
            num_customers=self.n_customers,
            cost_matrix=self.cost_matrix,
            reported_fitness=self.gbest_fitness
        )

        return {
            "algorithm": "Classical PSO",
            "instance": self.instance_name,
            "seed": self.seed,
            "best_fitness": float(self.gbest_fitness),
            "distance": float(self.gbest_fitness),
            "travel_time": float(self.gbest_fitness),
            "congestion_cost": 0.0,
            "vehicle_count": len(routes),
            "runtime_seconds": float(elapsed),
            "iterations": self.iteration,
            "convergence": self.convergence_history,
            "routes": routes,
            "parameters": {
                "w": self.w, "c1": self.c1, "c2": self.c2,
                "population_size": self.N, "max_iterations": self.max_iter
            },
            "status": "COMPLETED",
            "valid": val["valid"],
            "errors": val["errors"]
        }
