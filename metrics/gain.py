"""
Genetic gain metrics:
- Realized gain = mean(BV_t) - mean(BV_{t-1})
- Predicted gain = h^2 * S (Breeder's Equation)
"""

def predicted_gain(h2: float, S: float) -> float:
    """
    Breeder's Equation: R = h^2 * S
    """
    return float(h2 * S)

def realized_gain(current_mean_bv: float, prev_mean_bv: float) -> float:
    """
    Observed change in population mean breeding value.
    """
    return float(current_mean_bv - prev_mean_bv)
