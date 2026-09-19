# CLQPSO-GLS: Quantum-Inspired Dynamic Traffic Route Optimization

## Chaotic Lévy Quantum Particle Swarm Optimization with Guided Local Search

> A quantum-inspired dynamic vehicle-routing framework for SIH 2026 — Quantum Technology Vertical.

This project implements an advanced vehicle routing optimization engine that dynamically adapts to real-time traffic conditions. It combines **Chaotic Lévy Quantum Particle Swarm Optimization (CLQPSO)** with **Guided Local Search (GLS)** and the **SWAP* Operator** to rapidly escape local optima and balance loads across delivery vehicles. 

A React-based dashboard visualizes the routes in real-time, allowing users to toggle different traffic scenarios (Baseline, Moderate, Disruption, Recovery) and watch the AI dynamically reroute vehicles on a live OSMnx road network.

---

## 🚀 Quick Start Guide for Evaluators

This project requires both a Python backend (FastAPI) and a Node.js frontend (React + Vite). Please follow these steps to set up and evaluate the project.

### 1. Prerequisites
- Python 3.9+
- Node.js 18+ (and npm)
- Git

### 2. Backend Setup (Python)

Open a terminal in the root directory of the project (`clqpso-gls`):

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install all required Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup (Node.js)

Open a **second terminal** and navigate to the `frontend` folder:

```bash
cd frontend

# Install all required Node packages
npm install
```

### 4. Running the Application

You will need to run the backend and frontend simultaneously in two separate terminals.

**Terminal 1 (Backend):**
From the root directory (`clqpso-gls`), run:
```bash
python -m backend.main
```
*Note: The first time the backend starts, it will download the road network map from OpenStreetMap (OSMnx). This may take a few minutes. Subsequent startups will load instantly from the local cache.*

**Terminal 2 (Frontend):**
From the `frontend` directory, run:
```bash
npm run dev
```

The frontend terminal will output a local URL (usually `http://localhost:5173`). Open this URL in your web browser to view the interactive dashboard.

---

## 🧠 Core Technologies & Algorithms

- **CLQPSO (Chaotic Lévy QPSO):** A quantum-inspired swarm algorithm that uses Lévy flights and chaotic maps to maintain high swarm diversity, preventing premature convergence.
- **GLS (Guided Local Search):** Penalizes overused or congested road segments to force the algorithm to explore alternative routes when trapped in a local optimum.
- **SWAP* Operator:** An advanced routing heuristic that rapidly exchanges customers between different vehicle routes to balance loads and reduce overall fleet mileage.
- **OSMnx:** Used for real-world street network retrieval and accurate shortest-path routing.

## 📚 References

1. Sun, Feng & Xu (2004) — Core QPSO formulation
2. Prins (2004) — Giant-tour + Split decoder for CVRP
3. Vidal (2022) — SWAP* operator + O(n) Linear Split
4. Mantegna (1994) — Lévy-stable step generation
5. Voudouris & Tsang (1999) — Guided Local Search
