import requests
import json
import time
import os
from typing import Optional, Dict, Any, List
import pandas as pd  # NEW: For CSV handling and data structuring

# --- CONFIGURATION ---
TALLY_API_KEY = "d560c938af2e7c9db2f9be39a7f64885fd86e459d1383f24a1e68d97a1905ebe"
TALLY_API_ENDPOINT = "https://api.tally.xyz/query"
AAVE_ORG_ID = "2206072049829414624"
PAGE_LIMIT = 100
OUTPUT_FILENAME = "aave_all_voter_records.csv"  # Final aggregated CSV
CSV_FOLDER = "aave_proposal_batches"  # Folder for incremental CSV files
PROPOSALS_PER_BATCH = 100  # Your specified batch size
MAX_RETRIES = 5

# --- GRAPHQL QUERIES (Unchanged) ---
PROPOSALS_QUERY = """
query AllProposalsByOrg($input: ProposalsInput!) {
  proposals(input: $input) {
    nodes {
      ... on Proposal {
        id
        onchainId
        status
        metadata {
          title
        }
      }
    }
    pageInfo {
      lastCursor
    }
  }
}
"""

PROPOSAL_VOTES_QUERY = """
query ProposalTimelineChart($input: ProposalInput!, $votesInput: VotesInput!) {
  proposal(input: $input) {
    id
    onchainId
    createdAt
    status
    metadata {
      title
      description
      discourseURL
    }
    organization {
      slug
    }
    governor {
      quorum
      token {
        decimals
      }
    }
    voteStats {
      votesCount
      votersCount
      type
      percent
    }
  }
  votes(input: $votesInput) {
    nodes {
      ... on OnchainVote {
        voter {
          name
          address
        }
        amount
        type
        block {
          timestamp
        }
      }
    }
    pageInfo {
      count
      lastCursor
    }
  }
}
"""

# --- API HELPER FUNCTION (Unchanged) ---


