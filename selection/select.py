"""
Truncation selection by EBV separately for males and females.
Calculates selection differential S.
"""
import pandas as pd
import numpy as np
from config import BreedingConfig

def truncation_select(pop_df: pd.DataFrame, proportion: float = 0.20):
    """
    Selects top proportion of males and females based on EBV.
    Returns:
        selected_males_df, selected_females_df, selection_differential (S)
    """
    males = pop_df[pop_df["sex"] == "M"].copy()
    females = pop_df[pop_df["sex"] == "F"].copy()
    
    n_sel_m = max(1, int(len(males) * proportion))
    n_sel_f = max(1, int(len(females) * proportion))
    
    sel_males = males.sort_values(by="ebv", ascending=False).head(n_sel_m)
    sel_females = females.sort_values(by="ebv", ascending=False).head(n_sel_f)
    
    selected_pop = pd.concat([sel_males, sel_females])
    
    # Selection differential S = mean(selected phenotype) - mean(population phenotype)
    mean_sel_p = selected_pop["phenotype"].mean()
    mean_pop_p = pop_df["phenotype"].mean()
    S = float(mean_sel_p - mean_pop_p)
    
    return sel_males, sel_females, S
