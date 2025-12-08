import random

def theoretical_prob(a: int, b: int) -> float:
    if a == b:
        return 0.0
    return abs(a - b) / (a + b)

def run_single_sequence(a: int, b: int):
    # Return a randomized sequence of 'A' and 'B' of length a+b
    votes = ["A"] * a + ["B"] * b
    random.shuffle(votes)
    return votes