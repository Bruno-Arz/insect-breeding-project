"""
Trait simulation for larval body weight under infinitesimal model.
Phenotype = mean_phenotype + genetic_value + environmental_noise
"""
import pandas as pd
import numpy as np
from config import BreedingConfig

def assign_founder_traits(pop_df: pd.DataFrame, config: BreedingConfig, rng: np.random.Generator = None) -> pd.DataFrame:
    """
    Assigns genetic values and phenotypes to founder generation offspring.
    Founder sires and dams have genetic values ~ N(0, sigma_a2).
    Offspring receive 0.5 * a_sire + 0.5 * a_dam + Mendelian sampling ~ N(0, 0.5 * sigma_a2).
    """
    if rng is None:
        rng = np.random.default_rng(config.random_seed)
        
    df = pop_df.copy()
    n = len(df)
    
    unique_sires = df["sire_id"].unique()
    unique_dams = df["dam_id"].unique()
    
    # Founder parents genetic values ~ N(0, sigma_a2)
    sire_bv = {sid: rng.normal(0, np.sqrt(config.sigma_a2)) for sid in unique_sires}
    dam_bv = {did: rng.normal(0, np.sqrt(config.sigma_a2)) for did in unique_dams}
    
    sire_vals = df["sire_id"].map(sire_bv).values
    dam_vals = df["dam_id"].map(dam_bv).values
    
    # Mendelian sampling noise ~ N(0, 0.5 * sigma_a2)
    mendelian_sd = np.sqrt(0.5 * config.sigma_a2)
    mendelian_noise = rng.normal(0, mendelian_sd, size=n)
    
    df["genetic_value"] = 0.5 * sire_vals + 0.5 * dam_vals + mendelian_noise
    df["env_effect"] = rng.normal(0, np.sqrt(config.sigma_e2), size=n)
    df["phenotype"] = config.mean_phenotype + df["genetic_value"] + df["env_effect"]
    
    return df

def assign_offspring_traits(offspring_df: pd.DataFrame, parent_bv_map: dict, config: BreedingConfig, rng: np.random.Generator = None) -> pd.DataFrame:
    """
    Assigns genetic value and phenotype to offspring from parental breeding values.
    a_offspring = 0.5 * a_sire + 0.5 * a_dam + Mendelian sampling ~ N(0, 0.5 * sigma_a2)
    """
    if rng is None:
        rng = np.random.default_rng()
        
    df = offspring_df.copy()
    n = len(df)
    
    sire_bvs = df["sire_id"].map(parent_bv_map).values
    dam_bvs = df["dam_id"].map(parent_bv_map).values
    
    mendelian_sd = np.sqrt(0.5 * config.sigma_a2)
    mendelian_noise = rng.normal(0, mendelian_sd, size=n)
    
    df["genetic_value"] = 0.5 * sire_bvs + 0.5 * dam_bvs + mendelian_noise
    df["env_effect"] = rng.normal(0, np.sqrt(config.sigma_e2), size=n)
    df["phenotype"] = config.mean_phenotype + df["genetic_value"] + df["env_effect"]
    
    return df
