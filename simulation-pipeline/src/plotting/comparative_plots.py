import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import random
import matplotlib.colors
import numpy as np

# --- Global Style Definitions ---
MODEL_STYLES = {
    "Direct": {"color": "black", "linestyle": "--", "marker": "x", "zorder": 10},
    "Optimal": {"color": "C0", "linestyle": "-", "marker": "o", "zorder": 5},
    "Frozen": {"color": "C1", "linestyle": "-", "marker": "s", "zorder": 5},
    "Probabilistic": {"color": "C2", "linestyle": "-", "marker": "^", "zorder": 5},
}

# --- Plot Function 1: Wprime Share Comparison ---


def load_data_for_comparison(config):
    """Helper to load all DRep results for comparative plotting."""
    data = {}
    files_to_load = {
        "optimal": config.DREPS_OPTIMAL_FILE,
        "frozen": config.DREPS_FROZEN_FILE,
        "probabilistic": config.DREPS_PROBABILISTIC_FILE,
    }

    for model_name, file_path in files_to_load.items():
        try:
            data[model_name] = pd.read_csv(file_path)
        except FileNotFoundError:
            print(
                f"  - ⚠️ Warning: Could not find file {file_path.name}. Skipping for comparison plots."
            )

    if not data:
        print(
            f"  - ❌ Error: No analysis data found in {config.DATA_DIR_ANALYSIS} for comparison."
        )
        return None

    return data


def plot_wprime_share(config, data):
    """Plot: Wprime share of top 5 DReps over time, compared across models."""
    print("  Generating plot: Wprime Share Comparison")

    num_models = len(data)
    if num_models == 0:
        return

    fig, axes = plt.subplots(1, num_models, figsize=(7 * num_models, 6), sharey=True)
    if num_models == 1:
        axes = [axes]  # Make it iterable

    fig.suptitle("Wprime Share of Top 5 DReps Over Time (by Model)", fontsize=16)

    for ax, (model_name, df) in zip(axes, data.items()):

        if 0 not in df["epoch"].values:
            print(f"  - ⚠️ Skipping plot for {model_name}: no epoch 0 data.")
            continue

        top5 = df[df["epoch"] == 0].nlargest(5, "Wprime")["drep_id"]
        plot_data = df[df["drep_id"].isin(top5)]

        for drep_id in top5:
            drep_data = plot_data[plot_data["drep_id"] == drep_id]
            ax.plot(
                drep_data["epoch"],
                drep_data["Wprime_share"],
                label=drep_id,
                marker="o",
                markersize=4,
            )

        ax.set_title(model_name.capitalize())
        ax.set_xlabel("Epoch")
        if ax == axes[0]:
            ax.set_ylabel("Wprime Share")
        ax.legend(loc="upper left")
        ax.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    save_path = config.PLOT_DIR / "wprime_share_comparison.png"
    plt.savefig(save_path)
    print(f"  Saved plot: {save_path.name}")
    plt.close(fig)


# --- Helper for Weighted Median ---
def calculate_weighted_median(values, weights):
    """Calculate the weighted median of a series of values."""
    if weights.sum() == 0:
        return 0.5  # Default to 0.5 if no weights

    # Sort values and weights
    i = np.argsort(values)
    values_sorted = values.iloc[i]
    weights_sorted = weights.iloc[i]

    # Calculate cumulative weight sum
    cum_weights = np.cumsum(weights_sorted)
    total_weight = cum_weights.iloc[-1]

    # Find the index where cumulative weight crosses 50%
    median_idx = np.searchsorted(cum_weights, total_weight / 2.0)

    # Handle potential edge cases
    if median_idx >= len(values_sorted):
        median_idx = len(values_sorted) - 1

    return values_sorted.iloc[median_idx]


# --- Plot Function: W' Stake Distribution Histogram ---


