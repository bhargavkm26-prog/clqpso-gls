# CLQPSO-GLS: Quantum-Inspired Dynamic Traffic Route Optimization

## Chaotic Lévy Quantum Particle Swarm Optimization with Guided Local Search

> A quantum-inspired dynamic vehicle-routing framework for SIH 2026 — Quantum Technology Vertical.

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the optimizer on a benchmark instance
python -m backend.benchmarks.runner --instance A-n32-k5

# Start the API server
python -m backend.main

# Start the frontend (in another terminal)
cd frontend && npm install && npm run dev
```

### Architecture

See `docs/algorithm_design.md` for the full mathematical specification.

### References

1. Sun, Feng & Xu (2004) — Core QPSO formulation
2. Prins (2004) — Giant-tour + Split decoder for CVRP
3. Vidal (2022) — SWAP* operator + O(n) Linear Split
4. Mantegna (1994) — Lévy-stable step generation
5. Voudouris & Tsang (1999) — Guided Local Search
