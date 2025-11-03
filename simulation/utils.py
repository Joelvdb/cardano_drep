from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import random


def utility(opinion_i: float, opinion_j: float) -> float:
    """u = 1 - |Oi - Oj|  (in [0,1])"""
    return 1.0 - abs(opinion_i - opinion_j)


@dataclass
class DRep:
    """Delegate Representative."""

    id: str
    opinion: float  # O_t(j) in [0,1]
    stake: float = 0.0  # own stake (optional)


@dataclass
class Delegator:
    """Delegator with stickiness s_i and current delegation D_t(i)."""

    id: str
    opinion: float  # O_t(i) in [0,1]
    stake: float = 0.0  # own stake (optional)
    s: float = 0.5  # stickiness s_i in [0,1]
    current: Optional[DRep] = None  # current DRep object (D_t(i))

    # --- Core behaviors ---

    def reconsider_prob(self) -> float:
        """p(reconsider) = 1 - s_i (time-independent)."""
        return max(0.0, min(1.0, 1.0 - self.s))

    def closest_drep(self, dreps: List[DRep]) -> DRep:
        """argmin_j |O(i) - O(j)|; tie-break: by id (stable)."""
        return min(dreps, key=lambda d: (abs(self.opinion - d.opinion), d.id))

    def utility_with(self, drep: DRep) -> float:
        """Utility of delegating to a given DRep."""
        return utility(self.opinion, drep.opinion)

    def current_utility(self) -> float:
        """Utility with current DRep; 0.0 if no current."""
        if self.current is None:
            return 0.0
        return utility(self.opinion, self.current.opinion)

    def delta_u_vs_current(self, best: DRep) -> float:
        """Δu = u(best) - u(current); if no current, treat u(current)=0."""
        u_best = self.utility_with(best)
        u_cur = self.current_utility()
        return u_best - u_cur

    def step(
        self, dreps: List[DRep], rng: random.Random = random
    ) -> Tuple[bool, Optional[DRep]]:
        """
        One epoch decision for this delegator.

        Process:
          1) Draw reconsider ~ Bernoulli(1 - s_i)
          2) If reconsider and there is a strictly better DRep (Δu > 0),
             switch to that DRep with probability Δu (clamped to [0,1]).
        Returns:
          (switched?, new_current DRep or None)
        """
        best = self.closest_drep(dreps)
        delta_u = self.delta_u_vs_current(best)

        # If no improvement, never switch (even if reconsidered)
        if delta_u <= 0:
            return (False, self.current)

        # Stage 1: reconsider
        if rng.random() >= self.reconsider_prob():
            print(f"delegetor {self.id} maintained due to stickiness")
            return (False, self.current)  # maintained due to stickiness

        # Stage 2: accept better option with probability Δu
        p_switch = max(0.0, min(1.0, delta_u))
        if rng.random() < p_switch:
            self.current = best
            return (True, self.current)
        else:
            print(f"delegetor {self.id} maintained due to utility")
            return (False, self.current)


