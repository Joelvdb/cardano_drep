import pandas as pd
from kmodes.kmodes import KModes
import numpy as np
import os
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONFIGURATION ---
INPUT_FILENAME = "./tally-proposals/aave_all_voter_records.csv"
RESULTS_DIR = "aave_clustering_results"

# Ensure directories exist
PLOT_DIR = os.path.join(RESULTS_DIR, "plots")
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)
if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)

# Rolling Window Parameters
W = 40  # Window Size (Number of proposals)
S = 10  # Step Size (Window moves by this many proposals)
k = 3  # Number of clusters (voting blocs)
MIN_VOTES_REQUIRED = 5  # Minimum number of votes a voter must cast
# within a window (W=40) to be included in clustering.

# --- VOTE MAPPING & PREPARATION ---


def prepare_data(df_votes: pd.DataFrame) -> pd.DataFrame:
    """Encodes votes and pivots the data into the Voter-Proposal Matrix."""

    # Map active vote types. Non-active/abstain/missing will be NaN.
    # Note: Use the column names you provided (Voter_Address, Onchain_ID, Vote_Type).
    vote_mapping = {"for": 1, "against": 0}
    df_votes["Vote_Numeric"] = df_votes["Vote_Type"].map(vote_mapping)

    # Create the Voter-Proposal Matrix
    voter_proposal_matrix = df_votes.pivot_table(
        index="Voter_Address",
        columns="Onchain_ID",  # Using Onchain_ID for proposal unique identifier
        values="Vote_Numeric",
    )
    return voter_proposal_matrix


def exclude_non_voters_in_window(
    df_window: pd.DataFrame, min_votes: int
) -> tuple[pd.DataFrame, list]:
    """
    Filters the window data to keep only voters who meet the activity threshold.
    """

    # Count non-NaN votes (active FOR/AGAINST votes)
    active_votes_count = df_window.count(axis=1)

    # Identify and filter for active voters
    active_voters_index = active_votes_count[active_votes_count >= min_votes].index
    df_filtered = df_window.loc[active_voters_index]

    # Handle remaining scattered NaNs: fill with a unique integer (e.g., 2)
    # This treats the occasional non-vote as a distinct categorical choice for clustering.
    df_final = df_filtered.fillna(2).astype(int)

    print(
        f"    -> Window filtered: {len(active_voters_index)} voters remain (out of {len(df_window)} total voters)."
    )
    return df_final, active_voters_index.tolist()


# --- ROLLING WINDOW EXECUTION ---


def run_rolling_window_clustering(voter_proposal_matrix: pd.DataFrame):
    """Executes the rolling window clustering strategy."""

    all_proposal_ids = voter_proposal_matrix.columns.tolist()
    num_proposals = len(all_proposal_ids)

    start_index = 0
    window_number = 0
    all_voter_assignments = defaultdict(dict)

    print(f"\n--- Starting Rolling Window Analysis (W={W}, S={S}, k={k}) ---")
    print(f"Total Proposals: {num_proposals}. Min votes required: {MIN_VOTES_REQUIRED}")

    while start_index + W <= num_proposals:
        window_number += 1
        end_index = start_index + W

        window_proposal_ids = all_proposal_ids[start_index:end_index]
        df_current_window = voter_proposal_matrix[window_proposal_ids]

        # 1. Exclude Non-Voters and Prepare Data
        df_final_data, active_voters = exclude_non_voters_in_window(
            df_current_window, MIN_VOTES_REQUIRED
        )

        # 2. Apply k-Modes Clustering
        if len(df_final_data) < k:
            print(
                "    -> Not enough active voters to form k clusters. Skipping window."
            )
        else:
            kmode = KModes(
                n_clusters=k, init="Huang", n_init=5, verbose=0, random_state=42
            )
            clusters = kmode.fit_predict(df_final_data)

            # 3. Store Results
            window_key = f"W{window_number}_P{start_index+1}-P{end_index}"

            for voter, cluster_id in zip(active_voters, clusters):
                all_voter_assignments[voter][window_key] = cluster_id

            modes_df = pd.DataFrame(
                kmode.cluster_centroids_, columns=window_proposal_ids
            )
            modes_df.index = [f"Cluster_{i}_Mode" for i in range(k)]
            modes_df.to_csv(os.path.join(RESULTS_DIR, f"modes_{window_key}.csv"))

            print(f"Completed window {window_number}. Cluster modes saved.")

        # 4. Move the window forward
        start_index += S

    print("--- Rolling Window Analysis Complete ---")

    # 5. Compile and save the final trajectory data
    if all_voter_assignments:
        df_trajectory = pd.DataFrame(all_voter_assignments).T
        # Sort columns chronologically (important for plotting)
        sorted_cols = sorted(
            df_trajectory.columns, key=lambda x: int(x.split("_")[0][1:])
        )
        df_trajectory = df_trajectory[sorted_cols]

        trajectory_filename = os.path.join(
            RESULTS_DIR, "voter_trajectory_assignments.csv"
        )
        df_trajectory.to_csv(trajectory_filename)
        print(f"\nSuccessfully generated voter trajectory file: {trajectory_filename}")
        return df_trajectory
    return pd.DataFrame()


