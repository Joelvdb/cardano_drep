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

# Step 3: Proposal Simulation Outputs
DATA_DIR_PROPOSALS = DATA_DIR_ANALYSIS / "proposals"
PROPOSAL_OUT_DIRECT = DATA_DIR_PROPOSALS / "proposals_direct.csv"
PROPOSAL_OUT_OPTIMAL = DATA_DIR_PROPOSALS / "proposals_optimal.csv"
PROPOSAL_OUT_FROZEN = DATA_DIR_PROPOSALS / "proposals_frozen.csv"
PROPOSAL_OUT_PROBABILISTIC = DATA_DIR_PROPOSALS / "proposals_probabilistic.csv"

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
DELEGATIONS_PROBABILISTIC_FILE = (
    DATA_DIR_PROBABILISTIC / "delegations_probabilistic.csv"
)
DREPS_PROBABILISTIC_FILE = DATA_DIR_PROBABILISTIC / "dreps_wprime_probabilistic.csv"

# Step 3: Proposal Simulation Outputs
PROPOSAL_SIM_FILE = DATA_DIR_ANALYSIS / "proposal_outcomes.csv"

# Step 4: Plotting Outputs
PLOT_DIR = DATA_DIR / "plots"

# --- 5. Per-Epoch Plotting Parameters ---
# (From your new plotting script)
USE_STAKE_SIZE = True
SIZE_SCALE_DELEG = 0.5
SIZE_SCALE_DREPS = 1.0
JITTER = 0.02
DRAW_EDGES = True
EDGE_ALPHA = 0.05
EDGE_LW = 0.5
EDGE_SAMPLES = 200  # Max number of edges to draw
COLOR_SWITCHED = True  # Only used for 'probabilistic' model


# --- Helper function to ensure all directories exist ---
def create_directories():
    """Creates all configured data directories."""
    dirs = [
        DATA_DIR,
        DATA_DIR_RAW,
        DATA_DIR_ANALYSIS,
        DATA_DIR_OPTIMAL,
        DATA_DIR_FROZEN,
        DATA_DIR_PROBABILISTIC,
        DATA_DIR_PROPOSALS,  # <-- ADD THIS LINE
        PLOT_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