@dataclass
class World:
    """Simple container to simulate one epoch across multiple delegators."""

    dreps: List[DRep] = field(default_factory=list)
    delegators: List[Delegator] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)

    def epoch(self) -> dict:
        """
        Run one epoch across all delegators.
        Returns a small report dict (switched list, delegation map, W'_t per DRep).
        """
        switched = []
        for delegator in self.delegators:
            did_switch, _ = delegator.step(self.dreps, rng=self.rng)
            if did_switch:
                switched.append(delegator)

        # Compute W'_t(d): own stake + sum of delegators delegating to d
        Wprime = {d.id: d.stake for d in self.dreps}
        for delegator in self.delegators:
            if delegator.current is not None:
                Wprime[delegator.current.id] += delegator.stake

        # Map delegator -> current DRep id (or None)
        delegation_map = {
            delegator.id: (delegator.current.id if delegator.current else None)
            for delegator in self.delegators
        }
        return {
            "switched": switched,  # list of delegetors whos drep has been switched in epoch
            "delegation_map": delegation_map,  # map from delegetor id to DRep
            "Wprime": Wprime,  # map of stake from drep id to stake
        }

    def plot_opinions(
        self,
        use_stake_size: bool = True,
        size_scale: float = 20.0,
        jitter: float = 0.02,
        draw_edges: bool = True,
        edge_alpha: float = 0.25,
        edge_lw: float = 0.6,
        edge_color: str = "0.3",
        edge_samples: int | None = None,
        edge_random_seed: int | None = 123,
    ):
        """
        Visualize opinions of delegators and DReps on [0,1], with optional delegation edges.

        Params
        -------
        use_stake_size : marker size proportional to stake if True
        size_scale     : multiplier for stake->size
        jitter         : small vertical jitter to de-overlap rows
        draw_edges     : draw edges from each delegator to their current DRep
        edge_alpha     : transparency for edges
        edge_lw        : line width for edges
        edge_color     : matplotlib color for edges (e.g., '0.3' grey)
        edge_samples   : if set, randomly sample this many delegators to draw edges
        edge_random_seed : seed for edge sampling reproducibility

        Returns
        -------
        (fig, ax)
        """
        import matplotlib.pyplot as plt
        import random as _r

        # --- positions on the x axis ---
        x_deleg = [d.opinion for d in self.delegators]
        x_dreps = [d.opinion for d in self.dreps]

        # two horizontal rows with slight jitter
        y_row_deleg = 0.35
        y_row_dreps = 0.65
        y_deleg = [
            y_row_deleg + (_r.uniform(-jitter, jitter) if jitter > 0 else 0.0)
            for _ in x_deleg
        ]
        y_dreps = [
            y_row_dreps + (_r.uniform(-jitter, jitter) if jitter > 0 else 0.0)
            for _ in x_dreps
        ]

        # marker sizes
        if use_stake_size:
            s_deleg = [max(10.0, d.stake * size_scale) for d in self.delegators]
            s_dreps = [max(10.0, d.stake * size_scale) for d in self.dreps]
        else:
            s_deleg = [25.0] * len(x_deleg)
            s_dreps = [40.0] * len(x_dreps)

        # map DRep.id -> (x, y) for edge endpoints
        drep_pos = {d.id: (x, y) for d, x, y in zip(self.dreps, x_dreps, y_dreps)}

        fig, ax = plt.subplots(figsize=(10, 3.2))
        ax.set_xlim(0, 1)
        ax.set_ylim(0.2, 0.8)
        ax.hlines(0.5, 0.0, 1.0, linestyles="dashed", linewidth=0.8)

        # --- edges first (so points sit on top) ---
        if draw_edges and self.delegators:
            # indices of delegators that actually have a current DRep
            idxs = [i for i, a in enumerate(self.delegators) if a.current is not None]
            # optional subsampling to avoid clutter
            if edge_samples is not None and edge_samples < len(idxs):
                _rng = _r.Random(edge_random_seed)
                idxs = _rng.sample(idxs, edge_samples)

            for i in idxs:
                a = self.delegators[i]
                (x1, y1) = (x_deleg[i], y_deleg[i])
                # lookup endpoint by DRep id (robust if objects were copied)
                x2, y2 = drep_pos.get(a.current.id, (None, None))
                if x2 is None:
                    continue
                ax.plot(
                    [x1, x2],
                    [y1, y2],
                    linewidth=edge_lw,
                    alpha=edge_alpha,
                    color=edge_color,
                )

        # --- points ---
        ax.scatter(
            x_deleg, y_deleg, s=s_deleg, alpha=0.6, marker="o", label="Delegators"
        )
        ax.scatter(x_dreps, y_dreps, s=s_dreps, alpha=0.9, marker="s", label="DReps")

        # labels/ticks
        ax.set_xlabel("Opinion in [0, 1]")
        ax.set_yticks(
            [y_row_deleg, 0.5, y_row_dreps], labels=["Delegators", "", "DReps"]
        )
        ax.set_title("Opinions & delegations along a 0–1 spectrum")
        ax.legend(loc="upper center", ncol=2, frameon=False)
        fig.tight_layout()
        return fig, ax


__all__ = ["DRep", "Delegator", "utility", "World"]
