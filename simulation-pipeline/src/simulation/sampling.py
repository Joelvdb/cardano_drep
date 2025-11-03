import random

# --- Agent Parameter Sampling Functions ---

def sample_opinion_drep(rng: random.Random) -> float:
    # Example: bimodal-ish around 0.25 / 0.75
    return rng.random()

def sample_opinion_delegator(rng: random.Random) -> float:
    return rng.random()

def sample_stake(rng: random.Random) -> float:
    return rng.random()

def sample_stickiness(rng: random.Random, mean=0.6, k=40) -> float:
    # a = mean * k
    # b = (1 - mean) * k
    # return rng.betavariate(a, b)
    return rng.random()

# --- You can add new sampling functions here ---
# def sample_stake_v2(rng: random.Random) -> float:
#     return rng.gammavariate(2.0, 1.0)
