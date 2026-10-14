"""
Estimated Breeding Value (EBV) calculation.
(a) Individual EBV: EBV = h^2 * (phenotype - population_mean)
(b) Family EBV: EBV_fam = b * (family_mean - population_mean)
    where b = n * h^2 / (1 + (n - 1) * t), and t = h^2 / 2 for full-sibs.
"""
import pandas as pd
import numpy as np

def individual_ebv(pop_df: pd.DataFrame, h2: float) -> pd.Series:
    """
    Calculates individual EBV.
    """
    mean_p = pop_df["phenotype"].mean()
    return h2 * (pop_df["phenotype"] - mean_p)

def family_ebv(pop_df: pd.DataFrame, h2: float, family_col: str = "family_id") -> pd.Series:
    """
    Calculates full-sib family EBV broadcast to each individual.
    """
    mean_p = pop_df["phenotype"].mean()
    fam_stats = pop_df.groupby(family_col)["phenotype"].agg(["count", "mean"])
    
    t = h2 / 2.0  # correlation between full-sibs under additive gene action
    
    # b regression coefficient
    fam_stats["b"] = (fam_stats["count"] * h2) / (1.0 + (fam_stats["count"] - 1.0) * t)
    fam_stats["fam_ebv"] = fam_stats["b"] * (fam_stats["mean"] - mean_p)
    
    return pop_df[family_col].map(fam_stats["fam_ebv"])
