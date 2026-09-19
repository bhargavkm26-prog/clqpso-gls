"""
Lévy Flight Stagnation Escape.

Blueprint reference: §16 Enhancement 3 (Lévy Flight Stagnation Escape).

Uses Mantegna's algorithm to generate heavy-tailed step sizes.
When the swarm stagnates, a subset of particles undergo a large "jump"
to explore entirely new regions of the random-key search space.
"""

import math
from typing import Any

import numpy as np


class LevyFlight:
    """Manages Lévy flight jumps for the optimizer."""

    def __init__(self, config: dict[str, Any], seed: int = 42):
        """Initialize Lévy Flight module.

        Args:
            config: Configuration dictionary.
            seed: Random seed.
        """
        levy_config = config.get("levy", {})
        self.beta = levy_config.get("beta", 1.5)
        self.jump_scale = levy_config.get("jump_scale", 0.1)
        self.rng = np.random.RandomState(seed)
        
        # Precompute Mantegna constant
        # sigma_u = { (Gamma(1+beta) * sin(pi*beta/2)) / (Gamma((1+beta)/2) * beta * 2^((beta-1)/2)) }^(1/beta)
        num = math.gamma(1 + self.beta) * math.sin(math.pi * self.beta / 2)
        den = math.gamma((1 + self.beta) / 2) * self.beta * (2 ** ((self.beta - 1) / 2))
        self.sigma_u = (num / den) ** (1 / self.beta)
        self.sigma_v = 1.0

    def generate_steps(self, size: tuple[int, ...]) -> np.ndarray:
        """Generate Lévy steps using Mantegna's algorithm.

        Args:
            size: Shape of the required step array.

        Returns:
            NumPy array of Lévy steps.
        """
        u = self.rng.normal(0, self.sigma_u, size)
        v = self.rng.normal(0, self.sigma_v, size)
        
        # Avoid division by zero
        v = np.where(np.abs(v) < 1e-10, 1e-10, v)
        
        # step = u / |v|^(1/beta)
        step = u / (np.abs(v) ** (1 / self.beta))
        
        return self.jump_scale * step

    def apply_jump(self, population: np.ndarray, num_particles_to_jump: int, fitness: np.ndarray | None = None) -> np.ndarray:
        """Apply Lévy flight to the worst performing particles.

        Args:
            population: The current population array (N, D).
            num_particles_to_jump: How many particles to perturb.
            fitness: Optional fitness array (N,). If provided, selects the 
                     worst `num_particles_to_jump` particles (highest fitness values).
                     If None, assumes the caller has already ordered the population 
                     and perturbs the last N rows for backward compatibility.

        Returns:
            The perturbed population array. Modifies in-place but also returns.
        """
        if num_particles_to_jump <= 0:
            return population
            
        N, D = population.shape
        num_particles_to_jump = min(num_particles_to_jump, N)
        
        if fitness is not None:
            # Sort ascending by fitness, so worst particles (highest fitness) are at the end
            indices = np.argsort(fitness)[-num_particles_to_jump:]
        else:
            # We perturb the last `num_particles_to_jump` particles
            # (Assuming the caller has sorted them by fitness, or just wants a random subset.
            # Typically applied to the worst part of the swarm).
            indices = np.arange(N - num_particles_to_jump, N)
            
        steps = self.generate_steps((num_particles_to_jump, D))
        
        # Apply steps
        population[indices] += steps
        
        # Wrap/Fold back into [0, 1] bounds
        # Using a bounce-back or wrapping mechanism
        population[indices] = np.abs(population[indices]) % 1.0
        
        return population
