import pandas as pd
from kmodes.kmodes import KModes
import numpy as np
import os
from collections import defaultdict

# --- CONFIGURATION ---
INPUT_FILENAME = (
    "./tally-proposals/aave_all_voter_records.csv"  # Ensure your CSV is named this
)
RESULTS_DIR = "aave_clustering_results"
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

# Rolling Window Parameters
W = 40  # Window Size (Number of proposals)
S = 10  # Step Size (Window moves by this many proposals)
k = 3  # Number of clusters (voting blocs: e.g., For, Against, Swing)
MIN_VOTES_REQUIRED = 5  # Minimum number of votes a voter must cast
# within a window (W=40) to be included in clustering.

# --- VOTE MAPPING & PREPARATION ---


def prepare_data(df_votes: pd.DataFrame) -> pd.DataFrame:
    """Encodes votes and pivots the data into the Voter-Proposal Matrix."""

    # 1. Encode Vote Type to Numerical/Categorical
    # Only map the active votes (FOR/AGAINST). Leave ABSTAIN/NULL as NaN for now.
    # Note: Using 1 and 0 for active votes, making it a binary clustering
    # for the active vote subset.
    vote_mapping = {"for": 1, "agianst": 0}

    # Apply mapping, leaving all other Vote_Types (ABSTAIN, NULL, etc.) as NaN.
    df_votes["Vote_Numeric"] = df_votes["Vote_Type"].map(vote_mapping)

    # 2. Create the Voter-Proposal Matrix
    # Index = Voters, Columns = Proposals, Values = Encoded Votes (1/0 or NaN)
    voter_proposal_matrix = df_votes.pivot_table(
        index="Voter_Address",
        columns="Onchain_ID",  # Use Onchain_ID for reliable proposal tracking
        values="Vote_Numeric",
        # Do NOT use fill_value here; we need NaN for non-votes/abstentions to count active votes.
    )

    return voter_proposal_matrix


def exclude_non_voters_in_window(
    df_window: pd.DataFrame, min_votes: int
) -> tuple[pd.DataFrame, list]:
    """
    Filters the window data to keep only voters who meet the activity threshold
    (MIN_VOTES_REQUIRED) and handles remaining NaNs.
    """

    # 1. Count non-NaN votes (i.e., actual FOR/AGAINST votes) per voter
    active_votes_count = df_window.count(axis=1)

    # 2. Identify and filter for active voters
    active_voters_index = active_votes_count[active_votes_count >= min_votes].index
    df_filtered = df_window.loc[active_voters_index]

    # 3. Handle remaining scattered NaNs (missing/abstain votes for active voters).
    # kmodes requires integer data, so we fill the NaNs with a unique integer (e.g., 2).
    # This treats the occasional non-vote as a distinct categorical choice,
    # but only for the voters who were active enough to be included.
    df_final = df_filtered.fillna(2).astype(int)

    print(
        f"    -> Window filtered: {len(active_voters_index)} voters remain (out of {len(df_window)} total voters)."
    )
    return df_final, active_voters_index.tolist()


# --- ROLLING WINDOW EXECUTION ---


def run_rolling_window_clustering(voter_proposal_matrix: pd.DataFrame):
    """Executes the rolling window clustering strategy."""

    # Ensure proposals are sorted chronologically if possible (requires Timestamp tracking,
    # but we rely on the order provided by the pivot table which often follows ID order)
    all_proposal_ids = voter_proposal_matrix.columns.tolist()
    num_proposals = len(all_proposal_ids)

    start_index = 0
    window_number = 0
    all_voter_assignments = defaultdict(dict)

    print(f"\n--- Starting Rolling Window Analysis (W={W}, S={S}, k={k}) ---")
    print(
        f"Total Proposals: {num_proposals}. Min votes required per window: {MIN_VOTES_REQUIRED}"
    )

    while start_index + W <= num_proposals:
        window_number += 1
        end_index = start_index + W

        # 1. Define Window and Slice Data
        window_proposal_ids = all_proposal_ids[start_index:end_index]
        df_current_window = voter_proposal_matrix[window_proposal_ids]

        # 2. Exclude Non-Voters and Prepare Data
        df_final_data, active_voters = exclude_non_voters_in_window(
            df_current_window, MIN_VOTES_REQUIRED
        )

        # 3. Apply k-Modes Clustering
        if len(df_final_data) < k:
            print(
                "    -> Not enough active voters to form k clusters. Skipping window."
            )
        else:
            # Use 'Huang' initialization for kmodes
            kmode = KModes(
                n_clusters=k, init="Huang", n_init=5, verbose=0, random_state=42
            )
            clusters = kmode.fit_predict(df_final_data)

            # 4. Store Results
            window_key = f"W{window_number}_P{start_index+1}-P{end_index}"

            # Save assignments for analysis
            for voter, cluster_id in zip(active_voters, clusters):
                all_voter_assignments[voter][window_key] = cluster_id

            # Save the cluster modes for analysis (tracking bloc position)
            modes_df = pd.DataFrame(
                kmode.cluster_centroids_, columns=window_proposal_ids
            )
            modes_df.index = [f"Cluster_{i}_Mode" for i in range(k)]
            modes_df.to_csv(os.path.join(RESULTS_DIR, f"modes_{window_key}.csv"))

            print(f"Completed window {window_number}. Cluster modes saved.")

        # 5. Move the window forward
        start_index += S

    print("--- Rolling Window Analysis Complete ---")

    return all_voter_assignments


# --- MAIN EXECUTION AND ANALYSIS ---


def main():
    try:
        # NOTE: Ensure your CSV is ready and matches the column names provided
        df_raw = pd.read_csv(INPUT_FILENAME)
    except FileNotFoundError:
        print(
            f"Error: Input file '{INPUT_FILENAME}' not found. Ensure the CSV exists in the same directory."
        )
        return
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    # 1. Prepare Data
    voter_proposal_matrix = prepare_data(df_raw)

    # 2. Run Rolling Window Clustering
    voter_assignments = run_rolling_window_clustering(voter_proposal_matrix)

    # 3. Final Output: Voter Trajectory Analysis
    if voter_assignments:
        # Convert dictionary of assignments into a DataFrame
        df_trajectory = pd.DataFrame(voter_assignments).T.sort_index()

        trajectory_filename = os.path.join(
            RESULTS_DIR, "voter_trajectory_assignments.csv"
        )
        df_trajectory.to_csv(trajectory_filename)
        print(f"\nSuccessfully generated voter trajectory file: {trajectory_filename}")

        print("\n--- Next Steps ---")
        print(
            "1. **Cluster Matching:** Compare the 'modes' files using Hamming distance to track the same bloc across windows."
        )
        print(
            "2. **Voter Trajectories:** Analyze 'voter_trajectory_assignments.csv' to find voters whose cluster ID changes over time."
        )

    else:
        print("No clustering results generated.")


if __name__ == "__main__":
    main()
