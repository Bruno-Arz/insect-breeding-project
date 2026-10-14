"""
Narrow-sense heritability (h^2) estimation via one-way ANOVA of paternal half-sibs.
h^2 = 4 * sigma_sire^2 / sigma_phenotypic^2
"""
import pandas as pd
import numpy as np

def estimate_heritability_anova(pop_df: pd.DataFrame) -> dict:
    """
    Estimates sire variance component and narrow-sense heritability using one-way ANOVA
    grouped by paternal half-sib families (sire_family_id).
    """
    groups = pop_df.groupby("sire_family_id")["phenotype"]
    s = groups.ngroups  # number of sire families
    N = len(pop_df)     # total individuals
    
    if s <= 1 or N <= s:
        return {"h2_est": 0.0, "sigma2_sire": 0.0, "sigma2_within": 0.0, "sigma2_p": 0.0}
        
    # Group sizes
    ni = groups.size().values
    grand_mean = pop_df["phenotype"].mean()
    group_means = groups.mean().values
    
    # Sum of squares
    SS_between = np.sum(ni * (group_means - grand_mean)**2)
    SS_within = np.sum(groups.apply(lambda g: np.sum((g - g.mean())**2)).values)
    
    # Degrees of freedom
    df_between = s - 1
    df_within = N - s
    
    MS_between = SS_between / df_between
    MS_within = SS_within / df_within
    
    # Coefficient k0 for unequal/equal group sizes
    # k0 = (1 / (s - 1)) * (N - sum(ni^2) / N)
    k0 = (N - np.sum(ni**2) / N) / (s - 1)
    
    sigma2_sire = max(0.0, (MS_between - MS_within) / k0)
    sigma2_within = MS_within
    sigma2_p = sigma2_sire + sigma2_within
    
    if sigma2_p > 0:
        h2_est = (4.0 * sigma2_sire) / sigma2_p
        h2_est = min(max(h2_est, 0.0), 1.0) # Clamp within [0, 1]
    else:
        h2_est = 0.0
        
    return {
        "h2_est": float(h2_est),
        "sigma2_sire": float(sigma2_sire),
        "sigma2_within": float(sigma2_within),
        "sigma2_p": float(sigma2_p)
    }

def true_heritability(pop_df: pd.DataFrame) -> float:
    """
    Calculates true h^2 from simulated values: Var(A) / Var(P)
    """
    var_a = pop_df["genetic_value"].var()
    var_p = pop_df["phenotype"].var()
    if var_p == 0:
        return 0.0
    return float(var_a / var_p)
