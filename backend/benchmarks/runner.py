import logging
import argparse
import numpy as np
import time
from backend.orchestrator import OptimizerOrchestrator
from backend.benchmarks.classical_pso import ClassicalPSO
from backend.benchmarks.genetic_algorithm import GeneticAlgorithm

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_benchmarks():
    logger.info("Starting Benchmark Suite...")
    
    # Base config
    config = {
        "optimizer": {
            "population_size": 50,
            "max_iterations": 100,
            "use_chaotic_init": True,
            "local_search_frequency": 20,
            "levy": {"patience": 15, "jump_fraction": 0.3},
        },
        "vrp": {
            "num_customers": 30,
            "vehicle_capacity": 100.0
        },
        "graph": {
            "mode": "synthetic",
            "grid_size": 10
        }
    }
    
    seeds = [42, 123, 999]
    results_clqpso = []
    results_pso = []
    results_ga = []
    
    for seed in seeds:
        logger.info(f"--- Running Seed {seed} ---")
        config['optimizer']['seed'] = seed
        
        # 1. Run CLQPSO-GLS
        logger.info("Running CLQPSO-GLS...")
        orchestrator = OptimizerOrchestrator(config)
        orchestrator.rng = np.random.RandomState(seed)
        orchestrator.setup_problem(
            num_customers=config['vrp']['num_customers'],
            scenario_file="data/scenarios/baseline.json"
        )
        t0 = time.time()
        res_clqpso = orchestrator.run()
        t1 = time.time()
        results_clqpso.append(res_clqpso.best_fitness)
        logger.info(f"CLQPSO-GLS Cost: {res_clqpso.best_fitness:.2f} (Time: {t1-t0:.2f}s)")
        
        # We can extract the environment from orchestrator to run classical baseline
        cost_mat = orchestrator.cost_matrix_manager.matrix
        demands = orchestrator.demands
        cap = orchestrator.vehicle_capacity
        fitness_eval = orchestrator.fitness_evaluator
        
        # 2. Run Classical PSO
        logger.info("Running Classical PSO...")
        pso = ClassicalPSO(cost_mat, demands, cap, config['optimizer'], fitness_eval, seed)
        t0 = time.time()
        while not pso.should_stop():
            pso.step()
        res_pso = pso.get_result()
        t1 = time.time()
        results_pso.append(res_pso.best_fitness)
        logger.info(f"Classical PSO Cost: {res_pso.best_fitness:.2f} (Time: {t1-t0:.2f}s)")
        
        # 3. Run Genetic Algorithm
        logger.info("Running Genetic Algorithm...")
        ga = GeneticAlgorithm(cost_mat, demands, cap, config['optimizer'], fitness_eval, seed)
        t0 = time.time()
        while not ga.should_stop():
            ga.step()
        res_ga = ga.get_result()
        t1 = time.time()
        results_ga.append(res_ga.best_fitness)
        logger.info(f"Genetic Algorithm Cost: {res_ga.best_fitness:.2f} (Time: {t1-t0:.2f}s)")
        
    logger.info("=== Final Benchmark Results ===")
    logger.info(f"CLQPSO-GLS Mean Cost: {np.mean(results_clqpso):.2f} ± {np.std(results_clqpso):.2f}")
    logger.info(f"Classical PSO Mean Cost: {np.mean(results_pso):.2f} ± {np.std(results_pso):.2f}")
    logger.info(f"Genetic Algorithm Mean Cost: {np.mean(results_ga):.2f} ± {np.std(results_ga):.2f}")

if __name__ == "__main__":
    run_benchmarks()
