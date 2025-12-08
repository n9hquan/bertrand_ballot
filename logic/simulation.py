import random

def run_single_sequence(a: int, b: int):
    """Return a random sequence of A/B ballots."""
    votes = ['A'] * a + ['B'] * b
    random.shuffle(votes)
    return votes


def run_many_simulations(a: int, b: int, trials: int):
    """Monte Carlo simulation of Bertrand Ballot."""
    if a <= b:
        return 0.0

    success = 0
    for _ in range(trials):
        votes = run_single_sequence(a, b)
        a_count = 0
        b_count = 0
        ok = True

        for v in votes:
            a_count += (v == 'A')
            b_count += (v == 'B')

            if a_count <= b_count:
                ok = False
                break

        if ok:
            success += 1

    return success / trials