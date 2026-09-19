import numpy as np
from typing import Any
from backend.optimizer.decoder import random_keys_to_giant_tour
from backend.optimizer.split import split
from backend.optimizer.fitness import FitnessEvaluator

class GeneticAlgorithm:
    """Standard GA implementation for CVRP benchmark comparison."""
    
    def __init__(
        self,
        cost_matrix: np.ndarray,
        demands: np.ndarray,
        vehicle_capacity: float,
        config: dict[str, Any],
        fitness_evaluator: FitnessEvaluator,
        seed: int = 42
    ):
        self.cost_matrix = cost_matrix
        self.demands = demands
        self.vehicle_capacity = vehicle_capacity
        self.config = config
        self.fitness_evaluator = fitness_evaluator
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
        
        self._evaluate()
        
    def _evaluate(self):
        for i in range(self.N):
            giant_tour = random_keys_to_giant_tour(self.population[i])
            sp = split(giant_tour, self.cost_matrix, self.demands, self.vehicle_capacity, 999)
            self.split_results[i] = sp
            self.fitness[i] = self.fitness_evaluator.evaluate(sp)
            
            if self.fitness[i] < self.gbest_fitness:
                self.gbest_fitness = self.fitness[i]
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
                # Simulated Binary Crossover (SBX) style simple average or uniform crossover
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
        
    def should_stop(self) -> bool:
        return self.iteration >= self.max_iter
        
    def get_result(self):
        class DummyResult:
            def __init__(self, fitness, routes):
                self.best_fitness = fitness
                self.best_routes = routes
        return DummyResult(self.gbest_fitness, self.gbest_split.routes if self.gbest_split else [])
