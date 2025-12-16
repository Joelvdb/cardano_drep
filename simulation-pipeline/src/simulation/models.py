import random
from typing import Optional, List

# --- Core Simulation Classes ---
# (Content from your utils.py)


class DRep:
    def __init__(self, id: str, opinion: float, stake: float):
        self.id: str = str(id)
        self.opinion: float = float(opinion)
        self.stake: float = float(stake)
        self.delegated_stake: float = 0.0
        self.w_prime: float = 0.0  # w_prime = stake + delegated_stake

    def update_w_prime(self):
        self.w_prime = self.stake + self.delegated_stake

    def __repr__(self) -> str:
        return (
            f"DRep(id={self.id}, opinion={self.opinion:.2f}, "
            f"stake={self.stake:.2f}, w_prime={self.w_prime:.2f})"
        )


class Delegator:
    def __init__(
        self, id: str, opinion: float, stake: float, s: float, current: Optional[DRep]
    ):
        self.id: str = str(id)
        self.opinion: float = float(opinion)
        self.stake: float = float(stake)
        self.s: float = float(s)  # Stickiness in [0, 1]
        self.current: Optional[DRep] = current
        self.last_delta_u: float = 0.0
        self.last_delta_u: float = 0.0
        self.last_responsive_id: Optional[str] = None
        self.is_frozen: bool = False

    def utility(self, drep: DRep) -> float:
        """Calculates utility for a given DRep."""
        return 1.0 - abs(self.opinion - drep.opinion)

    def find_best_drep(self, dreps: List[DRep]) -> DRep:
        """Finds the best DRep by utility (opinion proximity)."""
        # 1. Find the best candidate based on utility (tie-break by ID)
        best_candidate = max(dreps, key=lambda d: (self.utility(d), d.id))

        # 2. If current DRep exists and has equal utility to the best candidate, stick with current
        if self.current:
            if self.utility(self.current) >= self.utility(best_candidate):
                return self.current

        return best_candidate

    def delegate(self, dreps: List[DRep], rng: random.Random, model_type: str = "probabilistic"):
        """
        Decision-making logic for delegation based on stickiness and utility.
        model_type: "probabilistic", "responsive", "frozen"
        """
        # 1. Always calculate responsive (best) for reporting
        best_drep = self.find_best_drep(dreps)
        self.last_responsive_id = best_drep.id
        
        if self.current:
            current_utility = self.utility(self.current)
            best_utility = self.utility(best_drep)
            delta_u = best_utility - current_utility
            self.last_delta_u = delta_u
        else:
            self.last_delta_u = 0.0

        # 2. Initial Delegation (if none)
        if self.current is None:
            self.current = best_drep
            self.is_frozen = False
            return

        # 3. Apply Delegation Model Logic
        
        if model_type == "frozen":
            # Never switch after initial assignment
            self.is_frozen = True
            return

        if model_type == "responsive":
            # Always switch to best
            self.current = best_drep
            self.is_frozen = False
            return

        # Default: Probabilistic (Stickiness + Utility)
        if rng.random() <= (1.0 - self.s)*(self.last_delta_u**self.s) and self.last_delta_u > 0:
            self.is_frozen = False
            self.current = best_drep
            return
        self.is_frozen = True
        # if rng.random() >= (1.0 - self.s):
        #     # Maintained delegation due to stickiness
        #     self.is_frozen = True
        #     return
        
        # self.is_frozen = False

        # # Switching logic
        # if self.last_delta_u > 0:
        #     # Switch with probability delta_u
        #     if rng.random() < self.last_delta_u:
        #         self.current = best_drep

    def __repr__(self) -> str:
        current_id = self.current.id if self.current else "None"
        return (
            f"Delegator(id={self.id}, opinion={self.opinion:.2f}, "
            f"stake={self.stake:.2f}, s={self.s:.2f}, current={current_id})"
        )


class World:
    def __init__(
        self, dreps: List[DRep], delegators: List[Delegator], rng: random.Random
    ):
        self.dreps = dreps
        self.delegators = delegators
        self.rng = rng

    def epoch(self, model_type: str = "probabilistic"):
        """Simulates one epoch of delegation."""

        # 1. Reset DRep delegated stake
        for drep in self.dreps:
            drep.delegated_stake = 0.0

        # 2. Delegators make their decisions
        for delegator in self.delegators:
            delegator.delegate(self.dreps, self.rng, model_type=model_type)

        # 3. Tally new delegated stake
        for delegator in self.delegators:
            if delegator.current:
                delegator.current.delegated_stake += delegator.stake

        # 4. Update DRep w_prime values
        for drep in self.dreps:
            drep.update_w_prime()

    def __repr__(self) -> str:
        return f"World(DReps={len(self.dreps)}, Delegators={len(self.delegators)})"
