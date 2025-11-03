#!/bin/bash

# --- Create sub-directories ---
mkdir -p configs
mkdir -p data/{raw,analysis/{optimal,frozen,probabilistic},plots}
mkdir -p src/{simulation,analysis,proposals,plotting}

# --- Create empty __init__.py files ---
touch src/__init__.py
touch src/simulation/__init__.py
touch src/analysis/__init__.py
touch src/proposals/__init__.py
touch src/plotting/__init__.py

# --- 1. Create run_pipeline.py ---
cat << 'EOF' > run_pipeline.py
import argparse
import importlib
from pathlib import Path

# --- Import your pipeline functions ---
from src.simulation.run_simulation import execute_simulation
from src.analysis.optimal import run_optimal_analysis
from src.analysis.frozen import run_frozen_analysis
from src.analysis.probabilistic import run_probabilistic_analysis
from src.proposals.simulate_votes import run_proposal_simulation
from src.plotting.comparative_plots import run_plotting

# --- Analysis "Plugin" Map ---
# This map makes it easy to add new analysis types
ANALYSIS_MODELS = {
    "optimal": run_optimal_analysis,
    "frozen": run_frozen_analysis,
    "probabilistic": run_probabilistic_analysis,
}

def get_config(config_name: str):
    """Dynamically imports a config file from the configs/ directory."""
    try:
        # Add 'configs' to sys.path to ensure it's found
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        config_module = importlib.import_module(f"configs.{config_name}")
        print(f"✅ Loaded configuration: 'configs/{config_name}.py'")
        return config_module
    except ImportError as e:
        print(f"❌ Error: Config file 'configs/{config_name}.py' not found.")
        print(f"👉 Make sure the file exists and has no syntax errors.")
        print(f"Details: {e}")
        exit(1)
    finally:
        # Clean up sys.path
        if 'sys' in locals() and str(Path(__file__).resolve().parent) in sys.path:
            sys.path.pop(0)

def main():
    parser = argparse.ArgumentParser(description="Run the DRep Simulation Pipeline")
    
    parser.add_argument(
        "--config",
        type=str,
        default="base_config",
        help="The name of the config file to use (e.g., 'base_config' or 'experiment_high_stake')."
    )
    
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run Step 1: Generate raw simulation data."
    )
    
    parser.add_argument(
        "--analyze",
        nargs="+",  # Accepts one or more values
        choices=list(ANALYSIS_MODELS.keys()) + ["all"],
        help=f"Run Step 2: Run one or more analysis models. Choices: {list(ANALYSIS_MODELS.keys())} or 'all'"
    )
    
    parser.add_argument(
        "--proposals",
        action="store_true",
        help="Run Step 3: Simulate proposal voting on analysis results."
    )
    
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Run Step 4: Generate plots from the analysis results."
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all steps in order: simulate, analyze (all), proposals, plot."
    )
    
    args = parser.parse_args()
    
    # --- Load Config ---
    # We need to add the project root to sys.path for configs and src to be importable
    import sys
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root))
    
    try:
        config_module = importlib.import_module(f"configs.{args.config}")
        print(f"✅ Loaded configuration: 'configs/{args.config}.py'")
    except ImportError as e:
        print(f"❌ Error: Config file 'configs/{args.config}.py' not found.")
        print(f"👉 Make sure the file exists and has no syntax errors.")
        print(f"Details: {e}")
        exit(1)

    # --- Determine which steps to run ---
    run_simulate = args.simulate or args.all
    run_analyze = args.analyze or args.all
    run_proposals = args.proposals or args.all
    run_plot = args.plot or args.all
    
    if not any([run_simulate, run_analyze, run_proposals, run_plot]):
        print("🔔 No steps selected. Use --help to see options.")
        return

    # --- Execute Pipeline Steps ---
    
    if run_simulate:
        print("\n--- 1. Running Simulation ---")
        config_module.create_directories() # Ensure dirs exist
        execute_simulation(config_module)


    if run_analyze:
        print("\n--- 2. Running Analysis ---")
        config_module.create_directories() # Ensure dirs exist
        
        models_to_run = []
        if args.all:
            models_to_run = ANALYSIS_MODELS.keys()
        elif args.analyze:
            if "all" in args.analyze:
                models_to_run = ANALYSIS_MODELS.keys()
            else:
                models_to_run = args.analyze
        
        for model_name in models_to_run:
            if model_name in ANALYSIS_MODELS:
                print(f"Running analysis model: '{model_name}'...")
                analysis_func = ANALYSIS_MODELS[model_name]
                analysis_func(config_module)
        print("✅ Analysis complete.")

    if run_proposals:
        print("\n--- 3. Running Proposal Simulation ---")
        config_module.create_directories() # Ensure dirs exist
        run_proposal_simulation(config_module)
        print("✅ Proposal simulation complete.")

    if run_plot:
        print("\n--- 4. Generating Plots ---")
        config_module.create_directories() # Ensure dirs exist
        run_plotting(config_module)
        print("✅ Plotting complete.")

    print("\n🎉 Pipeline finished.")
    
    # Clean up sys.path
    if str(project_root) in sys.path:
        sys.path.pop(0)