def plot_wprime_histograms(config, data):
    """
    Plot: W' stake distribution (weighted histogram) by opinion
    for epochs 0, 5, and 10.
    """
    print("  Generating plot: W' Stake Distribution Histograms")

    epochs_to_plot = [i for i in range(11)]
    num_bins = 50  # Bins for the 0-1 opinion range
    bin_range = (0, 1)

    # --- Iterate over each model ---
    for model_name, df in data.items():

        # Create a figure with 3 subplots (one for each epoch)
        fig, axes = plt.subplots(
            len(epochs_to_plot), 1, figsize=(10, 4 * len(epochs_to_plot)), squeeze=False
        )

        fig.suptitle(
            f"W' Stake Distribution by Opinion ({'Responsive' if model_name == 'optimal' else model_name.capitalize()})",
            fontsize=16,
        )

        # --- Iterate over each epoch for this model ---
        for i, epoch in enumerate(epochs_to_plot):
            ax = axes[i, 0]

            # Filter data for the specific epoch
            epoch_data = df[df["epoch"] == epoch]

            # Check if there is data to plot
            if epoch_data.empty or epoch_data["Wprime"].sum() == 0:
                ax.text(
                    0.5,
                    0.5,
                    f"No data for epoch {epoch}",
                    horizontalalignment="center",
                    verticalalignment="center",
                    transform=ax.transAxes,
                    fontsize=12,
                    color="gray",
                )
                ax.set_title(f"Epoch {epoch}")
                ax.set_xlim(0, 1)
                continue

            # --- Data exists, proceed with plotting ---
            opinions = epoch_data["opinion"].astype(float)
            weights = epoch_data["Wprime"].astype(float)

            # 1. Calculate the histogram
            # hist = sum of W' in each bin
            # bin_edges = the edges of the bins
            hist, bin_edges = np.histogram(
                opinions, bins=num_bins, range=bin_range, weights=weights
            )

            # 2. Calculate the W'-weighted median opinion
            median_op = calculate_weighted_median(opinions, weights)

            # 3. Plot the histogram bars
            bin_width = bin_edges[1] - bin_edges[0]
            ax.bar(
                bin_edges[:-1],
                hist,
                width=bin_width,
                align="edge",
                alpha=0.75,
                label="W' Stake",
                color=MODEL_STYLES.get(model_name.capitalize(), {}).get("color", "C0"),
            )

            # 4. Plot the weighted median line (Option B)
            ax.axvline(
                median_op,
                color="red",
                linestyle="--",
                linewidth=2,
                label=f"W' Weighted Median ({median_op:.3f})",
            )

            # 5. Style the plot
            ax.set_title(f"Epoch {epoch}")
            ax.set_xlabel("Opinion Bins [0, 1]")
            ax.set_ylabel("Sum of W' Stake")
            ax.set_xlim(0, 1)
            ax.legend(loc="upper right")
            ax.grid(True, alpha=0.3, linestyle=":")

        # Save the figure for the current model
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        save_name = model_name.replace("optimal", "responsive")
        save_path = config.PLOT_DIR / f"wprime_histogram_{save_name}.png"

        plt.savefig(save_path)
        print(f"  Saved plot: {save_path.name}")
        plt.close(fig)


# --- Plot Function 2: Per-Epoch Plots ---
def plot_median_comparison(config, data):
    """
    Plot: The trajectory of the W'-weighted median opinion over all epochs,
    comparing all models on one chart.
    """
    print("  Generating plot: Weighted Median Opinion Comparison")

    fig, ax = plt.subplots(figsize=(10, 6))

    # Iterate through each model (Optimal, Frozen, Probabilistic)
    for model_name, df in data.items():

        # 1. Identify epochs and calculate medians
        # Sort epochs to ensure the line is drawn correctly
        epochs = sorted(df["epoch"].unique())
        medians = []

        for epoch in epochs:
            epoch_data = df[df["epoch"] == epoch]

            # Calculate the weighted median using your helper function
            # (Assumes calculate_weighted_median is defined in your scope)
            if epoch_data.empty:
                med = 0.5  # Fallback
            else:
                med = calculate_weighted_median(
                    epoch_data["opinion"], epoch_data["Wprime"]
                )
            medians.append(med)

        # 2. Determine style and label
        # Handle the name change: optimal -> Responsive for the legend
        label_name = (
            "Responsive" if model_name.lower() == "optimal" else model_name.capitalize()
        )

        # Get style from your global MODEL_STYLES dict
        # Note: keys in MODEL_STYLES are usually Capitalized ("Optimal", "Frozen", etc.)
        style_key = (
            "Optimal" if model_name.lower() == "optimal" else model_name.capitalize()
        )
        style = MODEL_STYLES.get(style_key, {})

        # 3. Plot the line
        ax.plot(
            epochs,
            medians,
            label=label_name,
            color=style.get("color", None),
            linestyle=style.get("linestyle", "-"),
            marker=style.get("marker", None),
            markersize=4,
            alpha=0.9,
        )

    # 4. Finalize the plot
    ax.set_title("Weighted Median Opinion Over Time")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Weighted Median Opinion (0 to 1)")
    ax.set_ylim(0, 1)
    ax.axhline(0.5, color="gray", linestyle=":", alpha=0.5, label="Center (0.5)")

    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # 5. Save
    save_path = config.PLOT_DIR / "weighted_median_comparison.png"
    plt.savefig(save_path)
    print(f"  Saved plot: {save_path.name}")
    plt.close(fig)