# --- PLOTTING FUNCTIONS ---


def plot_voter_trajectory_heatmap(df_trajectory: pd.DataFrame):
    """Generates a heatmap to visualize individual voter movement."""

    plt.figure(figsize=(18, 10))

    # Sort voters (rows) by their cluster in the last window for visual grouping
    last_window = df_trajectory.columns[-1]
    df_sorted = df_trajectory.sort_values(by=last_window, na_position="first")

    # FIX: Convert to float to handle np.nan correctly for plotting
    plot_data = df_sorted.T.astype(float)

    sns.heatmap(
        plot_data,
        cmap="viridis",
        cbar_kws={"label": "Cluster ID"},
        linewidths=0.5,
        linecolor="lightgray",
        # Mask np.nan values (voters who were excluded from the window)
        mask=plot_data.isna(),
    )

    plt.title("Voter Cluster Assignment Trajectories Across Time Windows", fontsize=16)
    plt.xlabel("Voter Address (Sorted by final Cluster ID)", fontsize=14)
    plt.ylabel("Time Window", fontsize=14)
    plt.yticks(rotation=0)

    plot_path = os.path.join(PLOT_DIR, "voter_trajectories_heatmap.png")
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()
    print(f"Saved Voter Trajectory Heatmap to {plot_path}")
    #


def plot_cluster_evolution_area(df_trajectory: pd.DataFrame):
    """Generates a stacked area plot showing the total count of voters in each cluster over time."""

    # 1. Count members per cluster for each window
    df_counts = df_trajectory.apply(pd.Series.value_counts, axis=0).fillna(0).T

    # 2. Normalize counts to percentages for stacked area plot
    # Normalize by row (axis=1) sum to get proportions
    df_proportions = df_counts.div(df_counts.sum(axis=1), axis=0)

    plt.figure(figsize=(12, 7))

    df_proportions.plot(
        kind="area", stacked=True, ax=plt.gca(), cmap="tab10", linewidth=0
    )

    plt.title(
        "Evolution of Voter Bloc Size (Cluster Proportions) Over Time", fontsize=16
    )
    plt.xlabel("Time Window", fontsize=14)
    plt.ylabel("Proportion of Active Voters", fontsize=14)
    plt.legend(title="Cluster ID", loc="upper left")
    plt.ylim(0, 1)

    plot_path = os.path.join(PLOT_DIR, "cluster_evolution_area.png")
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()
    print(f"Saved Cluster Evolution Area Plot to {plot_path}")
    #


# --- MAIN EXECUTION ---


def main():
    try:
        df_raw = pd.read_csv(INPUT_FILENAME)
    except FileNotFoundError:
        print(f"Error: Input file '{INPUT_FILENAME}' not found. Ensure the CSV exists.")
        return
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    # 1. Prepare Data and Run Clustering
    voter_proposal_matrix = prepare_data(df_raw)
    df_assignments = run_rolling_window_clustering(voter_proposal_matrix)

    # 2. Generate Plots
    if not df_assignments.empty:
        plot_voter_trajectory_heatmap(df_assignments)
        plot_cluster_evolution_area(df_assignments)

        print(
            "\nAnalysis Complete. Check the 'aave_clustering_results/plots' directory for visualizations."
        )
    else:
        print(
            "\nClustering failed to produce results. Please check your data or configuration."
        )


if __name__ == "__main__":
    main()
