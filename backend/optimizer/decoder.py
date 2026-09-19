"""
SPV Random-Key Decoder.

Converts continuous random-key particles [0,1]^n to discrete
giant customer tours via Smallest Position Value (SPV) sorting.

Blueprint reference: §10 Random-Key → Route Decoder

The decoder is the bridge between the continuous QPSO search space
and the discrete combinatorial VRP solution space.

Example:
    X_i = [0.72, 0.11, 0.54, 0.31]
    SPV sort → customer order: [2, 4, 3, 1] (giant tour)
"""

from __future__ import annotations

import numpy as np


def random_keys_to_giant_tour(keys: np.ndarray) -> np.ndarray:
    """Convert a random-key vector to a giant customer tour via SPV.

    The Smallest Position Value (SPV) rule sorts customers by their
    corresponding random-key values in ascending order.

    Args:
        keys: 1D array of shape (n_customers,) with values in [0, 1].

    Returns:
        1D array of customer indices (0-based) in giant tour order.
        Customer indices are 0..n_customers-1 (NOT stop indices).

    Example:
        keys = [0.72, 0.11, 0.54, 0.31]
        result = [1, 3, 2, 0]  → customer 1 first, then 3, 2, 0
    """
    return np.argsort(keys, kind="stable")


def giant_tour_to_random_keys(tour: np.ndarray, n_customers: int) -> np.ndarray:
    """Re-encode a giant tour back to random keys (rank encoding).

    §18: When GLS improves a giant tour, re-encode its ordering
    into random keys so QPSO can inherit the improvement.

    Assigns monotonically increasing keys according to rank:
        rank 1 → (1 - 0.5) / n
        rank 2 → (2 - 0.5) / n
        ...
        rank n → (n - 0.5) / n

    Args:
        tour: 1D array of customer indices in giant tour order.
        n_customers: Total number of customers.

    Returns:
        1D array of random keys with shape (n_customers,).
    """
    keys = np.zeros(n_customers, dtype=np.float64)
    for rank, customer_idx in enumerate(tour):
        keys[customer_idx] = (rank + 0.5) / n_customers
    return keys


def batch_decode(population_keys: np.ndarray) -> np.ndarray:
    """Decode an entire population of random-key particles to giant tours.

    Args:
        population_keys: 2D array of shape (N, n_customers).

    Returns:
        2D array of shape (N, n_customers) with customer orderings.
    """
    return np.argsort(population_keys, axis=1, kind="stable")


def batch_encode(tours: np.ndarray, n_customers: int) -> np.ndarray:
    """Re-encode multiple giant tours back to random keys.

    Args:
        tours: 2D array of shape (N, n_customers) with customer orderings.
        n_customers: Total number of customers.

    Returns:
        2D array of shape (N, n_customers) with random keys.
    """
    N = tours.shape[0]
    keys = np.zeros((N, n_customers), dtype=np.float64)
    ranks = np.arange(n_customers, dtype=np.float64)
    rank_values = (ranks + 0.5) / n_customers

    for i in range(N):
        keys[i, tours[i]] = rank_values

    return keys
