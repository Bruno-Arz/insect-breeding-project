"""
Inbreeding metrics:
- Effective population size Ne = 4 * Ns * Nd / (Ns + Nd)
- Rate of inbreeding delta_F = 1 / (2 * Ne)
- Cumulative inbreeding F_t = F_{t-1} + (1 - F_{t-1}) * delta_F
"""

def effective_population_size(n_sires: int, n_dams: int) -> float:
    """
    Computes effective population size Ne for unequal number of sexes.
    """
    if n_sires + n_dams == 0:
        return 0.0
    return float(4.0 * n_sires * n_dams / (n_sires + n_dams))

def delta_inbreeding(Ne: float) -> float:
    """
    Rate of inbreeding delta_F = 1 / (2 * Ne)
    """
    if Ne <= 0:
        return 0.0
    return float(1.0 / (2.0 * Ne))

def cumulative_inbreeding(f_prev: float, delta_f: float) -> float:
    """
    Cumulative inbreeding coefficient: F_t = F_{t-1} + (1 - F_{t-1}) * delta_F
    """
    return float(f_prev + (1.0 - f_prev) * delta_f)
