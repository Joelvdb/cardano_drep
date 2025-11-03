import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import random
import matplotlib.colors
import numpy as np  # <-- Added Numpy

# --- Plot Function 1: Comparative Plot ---


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


# --- Plot Function 2: Per-Epoch Plots ---


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
            base_deleg = pd.read_csv(
                config.DELEGATORS_STATE_FILE
            )  # epoch, delegator_id, opinion, stake, s
            base_dreps = pd.read_csv(
                config.DREPS_STATE_FILE
            )  # epoch, drep_id, opinion, stake
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
    D = dreps_df[dreps_df["epoch"] == epoch].copy()
    A = deleg_df[deleg_df["epoch"] == epoch].copy()
    if D.empty or A.empty:
        print(f"  - [skip] No data for epoch {epoch} in source '{source}'.")
        return None, None  # Return None to signal skipping

    # Harmonize columns by source
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

    x_deleg = A["opinion"].astype(float).to_list()
    x_dreps = D["opinion"].astype(float).to_list()

    y_row_deleg = 0.35
    y_row_dreps = 0.65
    y_deleg = [
        y_row_deleg + (random.uniform(-jitter, jitter) if jitter > 0 else 0.0)
        for _ in x_deleg
    ]
    y_dreps = [
        y_row_dreps + (random.uniform(-jitter, jitter) if jitter > 0 else 0.0)
        for _ in x_dreps
    ]

    if use_stake_size:
        s_deleg = [max(10.0, float(s) * size_scale_deleg) for s in A["stake"]]
        size_source = D["Wprime"] if "Wprime" in D.columns else D["stake"]
        s_dreps = [max(10.0, float(s) * size_scale_dreps) for s in size_source]
    else:
        s_deleg = [25.0] * len(x_deleg)
        s_dreps = [40.0] * len(x_dreps)

    drep_pos = {
        d: (x, y) for d, x, y in zip(D["drep_id"].astype(str), x_dreps, y_dreps)
    }

    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0.2, 0.8)
    ax.hlines(0.5, 0.0, 1.0, linestyles="dashed", linewidth=0.8)

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

    ax.scatter(x_deleg, y_deleg, s=s_deleg, alpha=0.6, marker="o", label="Delegators")
    ax.scatter(x_dreps, y_dreps, s=s_dreps, alpha=0.9, marker="s", label="DReps")

    ax.set_xlabel("Opinion in [0, 1]")
    ax.set_yticks([y_row_deleg, 0.5, y_row_dreps], labels=["Delegators", "", "DReps"])
    ax.set_title(f"Opinions & delegations (epoch {epoch}, {source})")
    ax.legend(loc="upper center", ncol=2, frameon=False)
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


# --- Plot Function 3: 'FOR' Percentage Plots (Your New Code) ---


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


def plot_for_percentage(ax, df, title: str):
    """Plots the 'FOR' percentage over epochs."""

    if df.empty or "for_pct" not in df.columns:
        ax.text(
            0.5, 0.5, "No Data", ha="center", va="center", fontsize=10, color="grey"
        )
        ax.set_title(title)
        return

    # Plot the average 'FOR' pct across all proposals per epoch
    epoch_data = df.groupby("epoch")["for_pct"].mean().reset_index()

    ax.plot(
        epoch_data["epoch"],
        epoch_data["for_pct"],
        label="Avg. For %",
        color="blue",
        marker="o",
        markersize=4,
        linestyle="-",
    )
    ax.set_title(title)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Avg. Stake 'FOR' (%)")

    ax.set_ylim(0, 100)
    ax.axhline(50, color="grey", linestyle="--", linewidth=1.0, label="50% Threshold")

    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)


def generate_for_percentage_plots(config):
    """Generates four separate plots for 'FOR' percentage."""
    print("  Generating 'FOR' Percentage plots...")

    files_to_load = {
        "Direct": config.PROPOSAL_OUT_DIRECT,
        "Frozen": config.PROPOSAL_OUT_FROZEN,
        "Optimal": config.PROPOSAL_OUT_OPTIMAL,
        "Probabilistic": config.PROPOSAL_OUT_PROBABILISTIC,
    }

    plot_data = {}
    for title, path in files_to_load.items():
        try:
            df = pd.read_csv(path)
            plot_data[title] = add_for_percentage(df)
        except FileNotFoundError:
            print(
                f"  - ⚠️ Warning: Cannot find {path.name}. Skipping '{title}' FOR % plot."
            )
            plot_data[title] = pd.DataFrame()  # Add empty frame to avoid crashing

    # Create a 2x2 grid for these plots
    fig, axes = plt.subplots(2, 2, figsize=(18, 8))
    fig.suptitle("Proposal Outcome: 'FOR' Stake Percentage by Model", fontsize=16)

    plot_for_percentage(axes[0, 0], plot_data["Direct"], "Direct Voting")
    plot_for_percentage(axes[0, 1], plot_data["Frozen"], "Frozen Delegation")
    plot_for_percentage(axes[1, 0], plot_data["Optimal"], "Optimal Delegation")
    plot_for_percentage(
        axes[1, 1], plot_data["Probabilistic"], "Probabilistic Delegation"
    )

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    save_path = config.PLOT_DIR / "for_percentage_comparison.png"
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

    # 2. Generate the new per-epoch plots
    generate_epoch_plots(config)

    # 3. Generate the new 'FOR' percentage plots
    generate_for_percentage_plots(config)