def load_source_frames(config, source: str):
    """Loads delegator (ddf) and drep (rdf) frames for a given source."""
    if source == "optimal":
        d_path = config.DELEGATORS_OPTIMAL_FILE
        r_path = config.DREPS_OPTIMAL_FILE
    elif source == "probabilistic":
        d_path = config.DELEGATIONS_PROBABILISTIC_FILE
        r_path = config.DREPS_PROBABILISTIC_FILE
    elif source == "frozen":
        d_path = config.DELEGATORS_FROZEN_FILE
        r_path = config.DREPS_FROZEN_FILE
    else:
        raise ValueError(f"Unknown source: {source}")

    if not d_path.exists() or not r_path.exists():
        return None, None, None

    ddf = pd.read_csv(d_path)
    rdf = pd.read_csv(r_path)
    eps = sorted(set(ddf["epoch"]).intersection(set(rdf["epoch"])))
    return ddf, rdf, eps


def ensure_probabilistic_columns(config, A: pd.DataFrame) -> pd.DataFrame:
    """Ensure probabilistic delegations have opinion/stake/s (merge from minimal CSVs if needed)."""
    if (
        ("opinion" not in A.columns)
        or ("stake" not in A.columns)
        or ("s" not in A.columns)
        or ("drep_opinion" not in A.columns)
    ):
        try:
            base_deleg = pd.read_csv(config.DELEGATORS_STATE_FILE)
            base_dreps = pd.read_csv(config.DREPS_STATE_FILE)
        except FileNotFoundError:
            print("  - ❌ ERROR: Could not find raw data files from simulation step.")
            print("  - Please run --simulate first.")
            return pd.DataFrame(
                columns=A.columns.tolist()
                + ["opinion", "stake", "s", "drep_opinion", "switched"]
            )

        A = A.merge(
            base_deleg[["epoch", "delegator_id", "opinion", "stake", "s"]],
            on=["epoch", "delegator_id"],
            how="left",
        )
        A = A.merge(
            base_dreps[["epoch", "drep_id", "opinion"]].rename(
                columns={"opinion": "drep_opinion"}
            ),
            on=["epoch", "drep_id"],
            how="left",
        )
    if "switched" not in A.columns:
        A["switched"] = 0
    return A