def execute_graphql_query(
    query: str, variables: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Executes a GraphQL query with retries."""
    headers = {"Content-Type": "application/json", "Api-Key": TALLY_API_KEY}
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                TALLY_API_ENDPOINT, headers=headers, data=json.dumps(payload)
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                print(f"GraphQL Error on attempt {attempt + 1}: {data['errors']}")
                time.sleep(2 ** (attempt + 1))
                continue

            return data

        except requests.exceptions.RequestException as e:
            print(f"HTTP Request Error on attempt {attempt + 1}: {e}")
            time.sleep(2 ** (attempt + 1))
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

    print("Failed to execute query after maximum retries.")
    return None


# --- PHASE 1: COLLECT ALL PROPOSAL IDS (Unchanged) ---


def fetch_all_proposal_ids() -> List[str]:
    """Fetches Tally IDs for all proposals in the Aave DAO."""
    print("--- Phase 1: Collecting all Aave Proposal IDs ---")
    proposal_ids = []
    cursor = None
    total_fetched = 0

    while True:
        variables = {
            "input": {
                "filters": {"organizationId": AAVE_ORG_ID},
                "page": {"limit": PAGE_LIMIT, "afterCursor": cursor},
                "sort": {"sortBy": "id", "isDescending": True},
            }
        }
        result = execute_graphql_query(PROPOSALS_QUERY, variables)

        if not result or "proposals" not in result["data"]:
            print("Failed to fetch proposals list.")
            break

        proposals_data = result["data"]["proposals"]
        nodes = proposals_data.get("nodes", [])

        for proposal in nodes:
            proposal_ids.append(proposal["id"])

        total_fetched += len(nodes)
        print(f"Fetched {len(nodes)} proposals. Total collected: {total_fetched}")

        new_cursor = proposals_data["pageInfo"].get("lastCursor")

        if not new_cursor:
            print("Completed fetching all proposal IDs.")
            break

        cursor = new_cursor
        time.sleep(1)  # Rate limit adherence for pagination

    return proposal_ids


# --- PHASE 2: FETCH FULL DATA AND VOTES (Unchanged) ---


def fetch_full_data_for_proposal(proposal_id: str) -> Optional[Dict[str, Any]]:
    """Fetches full proposal details and all paginated votes for a single proposal."""
    full_votes = []
    cursor = None

    # 1. Fetch the proposal header data and first page of votes
    variables = {
        "input": {"id": proposal_id},
        "votesInput": {
            "filters": {"proposalId": proposal_id, "includePendingVotes": False},
            "sort": {"sortBy": "id", "isDescending": False},
            "page": {"limit": PAGE_LIMIT, "afterCursor": None},
        },
    }
    result = execute_graphql_query(PROPOSAL_VOTES_QUERY, variables)

    if not result or "proposal" not in result["data"]:
        print(f"  -> Skipping Proposal {proposal_id}: Failed to fetch details.")
        return None

    proposal_data = result["data"]["proposal"]
    votes_data = result["data"]["votes"]

    full_votes.extend(votes_data.get("nodes", []))
    cursor = votes_data["pageInfo"].get("lastCursor")

    # 2. Continue fetching subsequent vote pages
    while cursor:
        variables["votesInput"]["page"]["afterCursor"] = cursor
        time.sleep(1)

        vote_page_result = execute_graphql_query(PROPOSAL_VOTES_QUERY, variables)

        if not vote_page_result or "votes" not in vote_page_result["data"]:
            print(
                f"  -> Warning: Failed to fetch votes page for {proposal_id}. Stopping pagination."
            )
            break

        new_votes = vote_page_result["data"]["votes"].get("nodes", [])
        full_votes.extend(new_votes)

        cursor = vote_page_result["data"]["votes"]["pageInfo"].get("lastCursor")

    # Inject relevant data into the votes for easier flat mapping
    proposal_title = proposal_data["metadata"].get("title", "N/A")

    for vote in full_votes:
        vote["proposalId"] = proposal_data["id"]
        vote["onchainId"] = proposal_data["onchainId"]
        vote["proposalTitle"] = proposal_title

    print(f"  -> Fetched {len(full_votes)} votes for Proposal {proposal_id}.")
    return (
        full_votes  # Return the flattened vote list instead of the full proposal object
    )


# --- DATA TRANSFORMATION ---


def data_to_dataframe(vote_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """Converts the list of vote dictionaries into a clean Pandas DataFrame."""
    if not vote_list:
        return pd.DataFrame()

    # Flatten the nested vote structure
    rows = []
    for vote in vote_list:
        row = {
            "Proposal_ID": vote.get("proposalId"),
            "Proposal_Title": vote.get("proposalTitle"),
            "Onchain_ID": vote.get("onchainId"),
            "Voter_Address": vote["voter"].get("address"),
            "Voter_Name": vote["voter"].get("name"),
            "Vote_Type": vote.get("type"),  # e.g., 'FOR', 'AGAINST', 'ABSTAIN'
            "Voting_Power": vote.get("amount"),
            "Timestamp": vote["block"].get("timestamp"),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    return df.set_index("Proposal_ID")


# --- MAIN EXECUTION ---


def main():

    # 0. Setup and state tracking
    if not os.path.exists(CSV_FOLDER):
        os.makedirs(CSV_FOLDER)

    all_tally_ids = fetch_all_proposal_ids()
    if not all_tally_ids:
        print("No proposal IDs were fetched. Exiting.")
        return

    # In-memory buffer to hold votes before writing a batch
    batch_buffer = []

    # 1. Check for previously processed batches
    processed_files = sorted([f for f in os.listdir(CSV_FOLDER) if f.endswith(".csv")])
    total_processed_proposals = len(processed_files) * PROPOSALS_PER_BATCH

    # Check if the last batch file is partially filled (optional, for highly robust resume)
    # For simplicity, we assume batches are written complete or not at all.

    # Find the starting index for new fetching
    start_index = total_processed_proposals

    if start_index >= len(all_tally_ids):
        print(
            f"All {len(all_tally_ids)} proposals have already been fetched and batched. Skipping fetch phase."
        )
        ids_to_fetch = []
    else:
        ids_to_fetch = all_tally_ids[start_index:]
        print(
            f"Resuming fetch from proposal index {start_index}. Remaining to fetch: {len(ids_to_fetch)}."
        )

    # 2. Sequential Fetching Loop with Batch Writing
    print(f"\n--- Phase 2: Fetching {len(ids_to_fetch)} proposals sequentially ---")

    current_batch_index = len(processed_files)  # Starts with the next batch number

    for i, proposal_id in enumerate(ids_to_fetch):

        print(
            f"Processing proposal {start_index + i + 1}/{len(all_tally_ids)} (ID: {proposal_id})..."
        )

        # Fetch the data (returns the flat list of votes)
        # Note: Sleep is inside fetch_full_data_for_proposal for vote pagination
        data = fetch_full_data_for_proposal(proposal_id)

        if data:
            batch_buffer.extend(
                data
            )  # List extension is now limited to memory buffer size

        # Mandatory sleep between proposals for rate limit adherence
        time.sleep(1)

        # Check if buffer is full (every PROPOSALS_PER_BATCH proposals)
        if (i + 1) % PROPOSALS_PER_BATCH == 0 or (i + 1) == len(ids_to_fetch):

            # Write the buffered data to a new CSV file
            batch_df = data_to_dataframe(batch_buffer)
            batch_filename = os.path.join(
                CSV_FOLDER, f"batch_{current_batch_index:03d}.csv"
            )

            if not batch_df.empty:
                # Write the combined votes of the batch to disk
                batch_df.to_csv(batch_filename, index=False)
                print(
                    f"\n*** Saved Batch {current_batch_index} ({len(batch_df)} votes) to {batch_filename} ***\n"
                )
            else:
                print(f"Batch {current_batch_index} was empty. Skipping save.")

            # Reset the buffer and increment the batch index
            batch_buffer = []
            current_batch_index += 1

    # 3. Merge the final results
    print(f"\n--- Phase 3: Merging all CSV batches into {OUTPUT_FILENAME} ---")

    all_files = sorted(
        [
            os.path.join(CSV_FOLDER, f)
            for f in os.listdir(CSV_FOLDER)
            if f.endswith(".csv")
        ]
    )

    if not all_files:
        print("No CSV files found to merge.")
        return

    # Read and concatenate all CSV files
    try:
        df_list = [pd.read_csv(f) for f in all_files]
        final_df = pd.concat(df_list, ignore_index=True)

        # Save the final result
        final_df.to_csv(OUTPUT_FILENAME, index=False)
        print(f"Successfully merged {len(all_files)} batches into {OUTPUT_FILENAME}.")
        print(f"Total rows (individual votes) saved: {len(final_df)}.")

        # Optional: Clean up the temporary directory
        # import shutil
        # shutil.rmtree(CSV_FOLDER)
        # print(f"Cleaned up temporary directory: {CSV_FOLDER}")

    except Exception as e:
        print(f"ERROR during merging: {e}")


if __name__ == "__main__":
    main()
