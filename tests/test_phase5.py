"""
Phase 5 verification test.

Tests:
1. Logistic-Tent chaotic map generation
2. Lévy flight steps (Mantegna algorithm)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from backend.optimizer.initialization import logistic_tent_map
from backend.optimizer.levy import LevyFlight


def test_phase5():
    print("=" * 60)
    print("PHASE 5 VERIFICATION TEST")
    print("=" * 60)

    # 1. Test Chaotic Initialization
    print("\n[1/2] Testing Logistic-Tent Chaotic Map...")
    shape = (50, 20)
    chaotic_seq = logistic_tent_map(shape)
    
    assert chaotic_seq.shape == shape
    assert np.all((chaotic_seq > 0.0) & (chaotic_seq < 1.0))
    
    # Check that it doesn't collapse to a single value
    unique_vals = len(np.unique(chaotic_seq))
    assert unique_vals > 0.9 * np.prod(shape), f"Low diversity in chaos: {unique_vals}/{np.prod(shape)}"
    
    mean_val = np.mean(chaotic_seq)
    print(f"  ✓ Shape correct: {chaotic_seq.shape}")
    print(f"  ✓ Bounds respected (0, 1)")
    print(f"  ✓ High uniqueness: {unique_vals} / {np.prod(shape)}")
    print(f"  ✓ Mean value: {mean_val:.4f} (expected ~0.5)")

    # 2. Test Lévy Flight
    print("\n[2/2] Testing Lévy Flight (Mantegna)...")
    levy = LevyFlight(config={"levy": {"beta": 1.5, "jump_scale": 0.1}}, seed=42)
    
    # Test step generation
    steps = levy.generate_steps(shape)
    assert steps.shape == shape
    
    # Lévy steps should have heavy tails (some large values)
    max_step = np.max(np.abs(steps))
    mean_step = np.mean(np.abs(steps))
    
    print(f"  ✓ Sigma_u: {levy.sigma_u:.4f}")
    print(f"  ✓ Mean step magnitude: {mean_step:.4f}")
    print(f"  ✓ Max step magnitude: {max_step:.4f}")
    assert max_step > 5 * mean_step, "Lévy steps missing heavy tail"
    
    # Test apply_jump
    population = np.zeros(shape) + 0.5  # All 0.5
    num_jump = 10
    
    levy.apply_jump(population, num_particles_to_jump=num_jump)
    
    # First 40 should be untouched (0.5)
    assert np.allclose(population[:40, :], 0.5)
    
    # Last 10 should be changed and bounded in [0, 1]
    assert not np.allclose(population[40:, :], 0.5)
    assert np.all((population[40:, :] >= 0.0) & (population[40:, :] <= 1.0))
    
    print(f"  ✓ Jump applied selectively to worst {num_jump} particles")
    print(f"  ✓ Jumped particles bounded within [0, 1]")

    print("\n" + "=" * 60)
    print("✅ ALL PHASE 5 TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_phase5()