def plot_epoch_from_csv_unified(
    config,
    epoch: int,
    deleg_df: pd.DataFrame,
    dreps_df: pd.DataFrame,
    source: str = "optimal",
    use_stake_size: bool = True,
    size_scale_deleg: float = 20.0,
    size_scale_dreps: float = 20.0,
    jitter: float = 0.02,
    draw_edges: bool = True,
    edge_alpha: float = 0.25,
    edge_lw: float = 0.6,
    edge_samples: int | None = None,
    edge_random_seed: int | None = 123,
    color_switched: bool = True,
):
    D_all = dreps_df[dreps_df["epoch"] == epoch].copy()
    A = deleg_df[deleg_df["epoch"] == epoch].copy()
    if D_all.empty or A.empty:
        print(f"  - [skip] No data for epoch {epoch} in source '{source}'.")
        return None, None

    if source == "probabilistic":
        A = ensure_probabilistic_columns(config, A)
    else:
        if "switched" not in A.columns:
            A["switched"] = 0

    if A.empty or A["opinion"].isnull().all():
        print(
            f"  - [skip] Data missing after harmonization for epoch {epoch} in source '{source}'."
        )
        return None, None

    # --- NEW: Split DReps into Target and Others ---
    target_id = getattr(config, "TARGET_DREP_ID", None)

    D_target = D_all[D_all["drep_id"] == target_id] if target_id else D_all.iloc[0:0]
    D_others = D_all[D_all["drep_id"] != target_id] if target_id else D_all

    # --- X positions
    x_deleg = A["opinion"].astype(float).to_list()
    x_dreps_others = D_others["opinion"].astype(float).to_list()
    x_dreps_target = D_target["opinion"].astype(float).to_list()

    # --- Y rows + jitter
    y_row_deleg = 0.35
    y_row_dreps = 0.65
    y_deleg = [
        y_row_deleg + (random.uniform(-jitter, jitter) if jitter > 0 else 0.0)
        for _ in x_deleg
    ]
    y_dreps_others = [
        y_row_dreps + (random.uniform(-jitter, jitter) if jitter > 0 else 0.0)
        for _ in x_dreps_others
    ]
    y_dreps_target = [
        y_row_dreps + (random.uniform(-jitter, jitter) if jitter > 0 else 0.0)
        for _ in x_dreps_target
    ]

    # --- Sizes
    if use_stake_size:
        s_deleg = [max(10.0, float(s) * size_scale_deleg) for s in A["stake"]]

        size_source_others = (
            D_others["Wprime"] if "Wprime" in D_others.columns else D_others["stake"]
        )
        s_dreps_others = [
            max(10.0, float(s) * size_scale_dreps) for s in size_source_others
        ]

        size_source_target = (
            D_target["Wprime"] if "Wprime" in D_target.columns else D_target["stake"]
        )
        s_dreps_target = [
            max(10.0, float(s) * size_scale_dreps) for s in size_source_target
        ]
    else:
        s_deleg = [25.0] * len(x_deleg)
        s_dreps_others = [40.0] * len(x_dreps_others)
        s_dreps_target = [60.0] * len(x_dreps_target)  # Make target slightly bigger

    # --- DRep positions for edges (must include all)
    drep_pos = {
        d: (x, y)
        for d, x, y in zip(
            D_others["drep_id"].astype(str), x_dreps_others, y_dreps_others
        )
    }
    drep_pos.update(
        {
            d: (x, y)
            for d, x, y in zip(
                D_target["drep_id"].astype(str), x_dreps_target, y_dreps_target
            )
        }
    )

    # --- Plot
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0.2, 0.8)
    ax.hlines(0.5, 0.0, 1.0, linestyles="dashed", linewidth=0.8)

    # Edges
    if draw_edges:
        idxs = list(A.index)
        if edge_samples is not None and edge_samples < len(idxs):
            _rng = random.Random(edge_random_seed)
            idxs = _rng.sample(idxs, edge_samples)

        pos_map = {idx: pos for pos, idx in enumerate(A.index)}
        for i in idxs:
            a = A.loc[i]
            x1 = float(a["opinion"])
            y1 = y_deleg[pos_map[i]]
            drid = str(a["drep_id"])
            x2, y2 = drep_pos.get(drid, (None, None))
            if x2 is None:
                continue

            if (source in ["probabilistic", "optimal"]) and color_switched:
                switched_val = a.get("switched", 0)
                if pd.isna(switched_val):
                    switched_val = 0

                col = "C3" if int(switched_val) == 1 else "0.4"
                alp = 0.55 if int(switched_val) == 1 else edge_alpha
            else:
                col = "0.35"
                alp = edge_alpha

            ax.plot([x1, x2], [y1, y2], linewidth=edge_lw, alpha=alp, color=col)

    # --- NEW: Split scatter plot
    ax.scatter(x_deleg, y_deleg, s=s_deleg, alpha=0.6, marker="o", label="Delegators")
    ax.scatter(
        x_dreps_others,
        y_dreps_others,
        s=s_dreps_others,
        alpha=0.9,
        marker="s",
        label="DReps",
        color="C0",
    )

    if not D_target.empty:
        ax.scatter(
            x_dreps_target,
            y_dreps_target,
            s=s_dreps_target,
            alpha=1.0,
            marker="D",
            label=f"Target DRep ({target_id})",
            color="red",
            zorder=10,
            edgecolors="black",
            linewidth=0.5,
        )

    # Labels
    ax.set_xlabel("Opinion in [0, 1]")
    ax.set_yticks([y_row_deleg, 0.5, y_row_dreps], labels=["Delegators", "", "DReps"])
    ax.set_title(
        f"Opinions & delegations (epoch {epoch}, {"responsive" if source =="optimal" else source})"
    )
    ax.legend(loc="upper center", ncol=3, frameon=False)  # Changed to 3 columns
    fig.tight_layout()
    return fig, ax


