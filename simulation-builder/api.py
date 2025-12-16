from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path
import random
import pandas as pd

# Add simulation-pipeline to sys.path to import from src
# This assumes api.py is in ada_drep/simulation-builder/api.py
# and src is in ada_drep/simulation-pipeline/src
pipeline_dir = Path(__file__).parent.parent / "simulation-pipeline"
sys.path.append(str(pipeline_dir))

from src.simulation.models import World, DRep, Delegator
from src.simulation.sampling import (
    sample_opinion_drep,
    sample_opinion_delegator,
    sample_stake,
    sample_stickiness
)
import configs.base_config as base_config

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-Memory State ---
current_world: Optional[World] = None
simulation_results: Dict[str, Any] = {}

# --- Pydantic Models ---

class SimulationConfig(BaseModel):
    n_dreps: int = 100
    n_delegators: int = 2000
    epochs: int = 10
    shift_x: float = 0.1
    seed: int = 421
    seed: int = 421
    # Multi-target configuration
    # List of dicts: [{"id": "d1", "shift": 0.1}, ...]
    targets: List[Dict[str, Any]] = [] 
    # New distribution params
    # New distribution params
    opinion_dist: str = "uniform" # uniform, beta
    stake_dist: str = "uniform"   # uniform, beta
    delegation_model: str = "probabilistic" # probabilistic, responsive, frozen
    custom_logic: Optional[str] = None # Python code to run per epoch

class DRepModel(BaseModel):
    id: str
    opinion: float
    stake: float
    delegated_stake: float = 0.0
    w_prime: float = 0.0

class DelegatorModel(BaseModel):
    id: str
    opinion: float
    stake: float
    s: float
    current_drep_id: Optional[str] = None
    # New metrics
    last_delta_u: float = 0.0
    last_responsive_id: Optional[str] = None
    is_frozen: bool = False

class InitResponse(BaseModel):
    dreps: List[DRepModel]
    delegators: List[DelegatorModel]
    message: str

# --- Endpoints ---

@app.get("/config")
def get_default_config():
    """Returns the default configuration from base_config.py"""
    return {
        "n_dreps": base_config.N_DREPS,
        "n_delegators": base_config.N_DELEGATORS,
        "epochs": base_config.EPOCHS,
        "shift_x": base_config.SHIFT_X,
        "seed": base_config.SEED,
        "target_drep_id": getattr(base_config, "TARGET_DREP_ID", None),
        "target_drep_shift": getattr(base_config, "TARGET_DREP_SHIFT", None),
    }

@app.post("/init", response_model=InitResponse)
def initialize_simulation(config: SimulationConfig):
    """Initializes the world with the given configuration."""
    global current_world
    
    rng = random.Random(config.seed)
    
    # 1. Create DReps
    dreps = [DRep(id=f"d{k+1}", 
                  opinion=sample_opinion_drep(rng, dist_type=config.opinion_dist), 
                  stake=sample_stake(rng, dist_type=config.stake_dist))
             for k in range(config.n_dreps)]

    # 2. Create Delegators
    delegators = []
    for k in range(config.n_delegators):
        op = sample_opinion_delegator(rng, dist_type=config.opinion_dist)
        s  = sample_stickiness(rng)
        st = sample_stake(rng, dist_type=config.stake_dist)
        delegators.append(Delegator(id=f"a{k+1}", opinion=op, stake=st, s=s, current=None))

    current_world = World(dreps=dreps, delegators=delegators, rng=rng)
    
    # Perform initial delegation so "Delegated To" is populated
    for delegator in delegators:
        delegator.delegate(dreps, rng, model_type=config.delegation_model)

    # Convert to Pydantic models for response
    drep_models = [DRepModel(id=d.id, opinion=d.opinion, stake=d.stake) for d in dreps]
    delegator_models = [DelegatorModel(
        id=d.id, 
        opinion=d.opinion, 
        stake=d.stake, 
        s=d.s,
        last_delta_u=d.last_delta_u,
        last_responsive_id=d.last_responsive_id,
        is_frozen=d.is_frozen
    ) for d in delegators]
    
    return {
        "dreps": drep_models,
        "delegators": delegator_models,
        "message": f"Initialized world with {len(dreps)} DReps and {len(delegators)} Delegators."
    }

