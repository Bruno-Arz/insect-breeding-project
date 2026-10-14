"""
Nested mating design: Each selected sire is mated to multiple selected dams.
Generates offspring skeleton for the next generation.
"""
import pandas as pd
import numpy as np
from config import BreedingConfig

def nested_mating(selected_males: pd.DataFrame, selected_females: pd.DataFrame, 
                  generation: int, config: BreedingConfig, rng: np.random.Generator = None):
    """
    Pairs sires with dams in a nested structure and creates the new generation population skeleton.
    Returns:
        offspring_df, parent_bv_map
    """
    if rng is None:
        rng = np.random.default_rng()
        
    # Map of ID -> genetic_value for all selected parents
    parents_all = pd.concat([selected_males, selected_females]).drop_duplicates(subset=["id"])
    parent_bv_map = dict(zip(parents_all["id"], parents_all["genetic_value"]))
    
    # Select n_sires from selected males
    male_ids = selected_males["id"].tolist()
    if len(male_ids) >= config.n_sires:
        sires = rng.choice(male_ids, size=config.n_sires, replace=False)
    else:
        sires = rng.choice(male_ids, size=config.n_sires, replace=True)
        
    female_ids = selected_females["id"].tolist()
    total_dams_needed = config.n_sires * config.dams_per_sire
    
    if len(female_ids) >= total_dams_needed:
        assigned_dams = rng.choice(female_ids, size=total_dams_needed, replace=False)
    else:
        # Sample with replacement if pool is smaller than needed dams
        assigned_dams = rng.choice(female_ids, size=total_dams_needed, replace=True)
        
    records = []
    ind_counter = 1
    dam_idx = 0
    
    for s_idx, sire_id in enumerate(sires, start=1):
        sire_family_id = f"G{generation}_SF_{s_idx:03d}"
        for d_idx in range(1, config.dams_per_sire + 1):
            dam_id = assigned_dams[dam_idx]
            family_id = f"G{generation}_FS_{s_idx:03d}_{d_idx:02d}"
            dam_idx += 1
            
            for _ in range(config.offspring_per_dam):
                sex = "M" if rng.random() < 0.5 else "F"
                records.append({
                    "id": f"G{generation}_I{ind_counter:05d}",
                    "sire_id": sire_id,
                    "dam_id": dam_id,
                    "family_id": family_id,
                    "sire_family_id": sire_family_id,
                    "generation": generation,
                    "sex": sex
                })
                ind_counter += 1
                
    offspring_df = pd.DataFrame(records)
    return offspring_df, parent_bv_map
