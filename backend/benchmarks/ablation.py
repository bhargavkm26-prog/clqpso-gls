import logging
import time
import numpy as np
from backend.orchestrator import OptimizerOrchestrator

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_ablation_study():
    logger.info("Starting Ablation Study for CLQPSO-GLS...")
    
    base_config = {
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
    
    scenarios = {
        "Full CLQPSO-GLS": {},
        "No Local Search": {"local_search_frequency": 999999}, # effectively disable GLS
        "No Chaotic Init": {"use_chaotic_init": False},
        "No Levy Flight": {"levy": {"patience": 999999, "jump_fraction": 0.0}}
    }
    
    seed = 42
    results = {}
    
    for name, overrides in scenarios.items():
        logger.info(f"--- Running Scenario: {name} ---")
        
        # Build config for this scenario
        config = base_config.copy()
        config['optimizer'] = base_config['optimizer'].copy()
        for k, v in overrides.items():
            config['optimizer'][k] = v
        config['optimizer']['seed'] = seed
        
        orchestrator = OptimizerOrchestrator(config)
        orchestrator.rng = np.random.RandomState(seed)
        orchestrator.setup_problem(
            num_customers=config['vrp']['num_customers'],
            scenario_file="data/scenarios/baseline.json"
        )
        
        t0 = time.time()
        res = orchestrator.run()
        t1 = time.time()
        
        results[name] = {
            "cost": res.best_fitness,
            "time": t1 - t0
        }
        
        logger.info(f"{name} -> Cost: {res.best_fitness:.2f} (Time: {t1-t0:.2f}s)")
        
    logger.info("=== Ablation Study Summary ===")
    for name, res in results.items():
        logger.info(f"{name:20} | Cost: {res['cost']:.2f} | Time: {res['time']:.2f}s")
        
if __name__ == "__main__":
    run_ablation_study()
