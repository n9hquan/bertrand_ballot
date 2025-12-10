import random

def theoretical_prob(a: int, b: int) -> float:
    if a == b:
        return 0.0
    return abs(a - b) / (a + b)

def run_single_sequence(a: int, b: int):
    votes = ["A"] * a + ["B"] * b
    random.shuffle(votes)
    return votes