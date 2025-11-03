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
        return (f"DRep(id={self.id}, opinion={self.opinion:.2f}, "
                f"stake={self.stake:.2f}, w_prime={self.w_prime:.2f})")

class Delegator:
    def __init__(self, id: str, opinion: float, stake: float, s: float, current: Optional[DRep]):
        self.id: str = str(id)
        self.opinion: float = float(opinion)
        self.stake: float = float(stake)
        self.s: float = float(s)  # Stickiness in [0, 1]
        self.current: Optional[DRep] = current

    def utility(self, drep: DRep) -> float:
        """Calculates utility for a given DRep."""
        return 1.0 - abs(self.opinion - drep.opinion)

    def find_best_drep(self, dreps: List[DRep]) -> DRep:
        """Finds the best DRep by utility (opinion proximity)."""
        best_drep = max(dreps, key=lambda d: (self.utility(d), d.id))
        return best_drep

    def delegate(self, dreps: List[DRep], rng: random.Random):
        """
        Decision-making logic for delegation based on stickiness and utility.
        """
        # 1. Reconsideration
        if self.current is None:
            # No current DRep, must choose one
            best_drep = self.find_best_drep(dreps)
            self.current = best_drep
            # print(f"delegator {self.id} initial delegation to {self.current.id}")
            return

        if rng.random() >= (1.0 - self.s):
            # Maintained delegation due to stickiness
            # print(f"delegator {self.id} maintained due to stickiness")
            return

        # 2. Re-evaluation
        best_drep = self.find_best_drep(dreps)
        
        current_utility = self.utility(self.current)
        best_utility = self.utility(best_drep)
        delta_u = best_utility - current_utility

        # 3. Switching
        if delta_u > 0:
            # Switch with probability delta_u
            if rng.random() < delta_u:
                self.current = best_drep
                # print(f"delegator {self.id} switched to {self.current.id} (delta_u={delta_u:.2f})")
            # else:
                # print(f"delegator {self.id} re-evaluated but did not switch")
        # else:
            # print(f"delegator {self.id} maintained due to utility")

    def __repr__(self) -> str:
        current_id = self.current.id if self.current else "None"
        return (f"Delegator(id={self.id}, opinion={self.opinion:.2f}, "
                f"stake={self.stake:.2f}, s={self.s:.2f}, current={current_id})")

class World:
    def __init__(self, dreps: List[DRep], delegators: List[Delegator], rng: random.Random):
        self.dreps = dreps
        self.delegators = delegators
        self.rng = rng

    def epoch(self):
        """Simulates one epoch of delegation."""
        
        # 1. Reset DRep delegated stake
        for drep in self.dreps:
            drep.delegated_stake = 0.0

        # 2. Delegators make their decisions
        for delegator in self.delegators:
            delegator.delegate(self.dreps, self.rng)
        
        # 3. Tally new delegated stake
        for delegator in self.delegators:
            if delegator.current:
                delegator.current.delegated_stake += delegator.stake
        
        # 4. Update DRep w_prime values
        for drep in self.dreps:
            drep.update_w_prime()

    def __repr__(self) -> str:
        return f"World(DReps={len(self.dreps)}, Delegators={len(self.delegators)})"
