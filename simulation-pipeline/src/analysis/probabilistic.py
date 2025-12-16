import pandas as pd
from pathlib import Path
import random

# --- Helper functions specific to this module ---


def _utility(oi: float, oj: float) -> float:
    """Calculate utility based on opinion distance."""
    return 1.0 - abs(float(oi) - float(oj))


def _closest_drep_id(opinion_i: float, D: pd.DataFrame) -> str:
    """Find the DRep ID with the minimum opinion distance."""
    tmp = D[["drep_id", "opinion"]].copy()
    tmp["dist"] = (float(opinion_i) - tmp["opinion"].astype(float)).abs()
    # Sort by distance, then drep_id (as tie-breaker)
    tmp.sort_values(["dist", "drep_id"], inplace=True)
    return tmp.iloc[0]["drep_id"]


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

    epochs = sorted(dreps["epoch"].unique())

    deleg_rows = []
    wprime_rows = []

    # This map tracks the "current" delegation for each delegator across epochs
    current_map = {}

    for epoch in epochs:
        D = dreps.loc[dreps["epoch"] == epoch, ["drep_id", "opinion", "stake"]].copy()
        A = deleg.loc[
            deleg["epoch"] == epoch, ["delegator_id", "opinion", "stake", "s"]
        ].copy()

        if A.empty or D.empty:
            print(f"  Skipping epoch {epoch} (no agents).")
            continue

        # Initialize current (closest) for new delegators
        for _, row in A.iterrows():
            aid = row["delegator_id"]
            if aid not in current_map:
                current_map[aid] = _closest_drep_id(row["opinion"], D)

        drep_op = dict(zip(D["drep_id"], D["opinion"]))
        drep_stake = dict(zip(D["drep_id"], D["stake"]))

        for _, row in A.iterrows():
            aid = row["delegator_id"]
            oi = float(row["opinion"])
            si = float(row["s"])
            cur = current_map[aid]

            best = _closest_drep_id(oi, D)

            u_cur = _utility(oi, drep_op[cur])
            u_best = _utility(oi, drep_op[best])
            delta_u = (u_best - u_cur) ** 1

            p_reconsider = max(0.0, min(1.0, 1.0 - si)) ** 1
            p_switch_cond = max(0.0, min(1.0, float(delta_u))) if delta_u > 0 else 0.0

            p_overall = p_reconsider * (p_switch_cond**si)

            switched = 0
            # Check for switch
            # if (
            #     (rng.random() < p_reconsider)
            #     and (delta_u > 0)
            #     and (rng.random() < p_switch_cond)
            # ):
            if (
                (delta_u > 0)
                and (rng.random() < 0)
            ):
                current_map[aid] = best
                switched = 1

            deleg_rows.append(
                {
                    "epoch": int(epoch),
                    "delegator_id": aid,
                    "drep_id": current_map[aid],  # Save the *final* DRep for this epoch
                    "switched": int(switched),
                    "delta_u": float(delta_u),
                    "p_reconsider": float(p_reconsider),
                    "p_switch_cond": float(p_switch_cond),
                    "p_overall": float(p_overall),
                }
            )

        # Compute Wprime for epoch
        Wprime = {d: float(st) for d, st in drep_stake.items()}

        # We need the *final* delegations for this epoch to calculate Wprime
        epoch_deleg_map = {
            r["delegator_id"]: r["drep_id"] for r in deleg_rows if r["epoch"] == epoch
        }

        for _, row in A.iterrows():
            aid = row["delegator_id"]
            st = float(row["stake"])
            dr = epoch_deleg_map.get(aid)  # Get the final assigned DRep
            if dr and dr in Wprime:
                Wprime[dr] += st

        # --- FIX IS HERE ---
        # 1. Calculate total Wprime for the epoch
        total_Wprime = sum(Wprime.values())

        for d_id in D["drep_id"]:
            wp_val = float(Wprime[d_id])

            # 2. Calculate share
            wp_share = (wp_val / total_Wprime) if total_Wprime > 0 else 0.0

            wprime_rows.append(
                {
                    "epoch": int(epoch),
                    "drep_id": d_id,
                    "opinion": float(drep_op[d_id]),
                    "stake": float(drep_stake[d_id]),
                    "delegated_stake": float(wp_val - drep_stake[d_id]),
                    "Wprime": wp_val,
                    "Wprime_share": wp_share,  # 3. Add to output
                }
            )
        # --- END OF FIX ---

    # Save outputs
    deleg_df = pd.DataFrame(
        deleg_rows,
        columns=[
            "epoch",
            "delegator_id",
            "drep_id",
            "switched",
            "delta_u",
            "p_reconsider",
            "p_switch_cond",
            "p_overall",
        ],
    )

    # 4. Add 'Wprime_share' to the columns list
    wprime_df = pd.DataFrame(
        wprime_rows,
        columns=[
            "epoch",
            "drep_id",
            "opinion",
            "stake",
            "delegated_stake",
            "Wprime",
            "Wprime_share",
        ],
    )

    deleg_df.to_csv(config.DELEGATIONS_PROBABILISTIC_FILE, index=False)
    wprime_df.to_csv(config.DREPS_PROBABILISTIC_FILE, index=False)

    print(
        f"  Saved probabilistic delegations: {config.DELEGATIONS_PROBABILISTIC_FILE.name}"
    )
    print(f"  Saved probabilistic DRep state: {config.DREPS_PROBABILISTIC_FILE.name}")
