import json
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

# --- CONFIGURATION ---
INPUT_FILENAME = "aave_proposals_data.json"
OUTPUT_CSV_FILENAME = "./tally-proposals/aave_vote_timeline.csv"


def load_data(file_path: str) -> List[Dict[str, Any]]:
    """Loads the JSON data from the file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{file_path}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{file_path}'.")
        return []


def detokenize_amount(amount_str: str, decimals: int) -> float:
    """Converts the large integer token amount (Uint256 string) to a human-readable float."""
    try:
        amount_int = int(amount_str)
        return amount_int / (10**decimals)
    except ValueError:
        return 0.0


def transform_to_dataframe(proposals_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Transforms the nested list of proposals and votes into a flat DataFrame.

    Each row in the final DataFrame represents a single vote event.
    """
    all_vote_records = []

    for proposal in proposals_data:
        proposal_id = proposal.get("id")
        onchain_id = proposal.get("onchainId")
        proposal_title = proposal.get("metadata", {}).get("title", "N/A")
        proposal_status = proposal.get("status")
        proposal_created_at = proposal.get("createdAt")

        # Determine the token decimals, typically 18 for AAVE/stkAAVE
        decimals = proposal.get("governor", {}).get("token", {}).get("decimals", 18)

        # Iterate through the nested list of individual votes
        for vote in proposal.get("fullVotesTimeline", []):
            voter_info = vote.get("voter", {})
            block_info = vote.get("block", {})

            # Prepare the vote record
            record = {
                "proposal_id_tally": proposal_id,
                "proposal_id_onchain": onchain_id,
                "proposal_title": proposal_title,
                "proposal_status": proposal_status,
                "proposal_created_at": proposal_created_at,
                "voter_address": voter_info.get("address"),
                "voter_name": voter_info.get("name", "Anon"),
                "vote_type": vote.get("type"),  # 'for', 'against', 'abstain'
                # Convert vote amount from raw string (Uint256) to human-readable float
                "vote_amount_raw": vote.get("amount"),
                "vote_amount_aave": detokenize_amount(
                    vote.get("amount", "0"), decimals
                ),
                "vote_timestamp_str": block_info.get("timestamp"),
            }
            all_vote_records.append(record)

    df = pd.DataFrame(all_vote_records)

    # --- Final Processing and Sorting for Pattern Mining ---

    # Convert timestamp string to datetime object
    df["vote_timestamp"] = pd.to_datetime(df["vote_timestamp_str"], utc=True)

    # Sort by timestamp to ensure chronological order for time-series/pattern analysis
    df = df.sort_values(by=["vote_timestamp", "proposal_id_tally"]).reset_index(
        drop=True
    )

    return df


def main():
    proposals_data = load_data(INPUT_FILENAME)

    if not proposals_data:
        print("Exiting due to data loading error.")
        return

    df = transform_to_dataframe(proposals_data)

    # Display the first few rows and summary statistics
    print("\n--- Data Transformation Successful ---")
    print(f"Total Vote Records Extracted: {len(df)}")
    print(df.head())

    # Save the final, sorted DataFrame to a CSV file
    df.to_csv(OUTPUT_CSV_FILENAME, index=False)
    print(f"\n--- Data saved to '{OUTPUT_CSV_FILENAME}' ---")
    print(
        "DataFrame is chronologically sorted by 'vote_timestamp', ready for pattern mining."
    )


if __name__ == "__main__":
    # Ensure pandas is installed: pip install pandas
    main()
