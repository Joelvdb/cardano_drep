import pandas as pd
from pathlib import Path
import numpy as np


def simulate_direct_votes(config):
    """Simulates proposal votes using direct delegator stake."""
    try:
        deleg_df = pd.read_csv(config.DELEGATORS_STATE_FILE)
    except FileNotFoundError:
        print(
            f"  - ❌ Error: Cannot find {config.DELEGATORS_STATE_FILE.name}. Skipping direct vote sim."
        )
        return

    outcomes = []
    for epoch in deleg_df["epoch"].unique():
        epoch_delegs = deleg_df[deleg_df["epoch"] == epoch].copy()
        if epoch_delegs.empty:
            continue

        for p in config.PROPOSALS:
            prop_op = p["opinion"]
            thresh = config.VOTING_THRESHOLD
            prop_min = max(0.0, prop_op - thresh)
            prop_max = min(1.0, prop_op + thresh)

            # Rule: Delegator votes 'FOR' if their opinion is close to the proposal
            epoch_delegs["vote"] = (epoch_delegs["opinion"] - prop_op).abs() < thresh

            yes_stake = epoch_delegs[epoch_delegs["vote"] == True]["stake"].sum()
            no_stake = epoch_delegs[epoch_delegs["vote"] == False]["stake"].sum()

            outcomes.append(
                {
                    "epoch": epoch,
                    "proposal_id": p["id"],
                    "proposal_opinion": prop_op,
                    "prop_range_min": prop_min,  # <-- NEW
                    "prop_range_max": prop_max,  # <-- NEW
                    "for_stake": yes_stake,
                    "against_stake": no_stake,
                    "outcome": "Pass" if yes_stake > no_stake else "Fail",
                }
            )

    if outcomes:
        out_df = pd.DataFrame(outcomes)
        out_df.to_csv(config.PROPOSAL_OUT_DIRECT, index=False)
        print(f"  Saved direct proposal outcomes: {config.PROPOSAL_OUT_DIRECT.name}")


def simulate_drep_votes(config, model_name: str, input_file: Path, output_file: Path):
    """Simulates proposal votes based on DRep Wprime for a given model."""
    try:
        wprime_df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(
            f"  - ❌ Error: Cannot find {input_file.name}. Skipping '{model_name}' vote sim."
        )
        return

    outcomes = []
    for epoch in wprime_df["epoch"].unique():
        epoch_dreps = wprime_df[wprime_df["epoch"] == epoch].copy()
        if epoch_dreps.empty:
            continue

        for p in config.PROPOSALS:
            prop_op = p["opinion"]
            thresh = config.VOTING_THRESHOLD
            prop_min = max(0.0, prop_op - thresh)
            prop_max = min(1.0, prop_op + thresh)

            # Rule: DRep votes 'FOR' if their opinion is close to the proposal
            epoch_dreps["vote"] = (epoch_dreps["opinion"] - prop_op).abs() <= thresh

            yes_stake = epoch_dreps[epoch_dreps["vote"] == True]["Wprime"].sum()
            no_stake = epoch_dreps[epoch_dreps["vote"] == False]["Wprime"].sum()

            outcomes.append(
                {
                    "epoch": epoch,
                    "proposal_id": p["id"],
                    "proposal_opinion": prop_op,
                    "prop_range_min": prop_min,  # <-- NEW
                    "prop_range_max": prop_max,  # <-- NEW
                    "for_stake": yes_stake,
                    "against_stake": no_stake,
                    "outcome": "Pass" if yes_stake > no_stake else "Fail",
                }
            )

    if outcomes:
        out_df = pd.DataFrame(outcomes)
        out_df.to_csv(output_file, index=False)
        print(f"  Saved '{model_name}' proposal outcomes: {output_file.name}")


def run_proposal_simulation(config):
    """
    Simulates proposal votes for ALL models:
    1. Direct (delegator) voting
    2. Optimal (DRep) voting
    3. Frozen (DRep) voting
    4. Probabilistic (DRep) voting
    """
    print("  Simulating proposal votes for all models...")

    # 1. Direct simulation
    simulate_direct_votes(config)

    # 2. DRep-based simulations
    models_to_run = {
        "optimal": (config.DREPS_OPTIMAL_FILE, config.PROPOSAL_OUT_OPTIMAL),
        "frozen": (config.DREPS_FROZEN_FILE, config.PROPOSAL_OUT_FROZEN),
        "probabilistic": (
            config.DREPS_PROBABILISTIC_FILE,
            config.PROPOSAL_OUT_PROBABILISTIC,
        ),
    }

    for model_name, (in_file, out_file) in models_to_run.items():
        simulate_drep_votes(config, model_name, in_file, out_file)
