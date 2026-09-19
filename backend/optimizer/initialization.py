"""
Chaotic Initialization Module.

Blueprint reference: §13 Enhancement 1 (Logistic-Tent Chaotic Map).

Standard QPSO uses uniform random initialization (U(0,1)).
Chaotic sequences, specifically the Logistic-Tent map, provide better
ergodicity and spatial coverage, preventing early clustering of particles.

Source: 2024, Applied Soft Computing implementations.
"""

import numpy as np


def logistic_tent_map(
    size: tuple[int, ...],
    r: float = 3.99,
    seed: float = 0.4321,
) -> np.ndarray:
    """Generate chaotic numbers using the Logistic-Tent map.

    The Logistic-Tent map combines the Logistic map and the Tent map:
        x_{n+1} = (r * x_n * (1 - x_n) + (4 - r) * x_n / 2) mod 1  (if x_n < 0.5)
        x_{n+1} = (r * x_n * (1 - x_n) + (4 - r) * (1 - x_n) / 2) mod 1 (if x_n >= 0.5)

    Args:
        size: Shape of the output array.
        r: Control parameter (typically near 4.0 for deep chaos).
        seed: Initial value for the chaotic sequence in (0, 1).
            Defaults to 0.4321 for backward compatibility.

    Returns:
        NumPy array of chaotic values in (0, 1).
    """
    n_elements = np.prod(size)
    seq = np.empty(n_elements, dtype=np.float64)

    # Validate and clamp seed away from fixed points (0, 0.25, 0.5, 0.75, 1.0)
    x = float(seed)
    if x <= 0.0 or x >= 1.0 or x == 0.5 or x == 0.25 or x == 0.75:
        x = 0.4321

    # Burn-in phase to eliminate transient effects
    for _ in range(50):
        if x < 0.5:
            x = (r * x * (1.0 - x) + (4.0 - r) * x / 2.0) % 1.0
        else:
            x = (r * x * (1.0 - x) + (4.0 - r) * (1.0 - x) / 2.0) % 1.0

    # Generate sequence
    for i in range(n_elements):
        if x < 0.5:
            x = (r * x * (1.0 - x) + (4.0 - r) * x / 2.0) % 1.0
        else:
            x = (r * x * (1.0 - x) + (4.0 - r) * (1.0 - x) / 2.0) % 1.0
        
        # Guard against collapsing to exactly 0 or 1
        if x <= 0.0 or x >= 1.0:
            x = 0.4321
            
        seq[i] = x

    return seq.reshape(size)


def generate_population(
    n_particles: int,
    n_dimensions: int,
    seed: float = 0.4321,
) -> np.ndarray:
    """Generate an entire population using a single chaotic sequence.

    Args:
        n_particles: Number of particles (population size).
        n_dimensions: Number of dimensions per particle (e.g., customers).
        seed: Initial chaotic seed.

    Returns:
        2D array of shape (n_particles, n_dimensions) with values in (0, 1).
    """
    return logistic_tent_map((n_particles, n_dimensions), seed=seed)
