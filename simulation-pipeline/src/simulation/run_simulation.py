import pandas as pd
import random
from pathlib import Path

# Import from our new 'src' structure
from src.simulation.models import DRep, Delegator, World
from src.simulation.sampling import (
    sample_opinion_drep,
    sample_opinion_delegator,
    sample_stake,
    sample_stickiness,
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

    dreps = [
        DRep(id=f"d{k+1}", opinion=sample_opinion_drep(rng), stake=sample_stake(rng))
        for k in range(config.N_DREPS)
    ]

    delegators = []
    for k in range(config.N_DELEGATORS):
        op = sample_opinion_delegator(rng)
        s = sample_stickiness(rng)
        st = sample_stake(rng)
        delegators.append(
            Delegator(id=f"a{k+1}", opinion=op, stake=st, s=s, current=None)
        )

    world = World(dreps=dreps, delegators=delegators, rng=rng)
    print(
        f"  Initialized with {len(world.dreps)} DReps and {len(world.delegators)} delegators."
    )

    # 3. Run Simulation Epochs
    dreps_rows = []
    deleg_rows = []

    # --- MODIFICATION: Define the global shift pattern ---
    # Pattern: one positive, twice negative, twice positive, twice negative
    shift_pattern = [1.0, -1.0, -1.0, 1.0, 1.0, -1.0, -1.0, 1, 1, -1, -1, 1]
    shift_pattern = [1 for i in range(20)]
    pattern_length = len(shift_pattern)

    # We will use config.TARGET_DREP_SHIFT as the magnitude for this pattern
    # (or fall back to SHIFT_X if it's not defined)
    shift_amount = 0.0
    if hasattr(config, "TARGET_DREP_SHIFT") and config.TARGET_DREP_SHIFT > 0.0:
        shift_amount = config.TARGET_DREP_SHIFT
        print(f"  Using pattern-based shift for ALL DReps. Amount: {shift_amount}")
    elif hasattr(config, "") and config.SHIFT_X > 0.0:
        shift_amount = config.SHIFT_X
        print(
            f"  Using pattern-based shift for ALL DReps. Amount (from SHIFT_X): {shift_amount}"
        )
    else:
        print(
            "  WARNING: No DRep shift amount defined (TARGET_DREP_SHIFT or SHIFT_X). DReps will not move."
        )

    print(f"  Running simulation for {config.EPOCHS} epochs...")
    for epoch in range(config.EPOCHS):

        # Run the internal world dynamics (delegation)
        world.epoch()

        # Snapshot DRep state
        for d in world.dreps:
            dreps_rows.append(
                {
                    "epoch": epoch,
                    "drep_id": d.id,
                    "opinion": d.opinion,
                    "stake": d.stake,
                }
            )

        # Snapshot Delegator state
        for a in world.delegators:
            deleg_rows.append(
                {
                    "epoch": epoch,
                    "delegator_id": a.id,
                    "opinion": a.opinion,
                    "stake": a.stake,
                    "s": a.s,
                }
            )

        # --- MODIFICATION: Apply pattern-based opinion shift to ALL DReps ---
        # Apply DRep opinion shift for next epoch
        # Check for targeted shift first
        target_id = getattr(config, "TARGET_DREP_ID", None)
        target_shift = getattr(config, "TARGET_DREP_SHIFT", None)

        if target_id is not None and target_shift is not None:
            # Targeted shift mode
            for d in world.dreps:
                if d.id == target_id:
                    d.opinion = min(1.0, max(0.0, d.opinion + target_shift))
        elif shift_amount > 0.0:
            # Global shift mode (fallback)
            # Get current direction from the pattern based on the *current* epoch
            current_direction = shift_pattern[epoch % pattern_length]

            for d in world.dreps:
                # Calculate new opinion
                old_op = d.opinion
                new_op = old_op + (shift_amount * current_direction)

                # Clamp the opinion between 0.0 and 1.0
                if new_op > 1.0:
                    new_op = 1.0
                elif new_op < 0.0:
                    new_op = 0.0

                d.opinion = new_op
        # --- End of MODIFICATION ---

    # 4. Save CSVs
    print("  Simulation complete. Saving CSVs...")

    dreps_df = pd.DataFrame(dreps_rows)
    deleg_df = pd.DataFrame(deleg_rows)

    dreps_df.to_csv(config.DREPS_STATE_FILE, index=False)
    deleg_df.to_csv(config.DELEGATORS_STATE_FILE, index=False)

    print(f"  Saved raw DRep state: {config.DREPS_STATE_FILE.name}")
    print(f"  Saved raw delegator state: {config.DELEGATORS_STATE_FILE.name}")
