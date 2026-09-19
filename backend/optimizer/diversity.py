"""
Swarm diversity metrics for QPSO.

Computes diversity in the continuous random-key space
to control the contraction-expansion coefficient alpha.

Blueprint reference: §14 Enhancement 2 — Diversity-Adaptive alpha

The diversity metric measures how spread out the particles are.
High diversity = exploring; Low diversity = converging/stuck.
"""

from __future__ import annotations

import numpy as np


def continuous_diversity(population: np.ndarray) -> float:
    """Compute normalized diversity of the random-key population.

    §14: D_key = average distance of particles from the population
    centroid, normalized by the search-space scale.

    For random keys in [0,1]^n, the maximum possible distance from
    centroid is sqrt(n) * 0.5 (when centroid is at 0.5 and particle
    is at a corner).

    Args:
        population: 2D array of shape (N, n_customers) with values in [0,1].

    Returns:
        Normalized diversity in [0, 1].
        0 = all particles identical (collapsed).
        1 = maximum theoretical spread.
    """
    N, n_dim = population.shape
    if N <= 1:
        return 0.0

    centroid = population.mean(axis=0)  # shape: (n_dim,)

    # Distance of each particle from centroid
    distances = np.sqrt(np.sum((population - centroid) ** 2, axis=1))

    # Average distance
    avg_distance = distances.mean()

    # Normalize by maximum possible distance
    # Max distance from centroid [0.5, 0.5, ...] to corner [0, 0, ...]
    # is sqrt(n_dim * 0.25) = 0.5 * sqrt(n_dim)
    max_distance = 0.5 * np.sqrt(n_dim)

    if max_distance > 0:
        normalized = avg_distance / max_distance
    else:
        normalized = 0.0

    return float(np.clip(normalized, 0.0, 1.0))


def per_particle_distance(population: np.ndarray) -> np.ndarray:
    """Compute each particle's distance from the population centroid.

    Used for per-particle adaptive alpha (Upgrade 3).

    Args:
        population: 2D array of shape (N, n_customers).

    Returns:
        1D array of shape (N,) with normalized distances.
    """
    N, n_dim = population.shape
    centroid = population.mean(axis=0)
    distances = np.sqrt(np.sum((population - centroid) ** 2, axis=1))

    max_distance = 0.5 * np.sqrt(n_dim)
    if max_distance > 0:
        normalized = distances / max_distance
    else:
        normalized = np.zeros(N)

    return np.clip(normalized, 0.0, 1.0)


def fitness_rank(fitness_values: np.ndarray) -> np.ndarray:
    """Compute normalized fitness rank for each particle.

    Rank 0.0 = best particle, 1.0 = worst particle.

    Args:
        fitness_values: 1D array of fitness values (lower = better).

    Returns:
        1D array of normalized ranks in [0, 1].
    """
    N = len(fitness_values)
    if N <= 1:
        return np.zeros(N)

    # argsort gives indices that would sort the array
    order = np.argsort(fitness_values)
    ranks = np.empty(N, dtype=np.float64)
    ranks[order] = np.arange(N, dtype=np.float64) / (N - 1)

    return ranks
