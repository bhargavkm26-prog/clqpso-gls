import numpy as np
from typing import Any
from backend.optimizer.decoder import random_keys_to_giant_tour
from backend.optimizer.split import split
from backend.optimizer.fitness import FitnessEvaluator

class ClassicalPSO:
    """Standard PSO implementation for CVRP benchmark comparison."""
    
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
        
        self._evaluate()
        
    def _evaluate(self):
        for i in range(self.N):
            giant_tour = random_keys_to_giant_tour(self.population[i])
            sp = split(giant_tour, self.cost_matrix, self.demands, self.vehicle_capacity, 999)
            self.split_results[i] = sp
            fit = self.fitness_evaluator.evaluate(sp)
            
            if fit < self.pbest_fitness[i]:
                self.pbest_fitness[i] = fit
                self.pbest_positions[i] = self.population[i].copy()
                
            if fit < self.gbest_fitness:
                self.gbest_fitness = fit
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
        
    def should_stop(self) -> bool:
        return self.iteration >= self.max_iter
        
    def get_result(self):
        class DummyResult:
            def __init__(self, fitness, routes):
                self.best_fitness = fitness
                self.best_routes = routes
        return DummyResult(self.gbest_fitness, self.gbest_split.routes if self.gbest_split else [])
