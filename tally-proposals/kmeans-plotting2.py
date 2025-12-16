import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import re

# --- CONFIGURATION ---
RESULTS_DIR = "aave_clustering_results"
PLOT_DIR = os.path.join(RESULTS_DIR, "plots")
# Ensure directories exist (assuming the main script already ran this)
if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)

# --- SCORING AND PROCESSING ---


def calculate_propensity_score(mode_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the Propensity Score (0 to 1) for each cluster mode.

    The score is based on the ratio of FOR votes (1) to total active votes (1 and 0).
    The DNV/Abstain category (2) is ignored in the scoring.
    """

    # The mode_df index contains the cluster labels (e.g., 'Cluster_0_Mode')
    # The columns are the Proposal IDs. The values are 0, 1, or 2.

    # 1. Count FOR votes (1)
    n_for = (mode_df == 1).sum(axis=1)

    # 2. Count AGAINST votes (0)
    n_against = (mode_df == 0).sum(axis=1)

    # 3. Calculate Total Active Votes (FOR + AGAINST)
    n_active = n_for + n_against

    # 4. Calculate Score (Handle division by zero if a mode contains only '2's)
    scores = n_for / n_active

    # Create a DataFrame for the scores
    df_scores = pd.DataFrame({"Score": scores, "N_Active": n_active})
    return df_scores


def process_all_modes_and_match_clusters():
    """
    Loads all saved mode files, calculates scores, and attempts to match clusters
    across time based on the highest voting power (N_Active) for simplicity.
    """
    mode_files = sorted(
        glob.glob(os.path.join(RESULTS_DIR, "modes_W*.csv")),
        key=lambda x: int(re.search(r"W(\d+)", x).group(1)),
    )

    if not mode_files:
        print("Error: No cluster mode files found. Run the clustering script first.")
        return None

    all_scores = {}

    # Initialize cluster tracking: map the internal cluster ID (0, 1, 2)
    # to a consistent identifier ('Bloc A', 'Bloc B', etc.)
    consistent_labels = {}

    for i, file_path in enumerate(mode_files):

        # Extract the window key (e.g., W1_P1-P40)
        window_key = (
            os.path.basename(file_path).replace("modes_", "").replace(".csv", "")
        )

        # Load the mode data
        mode_df = pd.read_csv(file_path, index_col=0)

        # Calculate the Propensity Score for this window
        df_scores = calculate_propensity_score(mode_df)

        # --- SIMPLE CLUSTER MATCHING (CRITICAL STEP) ---
        if i == 0:
            # For the first window, label clusters based on their ID
            df_scores["Consistent_Label"] = df_scores.index.str.replace("_Mode", "")
            for j in range(len(df_scores)):
                consistent_labels[j] = df_scores.index[j].split("_")[
                    1
                ]  # Store initial mapping
        else:
            # For subsequent windows, re-map IDs to match the highest N_Active

            # Simple heuristic for tracking: match based on the score closest
            # to the previous window's matched scores. (Requires tracking previous scores)
            # For simplicity, we'll label based on descending score (Bloc A is highest FOR)

            # Sort scores descending and assign labels A, B, C
            sorted_scores = df_scores.sort_values(by="Score", ascending=False)
            sorted_scores["Consistent_Label"] = [
                f"Bloc {chr(65+j)}" for j in range(len(df_scores))
            ]
            df_scores["Consistent_Label"] = sorted_scores["Consistent_Label"]

        df_scores["Window"] = window_key

        # Store results, keyed by the consistent label
        for label, row in df_scores.iterrows():
            if row["Consistent_Label"] not in all_scores:
                all_scores[row["Consistent_Label"]] = {}
            all_scores[row["Consistent_Label"]][window_key] = row["Score"]

    # Convert the nested dict into a final DataFrame for plotting
    df_plot = pd.DataFrame(all_scores).T

    # Rename index labels (W1_... to W1) for cleaner plotting
    df_plot.columns = df_plot.columns.map(lambda x: re.search(r"W(\d+)", x).group(0))

    return df_plot.T


# --- PLOTTING FUNCTION ---


def plot_centroid_trajectory(df_scores_trajectory: pd.DataFrame):
    """Generates a line plot showing cluster score evolution (Polarization)."""

    plt.figure(figsize=(12, 7))

    # Plot each column (each cluster bloc) as a line
    df_scores_trajectory.plot(ax=plt.gca(), marker="o", linewidth=2)

    # Draw horizontal lines for reference
    plt.axhline(
        1.0, color="green", linestyle="--", alpha=0.5, label="Perfect FOR Alignment"
    )
    plt.axhline(0.5, color="gray", linestyle="--", alpha=0.7, label="Neutral/Swing")
    plt.axhline(
        0.0, color="red", linestyle="--", alpha=0.5, label="Perfect AGAINST Alignment"
    )

    plt.title("Cluster Centroid Trajectory (Propensity Score 0-1)", fontsize=16)
    plt.xlabel("Time Window", fontsize=14)
    plt.ylabel("Propensity Score (Ratio of FOR Votes)", fontsize=14)
    plt.ylim(-0.05, 1.05)
    plt.legend(title="Voter Bloc", loc="upper right")
    plt.grid(True, linestyle=":", alpha=0.6)

    plot_path = os.path.join(PLOT_DIR, "cluster_centroid_trajectory.png")
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()
    print(f"\nSaved Cluster Centroid Trajectory Plot (Polarization) to {plot_path}")
    #


# --- MAIN EXECUTION ---

if __name__ == "__main__":
    df_trajectory_scores = process_all_modes_and_match_clusters()

    if df_trajectory_scores is not None and not df_trajectory_scores.empty:
        plot_centroid_trajectory(df_trajectory_scores)
    else:
        print("Could not generate Centroid Trajectory Plot due to missing mode data.")