if __name__ == "__main__":
    main()
EOF

# --- 2. Create configs/base_config.py ---
cat << 'EOF' > configs/base_config.py
from pathlib import Path
import random

# --- Base Project Directory ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- 1. Simulation Parameters ---
N_DREPS = 100
N_DELEGATORS = 2000
EPOCHS = 10
SHIFT_X = 0.1  # DRep opinion shift per epoch
SEED = 421

# --- 2. Probabilistic Model Parameters ---
# Seed for the probabilistic delegation notebook
PROBABILISTIC_SEED = 12345

# --- 3. Directory Configuration ---
# Source data directory
DATA_DIR = BASE_DIR / "data"

# Step 1: Raw Simulation Output
DATA_DIR_RAW = DATA_DIR / "raw"
DREPS_STATE_FILE = DATA_DIR_RAW / "dreps_state.csv"
DELEGATORS_STATE_FILE = DATA_DIR_RAW / "delegators_state.csv"

# Step 2: Analysis Outputs
DATA_DIR_ANALYSIS = DATA_DIR / "analysis"

# Optimal
DATA_DIR_OPTIMAL = DATA_DIR_ANALYSIS / "optimal"
DELEGATORS_OPTIMAL_FILE = DATA_DIR_OPTIMAL / "delegators_state_with_delegations.csv"
DREPS_OPTIMAL_FILE = DATA_DIR_OPTIMAL / "dreps_state_with_wprime.csv"

# Frozen
DATA_DIR_FROZEN = DATA_DIR_ANALYSIS / "frozen"
DELEGATORS_FROZEN_FILE = DATA_DIR_FROZEN / "delegators_state_frozen.csv"
DREPS_FROZEN_FILE = DATA_DIR_FROZEN / "dreps_state_with_wprime_frozen.csv"

# Probabilistic
DATA_DIR_PROBABILISTIC = DATA_DIR_ANALYSIS / "probabilistic"
DELEGATIONS_PROBABILISTIC_FILE = DATA_DIR_PROBABILISTIC / "delegations_probabilistic.csv"
DREPS_PROBABILISTIC_FILE = DATA_DIR_PROBABILISTIC / "dreps_wprime_probabilistic.csv"

# Step 3: Proposal Simulation Outputs
PROPOSAL_SIM_FILE = DATA_DIR_ANALYSIS / "proposal_outcomes.csv"

# Step 4: Plotting Outputs
PLOT_DIR = DATA_DIR / "plots"


