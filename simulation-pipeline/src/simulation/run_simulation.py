import pandas as pd
import random
from pathlib import Path

# Import from our new 'src' structure
from src.simulation.models import DRep, Delegator, World
from src.simulation.sampling import (
    sample_opinion_drep, 
    sample_opinion_delegator, 
    sample_stake, 
    sample_stickiness
)

def execute_simulation(config):
    """
    Runs the main simulation to generate raw state CSVs.
    (Converted from state_exporter.minimal_csv.ipynb)
    """
    
    # 1. Set up RNG
    rng = random.Random(config.SEED)

    # 2. Initialize Agents
    print("  Initializing world...")
    
    dreps = [DRep(id=f"d{k+1}", 
                  opinion=sample_opinion_drep(rng), 
                  stake=sample_stake(rng))
             for k in range(config.N_DREPS)]

    delegators = []
    for k in range(config.N_DELEGATORS):
        op = sample_opinion_delegator(rng)
        s  = sample_stickiness(rng)
        st = sample_stake(rng)
        delegators.append(Delegator(id=f"a{k+1}", opinion=op, stake=st, s=s, current=None))

    world = World(dreps=dreps, delegators=delegators, rng=rng)
    print(f"  Initialized with {len(world.dreps)} DReps and {len(world.delegators)} delegators.")

    # 3. Run Simulation Epochs
    dreps_rows = []
    deleg_rows = []

    print(f"  Running simulation for {config.EPOCHS} epochs...")
    for epoch in range(config.EPOCHS):
        
        # Run the internal world dynamics (delegation)
        world.epoch()

        # Snapshot DRep state
        for d in world.dreps:
            dreps_rows.append({
                "epoch": epoch,
                "drep_id": d.id,
                "opinion": d.opinion,
                "stake": d.stake,
            })

        # Snapshot Delegator state
        for a in world.delegators:
            deleg_rows.append({
                "epoch": epoch,
                "delegator_id": a.id,
                "opinion": a.opinion,
                "stake": a.stake,
                "s": a.s,
            })

        # Apply DRep opinion shift for next epoch
        if config.SHIFT_X > 0.0:
            for d in world.dreps:
                d.opinion = min(1.0, d.opinion + config.SHIFT_X)

    # 4. Save CSVs
    print("  Simulation complete. Saving CSVs...")
    
    dreps_df = pd.DataFrame(dreps_rows)
    deleg_df = pd.DataFrame(deleg_rows)

    dreps_df.to_csv(config.DREPS_STATE_FILE, index=False)
    deleg_df.to_csv(config.DELEGATORS_STATE_FILE, index=False)

    print(f"  Saved raw DRep state: {config.DREPS_STATE_FILE.name}")
    print(f"  Saved raw delegator state: {config.DELEGATORS_STATE_FILE.name}")