def generate_epoch_plots(config):
    """
    Generates one plot per epoch for each specified model.
    """
    print("  Generating per-epoch plots...")

    ALL_SOURCES = ["optimal", "probabilistic", "frozen"]

    for src in ALL_SOURCES:
        ddf, rdf, eps = load_source_frames(config, src)
        if ddf is None:
            print(
                f"  - [skip] Source '{src}' missing expected CSVs. Skipping per-epoch plots."
            )
            continue

        print(f"  - Processing source: '{src}'")

        out_dir = config.PLOT_DIR / f"epoch_plots_{src}"
        out_dir.mkdir(parents=True, exist_ok=True)

        epochs_processed = 0
        for e in eps:
            fig, ax = plot_epoch_from_csv_unified(
                config,
                int(e),
                ddf,
                rdf,
                source=src,
                use_stake_size=config.USE_STAKE_SIZE,
                size_scale_deleg=config.SIZE_SCALE_DELEG,
                size_scale_dreps=config.SIZE_SCALE_DREPS,
                jitter=config.JITTER,
                draw_edges=config.DRAW_EDGES,
                edge_alpha=config.EDGE_ALPHA,
                edge_lw=config.EDGE_LW,
                edge_samples=config.EDGE_SAMPLES,
                color_switched=config.COLOR_SWITCHED,
            )

            if fig is None:
                continue

            save_path = out_dir / f"epoch_{int(e):04d}.png"
            fig.savefig(save_path, dpi=160, bbox_inches="tight")
            plt.close(fig)
            epochs_processed += 1

        if epochs_processed > 0:
            print(f"  - Saved {epochs_processed} plots to {out_dir.name}/")
        else:
            print(f"  - No plots generated for {src} (data may be missing).")


# --- Plot Functions 3, 4, 5: Proposal Vote Analysis ---


def add_for_percentage(df):
    """Returns a new DataFrame with a 'for_pct' column."""
    df_new = df.copy()

    if "for_stake" not in df_new.columns or "against_stake" not in df_new.columns:
        print(
            "  - ⚠️ Warning: 'for_stake' or 'against_stake' not in proposal data. Cannot calculate percentage."
        )
        df_new["for_pct"] = 0.0
        return df_new

    total_stake = df_new["for_stake"] + df_new["against_stake"]

    df_new["for_pct"] = np.where(
        total_stake == 0, 0, (df_new["for_stake"] / total_stake) * 100
    )
    return df_new


def load_all_proposal_data(config):
    """Loads and processes all 4 proposal CSVs into one DataFrame."""
    files_to_load = {
        "Direct": config.PROPOSAL_OUT_DIRECT,
        "Frozen": config.PROPOSAL_OUT_FROZEN,
        "Optimal": config.PROPOSAL_OUT_OPTIMAL,
        "Probabilistic": config.PROPOSAL_OUT_PROBABILISTIC,
    }

    all_dfs = []
    for model_name, path in files_to_load.items():
        try:
            df = pd.read_csv(path)
            df = add_for_percentage(df)  # Calculate 'for_pct'
            df["model"] = model_name
            all_dfs.append(df)
        except FileNotFoundError:
            print(
                f"  - ⚠️ Warning: Cannot find {path.name}. Skipping '{model_name}' for proposal plots."
            )

    if not all_dfs:
        print("  - ❌ Error: No proposal data found. Skipping proposal plots.")
        return None

    return pd.concat(all_dfs, ignore_index=True)