@app.post("/update-delegator")
def update_delegator(delegator_data: DelegatorModel):
    """Updates a specific delegator's parameters."""
    global current_world
    if not current_world:
        raise HTTPException(status_code=400, detail="World not initialized. Call /init first.")
    
    # Find the delegator
    target = next((d for d in current_world.delegators if d.id == delegator_data.id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Delegator {delegator_data.id} not found.")
    
    # Update fields
    target.opinion = delegator_data.opinion
    target.stake = delegator_data.stake
    target.s = delegator_data.s
    
    return {"message": f"Delegator {target.id} updated."}

@app.post("/run")
def run_simulation_loop(config: SimulationConfig):
    """Runs the simulation loop based on the current world state."""
    global current_world, simulation_results
    if not current_world:
        raise HTTPException(status_code=400, detail="World not initialized. Call /init first.")
    
    dreps_history = []
    delegators_history = []
    
    # Helper for Gini
    def gini(array):
        """Calculate the Gini coefficient of a numpy array."""
        # based on bottom-up strategy
        if not array: return 0.0
        array = sorted(array)
        height, area = 0, 0
        for value in array:
            height += value
            area += height - value / 2.
        fair_area = height * len(array) / 2.
        return (fair_area - area) / fair_area

    def weighted_median(values, weights):
        """Calculate the weighted median of a list of values."""
        if not values: return 0.0
        data = sorted(zip(values, weights), key=lambda x: x[0])
        total_weight = sum(weights)
        cum_weight = 0
        for v, w in data:
            cum_weight += w
            if cum_weight >= total_weight / 2:
                return v
        return data[-1][0]

    for epoch in range(config.epochs):
        # 1. Run Epoch
        current_world.epoch(model_type=config.delegation_model)
        
        # Calculate Metrics
        w_primes = [d.w_prime for d in current_world.dreps]
        opinions = [d.opinion for d in current_world.dreps]
        
        gini_val = gini(w_primes)
        median_val = float(pd.Series(w_primes).median())
        weighted_median_op = weighted_median(opinions, w_primes)

        # 2. Snapshot
        for d in current_world.dreps:
            dreps_history.append({
                "epoch": epoch,
                "drep_id": d.id,
                "opinion": d.opinion,
                "stake": d.stake,
                "w_prime": d.w_prime,
                "delegated_stake": d.delegated_stake,
                # Add global metrics to each row (redundant but easy for UI)
                "gini": gini_val,
                "median_power": median_val,
                "weighted_median_opinion": weighted_median_op
            })
            
        # For performance in UI, maybe we don't send ALL delegator history every time if it's huge?
        # But for now, let's send it.
        for a in current_world.delegators:
            delegators_history.append({
                "epoch": epoch,
                "delegator_id": a.id,
                "opinion": a.opinion,
                "stake": a.stake,
                "s": a.s,
                "current_drep_id": a.current.id if a.current else None,
                "last_delta_u": a.last_delta_u,
                "last_responsive_id": a.last_responsive_id,
                "is_frozen": a.is_frozen
            })
            
        # 3. Apply Shift
        if config.custom_logic and config.custom_logic.strip():
            # Custom Logic Execution
            try:
                # Context available to the user script
                context = {
                    "dreps": current_world.dreps,
                    "delegators": current_world.delegators,
                    "epoch": epoch,
                    "rng": current_world.rng,
                    "random": random,
                    # "math": math # Import math if needed
                }
                exec(config.custom_logic, {}, context)
            except Exception as e:
                print(f"Error executing custom logic in epoch {epoch}: {e}")
                # Optionally break or continue, for now we print and continue
        elif config.targets:
            # Multi-target shift
            for target in config.targets:
                t_id = target.get("id")
                t_shift = target.get("shift", 0.0)
                for d in current_world.dreps:
                    if d.id == t_id:
                        d.opinion = min(1.0, max(0.0, d.opinion + t_shift))
        elif config.shift_x > 0.0:
             # Global shift fallback
            for d in current_world.dreps:
                d.opinion = min(1.0, d.opinion + config.shift_x)

    return {
        "message": "Simulation complete",
        "dreps_history": dreps_history,
        "delegators_history": delegators_history
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
