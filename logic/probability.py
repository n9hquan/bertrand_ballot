def theoretical_prob(a: int, b: int) -> float:
    """Return theoretical Bertrand Ballot probability."""
    if a <= b:
        return 0.0
    return (a - b) / (a + b)