def get_proposal_labels(all_data):
    """Helper to create a mapping of {prop_id: "label [0.1, 0.3]"}."""
    all_proposals = {}
    if not all_data.empty and "proposal_id" in all_data.columns:
        # Create a unique label for each proposal
        data_with_labels = all_data.drop_duplicates(subset=["proposal_id"])
        for _, row in data_with_labels.iterrows():
            # Format to 2 decimal places: [0.05, 0.45]
            label = f"[{row.get('prop_range_min', 0):.2f}, {row.get('prop_range_max', 1):.2f}]"
            all_proposals[row["proposal_id"]] = label
    return all_proposals


def generate_proposal_comparison_plot(config, all_data):
    """
    Generates one plot per proposal, comparing all models' 'FOR %'
    against the Direct Voting baseline.
    """
    print("  Generating plot: 'FOR %' Comparison (All Models)")

    all_proposals = get_proposal_labels(all_data)
    if not all_proposals:
        print("  - [skip] No proposal data found for comparison plot.")
        return

    num_proposals = len(all_proposals)
    fig, axes = plt.subplots(
        num_proposals, 1, figsize=(10, 5 * num_proposals), squeeze=False
    )
    fig.suptitle("Proposal 'FOR' %: Direct vs. Delegated Voting", fontsize=16, y=0.99)

    for i, (prop_id, prop_label) in enumerate(all_proposals.items()):
        ax = axes[i, 0]

        for model_name in ["Direct", "Optimal", "Frozen", "Probabilistic"]:
            model_df = all_data[
                (all_data["model"] == model_name) & (all_data["proposal_id"] == prop_id)
            ]
            if model_df.empty:
                continue

            style = MODEL_STYLES.get(model_name)
            ax.plot(
                model_df["epoch"],
                model_df["for_pct"],
                label="responsive" if model_name.lower() == "optimal" else model_name,
                color=style.get("color"),
                linestyle=style.get("linestyle"),
                marker=style.get("marker"),
                zorder=style.get("zorder"),
                markersize=4,
            )

        ax.axhline(
            config.PASS_THRESHOLD,
            color="red",
            linestyle=":",
            linewidth=1.2,
            label=f"{config.PASS_THRESHOLD}% Pass Threshold",
        )
        ax.set_title(f"Proposal: {prop_id} {prop_label}")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Stake 'FOR' (%)")
        ax.set_ylim(-2, 102)  # Give 2% margin
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    save_path = config.PLOT_DIR / "for_percentage_comparison.png"
    plt.savefig(save_path)
    print(f"  Saved plot: {save_path.name}")
    plt.close(fig)


def generate_difference_plot(config, all_data):
    """
    Plots the *difference* between delegation models and direct voting.
    """
    print("  Generating plot: Delegation vs. Direct (Difference)")

    direct_data = all_data[all_data["model"] == "Direct"][
        ["epoch", "proposal_id", "for_pct"]
    ]
    if direct_data.empty:
        print(
            "  - [skip] No 'Direct' voting data to compare against. Skipping difference plot."
        )
        return

    delegation_data = all_data[all_data["model"] != "Direct"]
    if delegation_data.empty:
        print("  - [skip] No delegation voting data. Skipping difference plot.")
        return

    plot_data = delegation_data.merge(
        direct_data, on=["epoch", "proposal_id"], suffixes=("_deleg", "_direct")
    )
    plot_data["pct_difference"] = (
        plot_data["for_pct_deleg"] - plot_data["for_pct_direct"]
    )

    all_proposals = get_proposal_labels(all_data)
    proposals = sorted(plot_data["proposal_id"].unique())
    num_proposals = len(proposals)

    if num_proposals == 0:
        return

    fig, axes = plt.subplots(
        num_proposals, 1, figsize=(10, 4 * num_proposals), squeeze=False
    )
    fig.suptitle(
        "Difference from Direct Vote (Delegation 'FOR' % - Direct 'FOR' %)",
        fontsize=16,
        y=0.99,
    )

    for i, prop_id in enumerate(proposals):
        ax = axes[i, 0]
        prop_df = plot_data[plot_data["proposal_id"] == prop_id]

        for model_name in ["Optimal", "Frozen", "Probabilistic"]:
            model_df = prop_df[prop_df["model"] == model_name]
            if not model_df.empty:
                style = MODEL_STYLES[model_name]
                ax.plot(
                    model_df["epoch"],
                    model_df["pct_difference"],
                    label=(
                        "responsive" if model_name.lower() == "optimal" else model_name
                    ),
                    color=style["color"],
                    linestyle=style["linestyle"],
                    marker=style["marker"],
                    markersize=4,
                )

        ax.axhline(
            0,
            color="black",
            linestyle="--",
            linewidth=1.0,
            label="Direct Vote Baseline",
        )
        prop_label = all_proposals.get(prop_id, "")
        ax.set_title(f"Proposal: {prop_id} {prop_label}")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Difference in 'FOR' %")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    save_path = config.PLOT_DIR / "difference_from_direct.png"
    plt.savefig(save_path)
    print(f"  Saved plot: {save_path.name}")
    plt.close(fig)