# --- Helper function to ensure all directories exist ---
def create_directories():
    """Creates all configured data directories."""
    dirs = [
        DATA_DIR, DATA_DIR_RAW, DATA_DIR_ANALYSIS,
        DATA_DIR_OPTIMAL, DATA_DIR_FROZEN, DATA_DIR_PROBABILISTIC,
        PLOT_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
EOF

# --- 3. Create src/simulation/models.py ---
cat << 'EOF' > src/simulation/models.py
import random
from typing import Optional, List

# --- Core Simulation Classes ---
# (Content from your utils.py)

class DRep:
    def __init__(self, id: str, opinion: float, stake: float):
        self.id: str = str(id)
        self.opinion: float = float(opinion)
        self.stake: float = float(stake)
        self.delegated_stake: float = 0.0
        self.w_prime: float = 0.0  # w_prime = stake + delegated_stake

    def update_w_prime(self):
        self.w_prime = self.stake + self.delegated_stake

    def __repr__(self) -> str:
        return (f"DRep(id={self.id}, opinion={self.opinion:.2f}, "
                f"stake={self.stake:.2f}, w_prime={self.w_prime:.2f})")

class Delegator:
    def __init__(self, id: str, opinion: float, stake: float, s: float, current: Optional[DRep]):
        self.id: str = str(id)
        self.opinion: float = float(opinion)
        self.stake: float = float(stake)
        self.s: float = float(s)  # Stickiness in [0, 1]
        self.current: Optional[DRep] = current

    def utility(self, drep: DRep) -> float:
        """Calculates utility for a given DRep."""
        return 1.0 - abs(self.opinion - drep.opinion)

    def find_best_drep(self, dreps: List[DRep]) -> DRep:
        """Finds the best DRep by utility (opinion proximity)."""
        best_drep = max(dreps, key=lambda d: (self.utility(d), d.id))
        return best_drep

    def delegate(self, dreps: List[DRep], rng: random.Random):
        """
        Decision-making logic for delegation based on stickiness and utility.
        """
        # 1. Reconsideration
        if self.current is None:
            # No current DRep, must choose one
            best_drep = self.find_best_drep(dreps)
            self.current = best_drep
            # print(f"delegator {self.id} initial delegation to {self.current.id}")
            return

        if rng.random() >= (1.0 - self.s):
            # Maintained delegation due to stickiness
            # print(f"delegator {self.id} maintained due to stickiness")
            return

        # 2. Re-evaluation
        best_drep = self.find_best_drep(dreps)
        
        current_utility = self.utility(self.current)
        best_utility = self.utility(best_drep)
        delta_u = best_utility - current_utility

        # 3. Switching
        if delta_u > 0:
            # Switch with probability delta_u
            if rng.random() < delta_u:
                self.current = best_drep
                # print(f"delegator {self.id} switched to {self.current.id} (delta_u={delta_u:.2f})")
            # else:
                # print(f"delegator {self.id} re-evaluated but did not switch")
        # else:
            # print(f"delegator {self.id} maintained due to utility")

    def __repr__(self) -> str:
        current_id = self.current.id if self.current else "None"
        return (f"Delegator(id={self.id}, opinion={self.opinion:.2f}, "
                f"stake={self.stake:.2f}, s={self.s:.2f}, current={current_id})")

class World:
    def __init__(self, dreps: List[DRep], delegators: List[Delegator], rng: random.Random):
        self.dreps = dreps
        self.delegators = delegators
        self.rng = rng

    def epoch(self):
        """Simulates one epoch of delegation."""
        
        # 1. Reset DRep delegated stake
        for drep in self.dreps:
            drep.delegated_stake = 0.0

        # 2. Delegators make their decisions
        for delegator in self.delegators:
            delegator.delegate(self.dreps, self.rng)
        
        # 3. Tally new delegated stake
        for delegator in self.delegators:
            if delegator.current:
                delegator.current.delegated_stake += delegator.stake
        
        # 4. Update DRep w_prime values
        for drep in self.dreps:
            drep.update_w_prime()

    def __repr__(self) -> str:
        return f"World(DReps={len(self.dreps)}, Delegators={len(self.delegators)})"
EOF

# --- 4. Create src/simulation/sampling.py ---
cat << 'EOF' > src/simulation/sampling.py
import random

# --- Agent Parameter Sampling Functions ---

def sample_opinion_drep(rng: random.Random) -> float:
    # Example: bimodal-ish around 0.25 / 0.75
    return rng.random()

def sample_opinion_delegator(rng: random.Random) -> float:
    return rng.random()

def sample_stake(rng: random.Random) -> float:
    return rng.random()

def sample_stickiness(rng: random.Random, mean=0.6, k=40) -> float:
    # a = mean * k
    # b = (1 - mean) * k
    # return rng.betavariate(a, b)
    return rng.random()

# --- You can add new sampling functions here ---
# def sample_stake_v2(rng: random.Random) -> float:
#     return rng.gammavariate(2.0, 1.0)
EOF

# --- 5. Create src/simulation/run_simulation.py ---
cat << 'EOF' > src/simulation/run_simulation.py
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
EOF

# --- 6. Create src/analysis/utils.py ---
cat << 'EOF' > src/analysis/utils.py
import pandas as pd

def assign_closest_dreps_df(Ae: pd.DataFrame, De: pd.DataFrame) -> pd.DataFrame:
    """
    Assigns each delegator in DataFrame Ae to the closest DRep in DataFrame De.
    
    Returns a DataFrame with [delegator_id, drep_id, drep_opinion, distance].
    """
    a = Ae[['delegator_id','opinion']].rename(columns={'opinion':'op_a'}).copy()
    d = De[['drep_id','opinion']].rename(columns={'opinion':'op_d'}).copy()
    
    a['key'] = 1
    d['key'] = 1
    
    pairs = a.merge(d, on='key').drop(columns=['key'])
    pairs['distance'] = (pairs['op_a'] - pairs['op_d']).abs()
    
    # Sort by distance, then drep_id (as a tie-breaker)
    nearest = (pairs.sort_values(['delegator_id','distance','drep_id'])
                    .groupby('delegator_id', as_index=False)
                    .first())
                    
    nearest = nearest.rename(columns={'op_d':'drep_opinion'})
    
    return nearest[['delegator_id','drep_id','drep_opinion','distance']]
EOF

# --- 7. Create src/analysis/optimal.py ---
cat << 'EOF' > src/analysis/optimal.py
import pandas as pd
from pathlib import Path
from src.analysis.utils import assign_closest_dreps_df # Import the shared function

def run_optimal_analysis(config):
    """
    Assigns, for each epoch, each delegator to the *closest* DRep by opinion.
    (Converted from build_states_with_delegations_and_wprime_optimal.ipynb)
    """
    
    # Load inputs
    try:
        dreps = pd.read_csv(config.DREPS_STATE_FILE)
        deleg = pd.read_csv(config.DELEGATORS_STATE_FILE)
    except FileNotFoundError:
        print(f"❌ Error: Input files not found in '{config.DATA_DIR_RAW}'.")
        print("👉 Run the --simulate step first.")
        return

    delegator_rows = []
    drep_rows = []
    epochs = sorted(dreps['epoch'].unique())

    for e in epochs:
        D = dreps.loc[dreps['epoch'] == e, ['drep_id','opinion','stake']].copy()
        A = deleg.loc[deleg['epoch'] == e, ['delegator_id','opinion','stake','s']].copy()

        if A.empty or D.empty:
            print(f"  Skipping epoch {e} (no agents).")
            continue
            
        nearest = assign_closest_dreps_df(A, D)
        joined = (A.merge(nearest, on='delegator_id', how='left'))

        # Delegator rows
        for _, r in joined.iterrows():
            delegator_rows.append({
                'epoch': int(e),
                'delegator_id': r['delegator_id'],
                'opinion': float(r['opinion']),
                'stake': float(r['stake']),
                's': float(r['s']),
                'drep_id': r['drep_id'],
                'drep_opinion': float(r['drep_opinion']),
                'distance': float(r['distance']),
            })

        # DRep aggregates
        own = dict(zip(D['drep_id'], D['stake']))
        delegated_stake = joined.groupby('drep_id')['stake'].sum().to_dict()
        indeg = joined.groupby('drep_id')['delegator_id'].count().to_dict()
        avgdist = joined.groupby('drep_id')['distance'].mean().to_dict()

        total_Wprime = 0.0
        tmp = []
        for d_id, op in zip(D['drep_id'], D['opinion']):
            del_st = float(delegated_stake.get(d_id, 0.0))
            own_st = float(own.get(d_id, 0.0))
            Wp = own_st + del_st
            total_Wprime += Wp
            tmp.append({
                'epoch': int(e),
                'drep_id': d_id,
                'opinion': float(op),
                'stake': own_st,
                'delegated_stake': del_st,
                'indegree': int(indeg.get(d_id, 0)),
                'avg_distance': float(avgdist.get(d_id, 0.0)),
                'Wprime': Wp,
            })
            
        for row in tmp:
            row['Wprime_share'] = (row['Wprime'] / total_Wprime) if total_Wprime > 0 else 0.0
            drep_rows.append(row)

    # Save outputs
    pd.DataFrame(delegator_rows).to_csv(config.DELEGATORS_OPTIMAL_FILE, index=False)
    pd.DataFrame(drep_rows).to_csv(config.DREPS_OPTIMAL_FILE, index=False)

    print(f"  Saved optimal delegator state: {config.DELEGATORS_OPTIMAL_FILE.name}")
    print(f"  Saved optimal DRep state: {config.DREPS_OPTIMAL_FILE.name}")
EOF

# --- 8. Create src/analysis/frozen.py ---
cat << 'EOF' > src/analysis/frozen.py
import pandas as pd
from pathlib import Path
from src.analysis.utils import assign_closest_dreps_df # Import the shared function

def run_frozen_analysis(config):
    """
    Builds CSV outputs where delegations are "frozen" from the first epoch
    a delegator is seen.
    (Converted from build_frozen_delegations.ipynb)
    """
    
    # Load inputs
    try:
        dreps = pd.read_csv(config.DREPS_STATE_FILE)
        deleg = pd.read_csv(config.DELEGATORS_STATE_FILE)
    except FileNotFoundError:
        print(f"❌ Error: Input files not found in '{config.DATA_DIR_RAW}'.")
        print("👉 Run the --simulate step first.")
        return

    # First seen epoch per delegator
    first_seen = deleg.groupby('delegator_id', as_index=False)['epoch'].min().rename(columns={'epoch':'first_epoch'})
    deleg = deleg.merge(first_seen, on='delegator_id', how='left')

    dreps['drep_id'] = dreps['drep_id'].astype(str)
    deleg['delegator_id'] = deleg['delegator_id'].astype(str)

    epochs = sorted(dreps['epoch'].unique())

    frozen_map = {}
    delegator_rows = []
    drep_rows = []

    for e in epochs:
        D = dreps.loc[dreps['epoch'] == e, ['drep_id','opinion','stake']].copy()
        A = deleg.loc[deleg['epoch'] == e, ['delegator_id','opinion','stake','s','first_epoch']].copy()
        
        if A.empty or D.empty:
            print(f"  Skipping epoch {e} (no agents).")
            continue

        # Freeze mapping at first seen epoch
        new_ids = [aid for aid, fe in zip(A['delegator_id'], A['first_epoch']) if (aid not in frozen_map) and (fe == e)]
        if new_ids:
            Ae_new = A[A['delegator_id'].isin(new_ids)][['delegator_id','opinion']].copy()
            nearest_new = assign_closest_dreps_df(Ae_new, D)
            for _, row in nearest_new.iterrows():
                frozen_map[row['delegator_id']] = row['drep_id']

        # Fallback: if any still unassigned (data quirks), assign now
        missing = [aid for aid in A['delegator_id'] if aid not in frozen_map]
        if missing:
            Ae_new = A[A['delegator_id'].isin(missing)][['delegator_id','opinion']].copy()
            nearest_new = assign_closest_dreps_df(Ae_new, D)
            for _, row in nearest_new.iterrows():
                frozen_map[row['delegator_id']] = row['drep_id']

        # Build per-delegator rows for epoch e
        map_df = pd.DataFrame({'delegator_id': list(A['delegator_id']), 'drep_id': [frozen_map.get(aid) for aid in A['delegator_id']]}).astype(str)
        D_op = D[['drep_id','opinion']].rename(columns={'opinion':'drep_opinion'})
        joined = A.merge(map_df, on='delegator_id', how='left').merge(D_op, on='drep_id', how='left')
        joined['distance'] = (joined['opinion'] - joined['drep_opinion']).abs()

        for _, r in joined.iterrows():
            delegator_rows.append({
                'epoch': int(e),
                'delegator_id': r['delegator_id'],
                'opinion': float(r['opinion']),
                'stake': float(r['stake']),
                's': float(r['s']),
                'drep_id': r['drep_id'],
                'drep_opinion': float(r['drep_opinion']),
                'distance': float(r['distance']),
            })

        # DRep aggregates
        own = dict(zip(D['drep_id'], D['stake']))
        delegated_stake = joined.groupby('drep_id')['stake'].sum().to_dict()
        indeg = joined.groupby('drep_id')['delegator_id'].count().to_dict()
        avgdist = joined.groupby('drep_id')['distance'].mean().to_dict()

        all_ids = list(D['drep_id'])
        total_Wprime = 0.0
        tmp = []
        for d_id in all_ids:
            del_st = float(delegated_stake.get(d_id, 0.0))
            own_st = float(own.get(d_id, 0.0))
            Wp = own_st + del_st
            total_Wprime += Wp
            tmp.append({
                'epoch': int(e),
                'drep_id': d_id,
                'opinion': float(D.loc[D['drep_id']==d_id, 'opinion'].iloc[0]),
                'stake': own_st,
                'delegated_stake': del_st,
                'indegree': int(indeg.get(d_id, 0)),
                'avg_distance': float(avgdist.get(d_id, 0.0)),
                'Wprime': Wp,
            })
            
        for row in tmp:
            row['Wprime_share'] = (row['Wprime'] / total_Wprime) if total_Wprime > 0 else 0.0
            drep_rows.append(row)

    # Save outputs
    pd.DataFrame(delegator_rows).to_csv(config.DELEGATORS_FROZEN_FILE, index=False)
    pd.DataFrame(drep_rows).to_csv(config.DREPS_FROZEN_FILE, index=False)

    print(f"  Saved frozen delegator state: {config.DELEGATORS_FROZEN_FILE.name}")
    print(f"  Saved frozen DRep state: {config.DREPS_FROZEN_FILE.name}")
EOF

# --- 9. Create src/analysis/probabilistic.py ---
cat << 'EOF' > src/analysis/probabilistic.py
import pandas as pd
from pathlib import Path
import random

# --- Helper functions specific to this module ---

def _utility(oi: float, oj: float) -> float:
    """Calculate utility based on opinion distance."""
    return 1.0 - abs(float(oi) - float(oj))

def _closest_drep_id(opinion_i: float, D: pd.DataFrame) -> str:
    """Find the DRep ID with the minimum opinion distance."""
    tmp = D[['drep_id','opinion']].copy()
    tmp['dist'] = (float(opinion_i) - tmp['opinion'].astype(float)).abs()
    # Sort by distance, then drep_id (as tie-breaker)
    tmp.sort_values(['dist','drep_id'], inplace=True)
    return tmp.iloc[0]['drep_id']

# --- Main execution function ---

def run_probabilistic_analysis(config):
    """
    Reconstructs delegations per epoch using the probabilistic rule
    from the model (stickiness & utility).
    (Converted from delegations_probabilistic.ipynb)
    """
    
    # Set up RNG for this analysis
    rng = random.Random(config.PROBABILISTIC_SEED)

    # Load inputs
    try:
        dreps = pd.read_csv(config.DREPS_STATE_FILE)
        deleg = pd.read_csv(config.DELEGATORS_STATE_FILE)
    except FileNotFoundError:
        print(f"❌ Error: Input files not found in '{config.DATA_DIR_RAW}'.")
        print("👉 Run the --simulate step first.")
        return
        
    epochs = sorted(dreps['epoch'].unique())

    deleg_rows = []
    wprime_rows = []
    
    # This map tracks the "current" delegation for each delegator across epochs
    current_map = {} 

    for epoch in epochs:
        D = dreps.loc[dreps['epoch'] == epoch, ['drep_id','opinion','stake']].copy()
        A = deleg.loc[deleg['epoch'] == epoch, ['delegator_id','opinion','stake','s']].copy()
        
        if A.empty or D.empty:
            print(f"  Skipping epoch {epoch} (no agents).")
            continue

        # Initialize current (closest) for new delegators
        for _, row in A.iterrows():
            aid = row['delegator_id']
            if aid not in current_map:
                current_map[aid] = _closest_drep_id(row['opinion'], D)

        drep_op = dict(zip(D['drep_id'], D['opinion']))
        drep_stake = dict(zip(D['drep_id'], D['stake']))

        for _, row in A.iterrows():
            aid = row['delegator_id']
            oi  = float(row['opinion'])
            si  = float(row['s'])
            cur = current_map[aid]

            best = _closest_drep_id(oi, D)

            u_cur = _utility(oi, drep_op[cur])
            u_best = _utility(oi, drep_op[best])
            delta_u = u_best - u_cur

            p_reconsider = max(0.0, min(1.0, 1.0 - si))
            p_switch_cond = max(0.0, min(1.0, float(delta_u))) if delta_u > 0 else 0.0
            p_overall = p_reconsider * p_switch_cond

            switched = 0
            # Check for switch
            if (rng.random() < p_reconsider) and (delta_u > 0) and (rng.random() < p_switch_cond):
                current_map[aid] = best
                switched = 1

            deleg_rows.append({
                'epoch': int(epoch),
                'delegator_id': aid,
                'drep_id': current_map[aid], # Save the *final* DRep for this epoch
                'switched': int(switched),
                'delta_u': float(delta_u),
                'p_reconsider': float(p_reconsider),
                'p_switch_cond': float(p_switch_cond),
                'p_overall': float(p_overall),
            })

        # Compute Wprime for epoch
        Wprime = {d: float(st) for d, st in drep_stake.items()}
        
        # We need the *final* delegations for this epoch to calculate Wprime
        epoch_deleg_map = {r['delegator_id']: r['drep_id'] for r in deleg_rows if r['epoch'] == epoch}
        
        for _, row in A.iterrows():
            aid = row['delegator_id']
            st  = float(row['stake'])
            dr  = epoch_deleg_map.get(aid) # Get the final assigned DRep
            if dr and dr in Wprime:
                Wprime[dr] += st

        for d_id in D['drep_id']:
            wprime_rows.append({
                'epoch': int(epoch),
                'drep_id': d_id,
                'opinion': float(drep_op[d_id]),
                'stake': float(drep_stake[d_id]),
                'delegated_stake': float(Wprime[d_id] - drep_stake[d_id]),
                'Wprime': float(Wprime[d_id]),
            })

    # Save outputs
    deleg_df = pd.DataFrame(deleg_rows, columns=[
        'epoch','delegator_id','drep_id','switched','delta_u',
        'p_reconsider','p_switch_cond','p_overall'
    ])
    wprime_df = pd.DataFrame(wprime_rows, columns=[
        'epoch','drep_id','opinion','stake','delegated_stake','Wprime'
    ])

    deleg_df.to_csv(config.DELEGATIONS_PROBABILISTIC_FILE, index=False)
    wprime_df.to_csv(config.DREPS_PROBABILISTIC_FILE, index=False)

    print(f"  Saved probabilistic delegations: {config.DELEGATIONS_PROBABILISTIC_FILE.name}")
    print(f"  Saved probabilistic DRep state: {config.DREPS_PROBABILISTIC_FILE.name}")
EOF

# --- 10. Create src/proposals/simulate_votes.py ---
cat << 'EOF' > src/proposals/simulate_votes.py
import pandas as pd
from pathlib import Path

def run_proposal_simulation(config):
    """
    Simulates proposal votes based on the Wprime results
    from the analysis step.
    (Stubbed from proposal_votes_simulation.ipynb)
    """
    print("  Simulating proposal votes...")
    
    # --- Example Logic ---
    # This is a placeholder. You can replace this with your
    # actual proposal simulation logic.
    
    outcomes = []
    
    # 1. Load one of the analysis results (e.g., optimal)
    try:
        wprime_df = pd.read_csv(config.DREPS_OPTIMAL_FILE)
        model_name = "optimal" # Track which model is used
    except FileNotFoundError:
        print(f"  - ⚠️ Warning: Could not find optimal DRep file. Trying probabilistic...")
        try:
            wprime_df = pd.read_csv(config.DREPS_PROBABILISTIC_FILE)
            model_name = "probabilistic"
        except FileNotFoundError:
            print(f"  - ❌ Error: No DRep Wprime files found. Skipping proposal sim.")
            return

    print(f"  - Using '{model_name}' model for proposal simulation.")

    # 2. Define some proposals
    proposals = [
        {"id": "p1", "opinion": 0.25},
        {"id": "p2", "opinion": 0.75},
    ]

    # 3. Simulate for each epoch
    for epoch in wprime_df['epoch'].unique():
        epoch_dreps = wprime_df[wprime_df['epoch'] == epoch].copy()
        
        if epoch_dreps.empty:
            continue
            
        # Example rule: DRep votes "Yes" if their opinion is within 0.2 of proposal
        for p in proposals:
            epoch_dreps['vote'] = (epoch_dreps['opinion'] - p['opinion']).abs() < 0.2
            
            yes_stake = epoch_dreps[epoch_dreps['vote'] == True]['Wprime'].sum()
            no_stake = epoch_dreps[epoch_dreps['vote'] == False]['Wprime'].sum()
            total_stake = yes_stake + no_stake
            
            outcomes.append({
                "epoch": epoch,
                "model": model_name,
                "proposal_id": p['id'],
                "proposal_opinion": p['opinion'],
                "yes_wprime": yes_stake,
                "no_wprime": no_stake,
                "outcome": "Pass" if yes_stake > no_stake else "Fail"
            })
            
    # 4. Save results
    out_df = pd.DataFrame(outcomes)
    out_df.to_csv(config.PROPOSAL_SIM_FILE, index=False)
    print(f"  Saved proposal outcomes: {config.PROPOSAL_SIM_FILE.name}")
EOF

# --- 11. Create src/plotting/comparative_plots.py ---
cat << 'EOF' > src/plotting/comparative_plots.py
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def load_data(config):
    """Helper to load all analysis results for plotting."""
    data = {}
    files_to_load = {
        "optimal": config.DREPS_OPTIMAL_FILE,
        "frozen": config.DREPS_FROZEN_FILE,
        "probabilistic": config.DREPS_PROBABILISTIC_FILE
    }
    
    for model_name, file_path in files_to_load.items():
        try:
            data[model_name] = pd.read_csv(file_path)
        except FileNotFoundError:
            print(f"  - ⚠️ Warning: Could not find file {file_path.name}. Skipping for plots.")
            
    if not data:
        print(f"❌ Error: No analysis data found in {config.DATA_DIR_ANALYSIS}.")
        print("👉 Run the --analyze step first.")
        return None
        
    return data

def plot_wprime_share(config, data):
    """Example plot: Wprime share of top 5 DReps over time."""
    print("  Generating Wprime share plot...")
    
    num_models = len(data)
    if num_models == 0: return

    fig, axes = plt.subplots(1, num_models, figsize=(7 * num_models, 6), sharey=True)
    if num_models == 1:
        axes = [axes] # Make it iterable
        
    fig.suptitle("Wprime Share of Top 5 DReps Over Time", fontsize=16)

    for ax, (model_name, df) in zip(axes, data.items()):
        
        # Get top 5 DReps from epoch 0
        if 0 not in df['epoch'].values:
            print(f"  - ⚠️ Skipping plot for {model_name}: no epoch 0 data.")
            continue
            
        top5 = df[df['epoch'] == 0].nlargest(5, 'Wprime')['drep_id']
        plot_data = df[df['drep_id'].isin(top5)]
        
        for drep_id in top5:
            drep_data = plot_data[plot_data['drep_id'] == drep_id]
            ax.plot(drep_data['epoch'], drep_data.get('Wprime_share', 0), label=drep_id, marker='o', markersize=4)
        
        ax.set_title(model_name.capitalize())
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Wprime Share")
        ax.legend(loc="upper left")
        ax.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save plot
    save_path = config.PLOT_DIR / "wprime_share_top5.png"
    plt.savefig(save_path)
    print(f"  Saved plot: {save_path.name}")
    plt.close(fig)

def run_plotting(config):
    """
    Generates all plots for the simulation.
    (Converted from plot_from_csv...ipynb)
    """
    
    data = load_data(config)
    if data is None:
        return
        
    # --- Call all your plotting functions ---
    plot_wprime_share(config, data)
    # Add more plot functions here...
    # plot_total_distance(config, data)
    # plot_indegree_distribution(config, data)
EOF

# --- 12. Create configs/experiment_high_stake.py (Example) ---
cat << 'EOF' > configs/experiment_high_stake.py
# This is an example of an experimental config.
# It imports all base settings, then overrides just the ones we want to change.

from .base_config import *

N_DREPS = 500
N_DELEGATORS = 10000
EPOCHS = 20
SEED = 999
SHIFT_X = 0.0 # Disable opinion shift

print("--- ⚠️  Loaded EXPERIMENTAL config: high_stake ---")
EOF

# --- Done ---
echo ""
echo "✅ All files and directories created inside 'your_project_directory'."
echo "You can now run the pipeline:"
echo ""
echo "  cd your_project_directory"
echo "  python3 run_pipeline.py --all"
echo ""
echo "Or run an experiment:"
echo "  python3 run_pipeline.py --config experiment_high_stake --simulate --analyze optimal"
echo ""