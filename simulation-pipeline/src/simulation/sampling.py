import random

# --- Agent Parameter Sampling Functions ---


def sample_opinion_drep(rng: random.Random, dist_type="uniform", alpha=2.0, beta=2.0) -> float:
    if dist_type == "beta":
        return rng.betavariate(alpha, beta)
    return rng.random()


def sample_opinion_delegator(rng: random.Random, dist_type="uniform", alpha=2.0, beta=2.0) -> float:
    if dist_type == "beta":
        return rng.betavariate(alpha, beta)
    return rng.random()


def sample_stake(rng: random.Random, dist_type="uniform", alpha=2.0, beta=5.0) -> float:
    if dist_type == "beta":
        # Stake is usually not 0-1 in reality but for this sim 0-1 is fine, 
        # or we could scale it. Keeping it simple 0-1 for now.
        return rng.betavariate(alpha, beta)
    return rng.random()


def sample_stickiness(rng: random.Random, mean=0.6, k=40) -> float:
    # a = mean * k
    # b = (1 - mean) * k
    # return rng.betavariate(a, b)
    return rng.random()