def generate_pass_rate_barchart(config, all_data):
    """
    Bar chart of the percentage of epochs where each proposal passed.
    """
    print("  Generating plot: Epoch Pass Rate Bar Chart")

    # 1. Calculate pass/fail for each epoch (using config)
    all_data["passed"] = all_data["for_pct"] > config.PASS_THRESHOLD

    # 2. Get total number of epochs for each group
    total_epochs = all_data.groupby(["model", "proposal_id"])["epoch"].nunique()

    # 3. Get total *passed* epochs
    passed_epochs = (
        all_data[all_data["passed"] == True]
        .groupby(["model", "proposal_id"])["epoch"]
        .nunique()
    )

    # 4. Combine and calculate percentage
    summary = (passed_epochs.div(total_epochs, fill_value=0) * 100).reset_index(
        name="pass_rate_pct"
    )

    all_proposals = get_proposal_labels(all_data)
    proposals = sorted(summary["proposal_id"].unique())
    models = ["Direct", "Frozen", "Optimal", "Probabilistic"]  # For consistent order
    num_proposals = len(proposals)

    if num_proposals == 0:
        print("  - [skip] No data for pass rate bar chart.")
        return

    fig, axes = plt.subplots(
        1, num_proposals, figsize=(6 * num_proposals, 5), squeeze=False
    )
    fig.suptitle(
        f"% of Epochs Passed ('FOR' % > {config.PASS_THRESHOLD}%)", fontsize=16
    )

    for i, prop_id in enumerate(proposals):
        ax = axes[0, i]
        prop_data = (
            summary[summary["proposal_id"] == prop_id]
            .set_index("model")
            .reindex(models)
        )

        bar_colors = [MODEL_STYLES[m]["color"] for m in models]

        ax.bar(prop_data.index, prop_data["pass_rate_pct"], color=bar_colors)
        # Create new labels list, replacing 'Optimal' with 'Responsive'
        new_labels = [
            "Responsive" if model_name == "Optimal" else model_name
            for model_name in prop_data.index
        ]
        ax.set_xticklabels(new_labels)

        prop_label = all_proposals.get(prop_id, "")
        ax.set_title(f"Proposal: {prop_id} {prop_label}")
        ax.set_ylabel("% of Epochs Passed")
        ax.set_ylim(0, 100)
        ax.yaxis.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout(rect=[0, 0.03, 1, 0.94])
    save_path = config.PLOT_DIR / "pass_rate_barchart.png"
    plt.savefig(save_path)
    print(f"  Saved plot: {save_path.name}")
    plt.close(fig)


# --- Main run_plotting function (UPDATED) ---


def run_plotting(config):
    """
    Generates ALL plots for the simulation.
    """

    # 1. Generate the comparative Wprime plot
    comparison_data = load_data_for_comparison(config)
    if comparison_data:
        plot_wprime_share(config, comparison_data)
        plot_wprime_histograms(config, comparison_data)
        plot_median_comparison(config, comparison_data)
    # 2. Generate the per-epoch plots
    generate_epoch_plots(config)

    # --- Load proposal data ONCE ---
    proposal_plot_data = load_all_proposal_data(config)

    if proposal_plot_data is not None:

        # 3. Generate the "all-in-one" FOR % comparison
        generate_proposal_comparison_plot(config, proposal_plot_data)

        # 4. Generate the "Difference from Direct" plot
        generate_difference_plot(config, proposal_plot_data)

        # 5. Generate the "Pass Rate" bar chart
        generate_pass_rate_barchart(config, proposal_plot_data)
