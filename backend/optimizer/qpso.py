"""
Core Quantum Particle Swarm Optimization (QPSO) Engine.

Blueprint reference: §9 Core QPSO, §14 Enhancement 2 (Adaptive alpha),
    §10 Random-Key + Split, Upgrade 3 (Per-Particle Adaptive alpha)

Source: Sun, Feng & Xu (2004) — "Particle Swarm Optimization with
    Particles Having Quantum Behavior", IEEE CEC.

QPSO position update (per particle per dimension):
    1. Local attractor:  p_ij = phi * P_ij + (1-phi) * G_j
    2. Mean best:        M_j  = (1/N) sum(P_ij)
    3. Position update:  X_ij = p_ij +/- alpha * |M_j - X_ij| * ln(1/u)

Where:
    P_i  = personal best position of particle i
    G    = global best position
    phi  = random in [0, 1]
    u    = random in [0, 1]
    alpha= contraction-expansion coefficient (adaptive)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from backend.optimizer.decoder import random_keys_to_giant_tour, giant_tour_to_random_keys
from backend.optimizer.split import split, SplitResult
from backend.optimizer.fitness import FitnessEvaluator
from backend.optimizer.diversity import continuous_diversity, per_particle_distance, fitness_rank


@dataclass
class QPSOState:
    """Complete state of the QPSO optimizer at a given iteration.

    Stored for each iteration to enable convergence analysis,
    algorithm race visualization, and WebSocket streaming.
    """
    iteration: int
    best_fitness: float
    mean_fitness: float
    worst_fitness: float
    diversity: float
    alpha_mean: float
    gbest_routes: list[list[int]]
    gbest_cost: float
    gbest_vehicles: int
    stagnation_counter: int
    elapsed_ms: float
    levy_triggered: bool = False


@dataclass
class QPSOResult:
    """Final result of a QPSO optimization run.

    Contains the best solution found, convergence history,
    and run statistics.
    """
    best_fitness: float
    best_routes: list[list[int]]
    best_route_costs: list[float]
    best_total_cost: float
    best_num_vehicles: int
    convergence_history: list[QPSOState]
    total_iterations: int
    elapsed_ms: float
    seed: int


class QPSOEngine:
    """Core QPSO optimization engine.

    Implements the complete QPSO pipeline:
        1. Initialize population (chaotic or random)
        2. Decode: random keys -> giant tour -> Split -> routes
        3. Evaluate fitness
        4. Update personal bests, global best
        5. Compute mean best
        6. Update positions using quantum mechanics
        7. Apply adaptive alpha
        8. Check stagnation (Levy flight applied externally)
        9. Repeat until convergence or budget exhausted

    The engine is designed to be composable:
        - Local search (GLS + 2-opt/Or-opt/SWAP*) is applied externally
        - Levy flight is triggered by the orchestrator
        - Chaotic initialization is a separate module
    """

    def __init__(
        self,
        cost_matrix: np.ndarray,
        demands: np.ndarray,
        vehicle_capacity: float,
        config: dict[str, Any],
        fitness_evaluator: FitnessEvaluator,
        seed: int = 42,
    ):
        """Initialize the QPSO engine.

        Args:
            cost_matrix: Stop-to-stop cost matrix (index 0 = depot).
            demands: Customer demands array.
            vehicle_capacity: Vehicle capacity.
            config: Optimizer configuration from default.yaml.
            fitness_evaluator: Fitness evaluator instance.
            seed: Random seed for reproducibility.
        """
        self.cost_matrix = cost_matrix
        self.demands = demands
        self.vehicle_capacity = vehicle_capacity
        self.config = config
        self.fitness_evaluator = fitness_evaluator
        self.seed = seed
        self.rng = np.random.RandomState(seed)

        # Problem dimensions
        self.n_customers = len(demands)
        self.N = config.get("population_size", 128)
        self.max_iter = config.get("max_iterations", 200)

        # Alpha configuration
        alpha_config = config.get("alpha", {})
        self.alpha_mode = alpha_config.get("mode", "per_particle")
        self.alpha_min = alpha_config.get("min", 0.5)
        self.alpha_max = alpha_config.get("max", 1.2)
        self.alpha_initial = alpha_config.get("initial", 1.0)

        # Diversity thresholds
        div_config = config.get("diversity", {})
        self.d_low = div_config.get("d_low", 0.1)
        self.d_high = div_config.get("d_high", 0.4)

        # Stopping criteria
        stop_config = config.get("stopping", {})
        self.convergence_patience = stop_config.get("convergence_patience", 50)
        self.time_budget_ms = stop_config.get("time_budget_ms", 30000)

        # Max vehicles
        self.max_vehicles = config.get("max_vehicles", None)

        # State arrays (initialized in initialize())
        self.population: np.ndarray | None = None  # (N, n_customers) random keys
        self.fitness: np.ndarray | None = None  # (N,) fitness values
        self.split_results: list[SplitResult] | None = None
        self.pbest_positions: np.ndarray | None = None  # (N, n_customers)
        self.pbest_fitness: np.ndarray | None = None  # (N,)
        self.gbest_position: np.ndarray | None = None  # (n_customers,)
        self.gbest_fitness: float = float("inf")
        self.gbest_split: SplitResult | None = None
        self.alpha: np.ndarray | None = None  # (N,) per-particle alpha

        # Tracking
        self.iteration: int = 0
        self.stagnation_counter: int = 0
        self.convergence_history: list[QPSOState] = []
        self._start_time: float = 0.0

    def initialize(
        self,
        initial_population: np.ndarray | None = None,
    ) -> None:
        """Initialize the population and evaluate.

        Args:
            initial_population: Optional pre-generated population
                (e.g., from chaotic initialization). Shape: (N, n_customers).
                If None, uses uniform random initialization.
        """
        self._start_time = time.time()

        # Initialize population
        if initial_population is not None:
            assert initial_population.shape == (self.N, self.n_customers), \
                f"Expected shape ({self.N}, {self.n_customers}), got {initial_population.shape}"
            self.population = initial_population.copy()
        else:
            self.population = self.rng.random((self.N, self.n_customers))

        # Clamp to [0, 1]
        self.population = np.clip(self.population, 0.0, 1.0)

        # Initialize alpha
        self.alpha = np.full(self.N, self.alpha_initial, dtype=np.float64)

        # Evaluate all particles
        self._evaluate_population()

        # Initialize personal bests
        self.pbest_positions = self.population.copy()
        self.pbest_fitness = self.fitness.copy()

        # Initialize global best
        best_idx = np.argmin(self.fitness)
        self.gbest_position = self.population[best_idx].copy()
        self.gbest_fitness = float(self.fitness[best_idx])
        self.gbest_split = self.split_results[best_idx]

        self.iteration = 0
        self.stagnation_counter = 0

        # Record initial state
        self._record_state(levy_triggered=False)

    def step(self) -> QPSOState:
        """Execute one QPSO iteration.

        Returns:
            QPSOState snapshot of this iteration.
        """
        self.iteration += 1
        old_gbest = self.gbest_fitness

        # Step 1: Compute Mean Best (M_best)
        mbest = self.pbest_positions.mean(axis=0)  # shape: (n_customers,)

        # Step 2: Update alpha adaptively
        self._update_alpha()

        # Step 3: QPSO position update for all particles
        self._qpso_update(mbest)

        # Step 4: Evaluate updated population
        self._evaluate_population()

        # Step 5: Update personal and global bests
        self._update_bests()

        # Step 6: Track stagnation
        if self.gbest_fitness < old_gbest - 1e-10:
            self.stagnation_counter = 0
        else:
            self.stagnation_counter += 1

        # Record state
        state = self._record_state(levy_triggered=False)
        return state

    def _qpso_update(self, mbest: np.ndarray) -> None:
        """Perform the core QPSO position update.

        §9: For each particle i, each dimension j:
            phi_ij  = U(0, 1)
            p_ij    = phi_ij * P_ij + (1 - phi_ij) * G_j
            u_ij    = U(0, 1)
            X_ij    = p_ij +/- alpha_i * |M_j - X_ij| * ln(1 / u_ij)
        """
        N, D = self.population.shape

        # Random matrices
        phi = self.rng.random((N, D))
        u = self.rng.random((N, D))
        sign = np.where(self.rng.random((N, D)) < 0.5, 1.0, -1.0)

        # Local attractor: p = phi * P_best + (1-phi) * G_best
        local_attractor = phi * self.pbest_positions + (1.0 - phi) * self.gbest_position

        # Quantum update: X = p +/- alpha * |M - X| * ln(1/u)
        # Avoid log(0) by clamping u
        u = np.clip(u, 1e-10, 1.0)
        ln_term = np.log(1.0 / u)

        # Per-particle alpha: broadcast (N,) to (N, D)
        alpha_expanded = self.alpha[:, np.newaxis]

        # Distance from mean best
        delta = np.abs(mbest - self.population)

        # New positions
        self.population = local_attractor + sign * alpha_expanded * delta * ln_term

        # Clamp to [0, 1] (bound enforcement for random keys)
        self.population = np.clip(self.population, 0.0, 1.0)

    def _update_alpha(self) -> None:
        """Update the contraction-expansion coefficient.

        §14: Diversity-adaptive alpha:
            If diversity < d_low:  increase alpha → more exploration
            If diversity > d_high: decrease alpha → more exploitation
            Otherwise:             linear interpolation

        Upgrade 3 (Per-Particle): Additionally adjust based on
            each particle's fitness rank:
            - Good particles get smaller alpha (exploit their region)
            - Poor particles get larger alpha (explore more)
            
        Note: The adjustment constants (0.3 and 0.15) are engineering choices 
        specific to this implementation. They do not originate from the original 
        QPSO paper.
        """
        diversity = continuous_diversity(self.population)

        if self.alpha_mode == "per_particle":
            # Base alpha from diversity (same for all)
            if diversity < self.d_low:
                base_alpha = self.alpha_max
            elif diversity > self.d_high:
                base_alpha = self.alpha_min
            else:
                # Linear interpolation
                t = (diversity - self.d_low) / (self.d_high - self.d_low)
                base_alpha = self.alpha_max - t * (self.alpha_max - self.alpha_min)

            # Per-particle adjustment based on fitness rank
            ranks = fitness_rank(self.fitness)  # 0=best, 1=worst
            # Good particles (rank~0) → alpha closer to alpha_min
            # Poor particles (rank~1) → alpha closer to alpha_max
            adjustment = ranks * (self.alpha_max - self.alpha_min) * 0.3

            self.alpha = np.clip(
                base_alpha + adjustment - (self.alpha_max - self.alpha_min) * 0.15,
                self.alpha_min,
                self.alpha_max,
            )
        else:
            # Global adaptive alpha
            if diversity < self.d_low:
                alpha = self.alpha_max
            elif diversity > self.d_high:
                alpha = self.alpha_min
            else:
                t = (diversity - self.d_low) / (self.d_high - self.d_low)
                alpha = self.alpha_max - t * (self.alpha_max - self.alpha_min)

            self.alpha[:] = alpha

    def _evaluate_population(self) -> None:
        """Decode and evaluate all particles."""
        self.fitness = np.empty(self.N, dtype=np.float64)
        self.split_results = []

        for i in range(self.N):
            # Decode: random keys → giant tour → Split → routes
            giant_tour = random_keys_to_giant_tour(self.population[i])
            result = split(
                giant_tour=giant_tour,
                cost_matrix=self.cost_matrix,
                demands=self.demands,
                vehicle_capacity=self.vehicle_capacity,
                max_vehicles=self.max_vehicles,
            )
            self.split_results.append(result)
            self.fitness[i] = self.fitness_evaluator.evaluate(result)

    def _update_bests(self) -> None:
        """Update personal and global best positions."""
        # Personal bests
        improved = self.fitness < self.pbest_fitness
        self.pbest_positions[improved] = self.population[improved].copy()
        self.pbest_fitness[improved] = self.fitness[improved]

        # Global best: update if any of the CURRENT evaluated particles beat gbest.
        # This ensures gbest_position, gbest_fitness, and gbest_split correspond
        # exactly to the same solution.
        best_idx = np.argmin(self.fitness)
        if self.fitness[best_idx] < self.gbest_fitness:
            self.gbest_fitness = float(self.fitness[best_idx])
            self.gbest_position = self.population[best_idx].copy()
            self.gbest_split = self.split_results[best_idx]

    def _record_state(self, levy_triggered: bool = False) -> QPSOState:
        """Record current optimizer state for history/streaming."""
        diversity = continuous_diversity(self.population)
        elapsed = (time.time() - self._start_time) * 1000.0

        state = QPSOState(
            iteration=self.iteration,
            best_fitness=self.gbest_fitness,
            mean_fitness=float(self.fitness.mean()),
            worst_fitness=float(self.fitness.max()),
            diversity=diversity,
            alpha_mean=float(self.alpha.mean()),
            gbest_routes=[list(r) for r in self.gbest_split.routes] if self.gbest_split else [],
            gbest_cost=self.gbest_split.total_cost if self.gbest_split else float("inf"),
            gbest_vehicles=self.gbest_split.num_vehicles if self.gbest_split else 0,
            stagnation_counter=self.stagnation_counter,
            elapsed_ms=elapsed,
            levy_triggered=levy_triggered,
        )
        self.convergence_history.append(state)
        return state

    def is_stagnated(self, patience: int | None = None) -> bool:
        """Check if the optimizer has stagnated.

        Args:
            patience: Override stagnation patience. Defaults to config value.

        Returns:
            True if stagnation counter exceeds patience.
        """
        if patience is None:
            patience = self.convergence_patience
        return self.stagnation_counter >= patience

    def should_stop(self) -> bool:
        """Check if optimization should terminate.

        Returns True if:
            - Max iterations reached
            - Time budget exceeded
            - Convergence patience exceeded
        """
        if self.iteration >= self.max_iter:
            return True

        elapsed = (time.time() - self._start_time) * 1000.0
        if elapsed >= self.time_budget_ms:
            return True

        if self.stagnation_counter >= self.convergence_patience:
            return True

        return False

    def get_result(self) -> QPSOResult:
        """Package the final result."""
        elapsed = (time.time() - self._start_time) * 1000.0

        return QPSOResult(
            best_fitness=self.gbest_fitness,
            best_routes=[list(r) for r in self.gbest_split.routes] if self.gbest_split else [],
            best_route_costs=list(self.gbest_split.route_costs) if self.gbest_split else [],
            best_total_cost=self.gbest_split.total_cost if self.gbest_split else float("inf"),
            best_num_vehicles=self.gbest_split.num_vehicles if self.gbest_split else 0,
            convergence_history=self.convergence_history,
            total_iterations=self.iteration,
            elapsed_ms=elapsed,
            seed=self.seed,
        )

    def inject_improved_solution(
        self,
        particle_idx: int,
        improved_tour: np.ndarray,
        improved_split: SplitResult,
        improved_fitness: float,
    ) -> None:
        """Inject an improved solution back into the population.

        §18: After GLS improves a tour, re-encode to random keys
        and update the particle + personal best.

        Args:
            particle_idx: Which particle to update.
            improved_tour: Improved giant tour (customer indices).
            improved_split: Split result for the improved tour.
            improved_fitness: Fitness of the improved solution.
        """
        # Re-encode tour to random keys
        improved_keys = giant_tour_to_random_keys(improved_tour, self.n_customers)

        # Update population
        self.population[particle_idx] = improved_keys

        # Update this particle's cached state
        self.fitness[particle_idx] = improved_fitness
        self.split_results[particle_idx] = improved_split

        # Update personal best if improved
        if improved_fitness < self.pbest_fitness[particle_idx]:
            self.pbest_positions[particle_idx] = improved_keys.copy()
            self.pbest_fitness[particle_idx] = improved_fitness

        # Update global best if improved
        if improved_fitness < self.gbest_fitness:
            self.gbest_fitness = improved_fitness
            self.gbest_position = improved_keys.copy()
            self.gbest_split = improved_split
