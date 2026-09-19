"""
Genetic Algorithm Baseline for CVRP.

Standard GA implementation for CVRP benchmark comparison using the same
random-key + Prins Split decoder as CLQPSO-GLS.
"""

import time
import numpy as np
from typing import Any
from backend.optimizer.decoder import random_keys_to_giant_tour
from backend.optimizer.split import split
from backend.optimizer.fitness import FitnessEvaluator
from backend.benchmarks.reproducibility import validate_solution

class GeneticAlgorithm:
    """Standard GA implementation for CVRP benchmark comparison."""
    
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
        
        self.crossover_rate = 0.8
        self.mutation_rate = 0.1
        
        self.iteration = 0
        self.gbest_fitness = float('inf')
        self.gbest_position = None
        self.gbest_split = None
        
        self.population = self.rng.uniform(0, 1, (self.N, self.n_customers))
        self.fitness = np.full(self.N, float('inf'))
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
            self.fitness[i] = cost
            
            if cost < self.gbest_fitness:
                self.gbest_fitness = cost
                self.gbest_position = self.population[i].copy()
                self.gbest_split = sp

    def _tournament_selection(self, k=3):
        indices = self.rng.choice(self.N, k, replace=False)
        best_idx = indices[np.argmin(self.fitness[indices])]
        return self.population[best_idx].copy()

    def step(self):
        new_population = np.zeros_like(self.population)
        
        # Elitism
        new_population[0] = self.gbest_position.copy()
        
        for i in range(1, self.N, 2):
            p1 = self._tournament_selection()
            p2 = self._tournament_selection()
            
            if self.rng.rand() < self.crossover_rate:
                mask = self.rng.rand(self.n_customers) < 0.5
                c1 = np.where(mask, p1, p2)
                c2 = np.where(mask, p2, p1)
            else:
                c1, c2 = p1, p2
                
            if self.rng.rand() < self.mutation_rate:
                c1 += self.rng.normal(0, 0.1, self.n_customers)
            if self.rng.rand() < self.mutation_rate:
                c2 += self.rng.normal(0, 0.1, self.n_customers)
                
            new_population[i] = c1
            if i + 1 < self.N:
                new_population[i+1] = c2
                
        self.population = np.clip(new_population, 0, 1)
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
            "algorithm": "Genetic Algorithm",
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
                "crossover_rate": self.crossover_rate, "mutation_rate": self.mutation_rate,
                "population_size": self.N, "max_iterations": self.max_iter
            },
            "status": "COMPLETED",
            "valid": val["valid"],
            "errors": val["errors"]
        }
