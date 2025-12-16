import pandas as pd
from typing import List, Tuple
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori

# New import for Sequential Pattern Mining
from prefixspan import PrefixSpan

# --- CONFIGURATION ---
INPUT_CSV_FILENAME = "./tally-proposals/aave_vote_timeline.csv"
# The minimum support threshold is now applied to sequences.
# Example: Look for sequences present in at least 20% of the entire sequence history
MIN_SUPPORT_THRESHOLD_CO_VOTE = 0.5  # For Apriori
MIN_SUPPORT_THRESHOLD_SEQUENTIAL = 0.2  # For PrefixSpan (Often lower than Apriori)
MAX_PATTERN_LENGTH = 10


def load_and_preprocess_data(file_path: str) -> pd.DataFrame:
    """Loads the sorted vote data and ensures correct types."""
    try:
        df = pd.read_csv(file_path)
        # Ensure data is sorted by proposal ID and then by vote timestamp (Crucial for sequential mining)
        df = df.sort_values(by=["proposal_id_tally", "vote_timestamp_str"])
        df["vote_timestamp"] = pd.to_datetime(df["vote_timestamp_str"], utc=True)
        return df
    except FileNotFoundError:
        print(
            f"Error: Input CSV file '{file_path}' not found. "
            "Please ensure you run the data collection/analysis step first to create this file."
        )
        return pd.DataFrame()


# --- DATA PREP 1: For Apriori (Co-Voting) ---


def prepare_for_apriori(df: pd.DataFrame) -> Tuple[List[List[str]], List[str]]:
    """
    Transforms the vote timeline into the transaction format required by Apriori.
    Transaction (basket) = All unique voters on a single proposal.
    """
    # Create an item for each voter combining address and vote type
    df["item"] = df["voter_address"] + "_" + df["vote_type"]
    transactions = df.groupby("proposal_id_tally")["item"].unique().tolist()
    all_unique_items = list(set(df["item"]))
    return transactions, all_unique_items


# --- DATA PREP 2: For PrefixSpan (Sequential Mining) ---


def prepare_for_prefixspan(df: pd.DataFrame) -> List[List[List[str]]]:
    """
    Transforms the vote timeline into the sequential format required by PrefixSpan.
    Sequence = The list of proposals (chronological order)
    Transaction (Element in Sequence) = All unique voter/vote items on a proposal.
    """
    df_sorted = df.sort_values(by=["vote_timestamp"])

    # Group by proposal ID to get the set of items (voter_address_vote_type) for each proposal
    proposal_transactions = df_sorted.groupby("proposal_id_tally")["item"].unique()

    # Create the single, chronological sequence of transactions (one transaction per proposal)
    sequence = proposal_transactions.tolist()

    # PrefixSpan requires the data to be in the format: List[Sequence], where Sequence is List[Transaction].
    # In this case, we treat the entire history of proposals as one long sequence.
    # The structure required by prefixspan is technically List[List[str]] if the inner lists are transactions.
    # For many SPM packages, a sequence is List[Transaction] where Transaction is List[Item].
    # The 'prefixspan' library expects List[Transaction] where Transaction is List[Item].
    # So we return the `sequence` directly: List[List[str]]
    return sequence


def perform_frequent_itemset_mining(transactions: List[List[str]]) -> pd.DataFrame:
    """
    Applies the Apriori algorithm to find frequently co-occurring voters/votes.
    """
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

    frequent_itemsets = apriori(
        df_encoded,
        min_support=MIN_SUPPORT_THRESHOLD_CO_VOTE,
        use_colnames=True,
        max_len=MAX_PATTERN_LENGTH,
    )

    frequent_itemsets["pattern_size"] = frequent_itemsets["itemsets"].apply(
        lambda x: len(x)
    )
    return frequent_itemsets.sort_values(by="support", ascending=False)


def perform_sequential_pattern_mining(sequences: List[List[str]]) -> pd.DataFrame:
    """
    Applies the PrefixSpan algorithm to find frequent sequences of votes across proposals.

    The sequence is ordered by proposal chronology.
    """
    # Initialize PrefixSpan with the sequence data
    ps = PrefixSpan(sequences)

    # min_support is passed as an absolute count, so we calculate the minimum count
    min_count = int(MIN_SUPPORT_THRESHOLD_SEQUENTIAL * len(sequences))

    # Run the mining algorithm
    # The result is a list of tuples: (support_count, pattern_sequence)
    frequent_sequences = ps.frequent(min_count)

    # Convert results to DataFrame
    df_sequences = pd.DataFrame(frequent_sequences, columns=["count", "sequence"])
    df_sequences["support"] = df_sequences["count"] / len(sequences)

    # sequences returned are nested lists (list of transactions)
    df_sequences["pattern_size"] = df_sequences["sequence"].apply(lambda x: len(x))

    return df_sequences.sort_values(by="support", ascending=False)


def main():
    # Load and preprocess the chronological vote data
    df = load_and_preprocess_data(INPUT_CSV_FILENAME)

    if df.empty:
        return

    # Create the combined 'item' column used by both miners
    df["item"] = df["voter_address"] + "_" + df["vote_type"]

    # --- 1. Sequential Pattern Mining (PrefixSpan) ---
    sequences = prepare_for_prefixspan(df)
    print(f"Total Proposals in Sequence: {len(sequences)}")

    print(
        f"\n--- Starting Sequential Pattern Mining (Min Support: {MIN_SUPPORT_THRESHOLD_SEQUENTIAL}) ---"
    )
    sequential_patterns_df = perform_sequential_pattern_mining(sequences)

    print("\n--- Top Sequential Patterns Across Proposals ---")
    print(
        "Interpretation: Proposal 1 contained (Pattern A), followed by Proposal 2 containing (Pattern B, C)."
    )
    print(
        "Format: Sequence is a list of transactions. Transaction is a list of items on that proposal."
    )
    print("Item Format: [Voter Address]_[Vote Type]")

    results_to_display_seq = sequential_patterns_df[
        sequential_patterns_df["pattern_size"] > 1
    ]

    if results_to_display_seq.empty:
        print("\nNo sequential patterns found above the set minimum support threshold.")
    else:
        print(
            results_to_display_seq[["support", "pattern_size", "sequence"]]
            .head(100)
            .to_markdown(index=False)
        )
        print("\nNote: Sequences are lists of transactions (proposals).")

    print("\n" + "=" * 80 + "\n")

    # --- 2. Frequent Itemset Mining (Apriori) - Original Logic ---
    transactions, _ = prepare_for_apriori(df)

    print(
        f"\n--- Starting Frequent Co-Voting Mining (Min Support: {MIN_SUPPORT_THRESHOLD_CO_VOTE}) ---"
    )
    frequent_patterns_df = perform_frequent_itemset_mining(transactions)

    print("\n--- Top Co-Voting Patterns (Itemsets) Across Proposals ---")
    print(
        "Interpretation: These groups of voters consistently voted on the same single proposal."
    )

    results_to_display_apriori = frequent_patterns_df[
        frequent_patterns_df["pattern_size"] > 1
    ]

    if results_to_display_apriori.empty:
        print("\nNo co-voting patterns found above the set minimum support threshold.")
    else:
        print(
            results_to_display_apriori[["support", "pattern_size", "itemsets"]]
            .head(10)
            .to_markdown(index=False)
        )


if __name__ == "__main__":
    main()
