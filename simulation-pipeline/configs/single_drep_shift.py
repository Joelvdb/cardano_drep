# (New file: configs/single_drep_shift.py)

from .base_config import *

print("--- ⚠️  Loaded EXPERIMENTAL config: single_drep_shift ---")

# 1. Disable the old "all DReps" shift
SHIFT_X = 0.0


# 2. Define the new targeted shift
# This will shift DRep 'd1' by +0.1 each epoch.
TARGET_DREP_ID = "d1"
TARGET_DREP_SHIFT = 0.1

# 3. (Optional) Give it a new seed so it's a new simulation
SEED = 101
