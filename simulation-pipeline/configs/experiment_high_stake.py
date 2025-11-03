# This is an example of an experimental config.
# It imports all base settings, then overrides just the ones we want to change.

from .base_config import *

N_DREPS = 500
N_DELEGATORS = 10000
EPOCHS = 20
SEED = 999
SHIFT_X = 0.0 # Disable opinion shift

print("--- ⚠️  Loaded EXPERIMENTAL config: high_stake ---")
