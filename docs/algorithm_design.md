# CLQPSO-GLS Algorithm Design

## Overview
CLQPSO-GLS (Chaotic Levy Quantum Particle Swarm Optimization with Guided Local Search) is a hybrid metaheuristic designed for the Capacitated Vehicle Routing Problem (CVRP) in dynamic road networks (e.g., Bangalore).

The objective is to route a fleet of homogeneous vehicles to serve a set of customer demands, minimizing the total travel cost (distance or time) without exceeding vehicle capacity. 

This solver achieves high performance via four key innovations:
1. **Quantum Particle Swarm Optimization (QPSO)**: Replaces traditional velocity-based PSO with a quantum delta potential well model, allowing particles to sample globally without bounds.
2. **Chaotic Initialization**: Uses logistic mapping for initial particle distribution, covering the search space more evenly than uniform random distribution.
3. **Lévy Flights**: Introduces heavy-tailed jumps (Lévy distribution) to rescue the swarm when stagnation is detected, overcoming local optima.
4. **Guided Local Search (GLS)**: Applies edge penalties and local optimization (2-opt, SWAP*) to refine routes directly in the physical domain after SPV (Smallest Position Value) decoding.

## Representation & Decoding
- **Random-Key Encoding**: Each particle is an $N$-dimensional vector in $[0, 1]^N$.
- **SPV Decoding**: Sorting the random keys yields a sequence of customers (the Giant Tour).
- **Prins' Split Algorithm**: Evaluates all feasible trips in $O(n^2)$ (or $O(n)$ with bounds) and uses a Shortest Path algorithm (Bellman-Ford / DAG shortest path) to slice the Giant Tour into valid capacity-constrained routes.

## QPSO Position Update
For each dimension $j$ of particle $i$:

1. **Local Attractor ($p_{ij}$)**:
   $$ p_{ij} = \phi P_{ij} + (1-\phi) G_j $$
   where $P$ is personal best, $G$ is global best, and $\phi \sim U(0,1)$.

2. **Mean Best Position ($M_j$)**:
   $$ M_j = \frac{1}{N} \sum_{k=1}^N P_{kj} $$

3. **Position Update**:
   $$ X_{ij} = p_{ij} \pm \alpha |M_j - X_{ij}| \ln(1/u) $$
   where $u \sim U(0,1)$ and $\alpha$ is the contraction-expansion coefficient, which adapts per particle based on diversity.

## Algorithm Flow
1. **Init**: Generate initial population using Chaotic maps.
2. **Decode**: Convert random keys -> Giant Tour -> Routes via Split.
3. **Evaluate**: Calculate fitness (total travel cost).
4. **Update PBest & GBest**: Track individual and global bests.
5. **Local Search (GLS)**: Periodically apply 2-opt and SWAP* to the GBest routes. Reverse-map the improved routes back to random keys.
6. **Diversity Check**: Measure swarm variance. If below threshold (stagnation), trigger Lévy flights for a subset of particles.
7. **QPSO Update**: Compute mean best and update all particles.
8. **Loop**: Repeat until max iterations or time limit.
