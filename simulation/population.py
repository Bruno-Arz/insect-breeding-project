"""
Population structure and nested family generation.
Schema: id, sire_id, dam_id, family_id, sire_family_id, generation, sex
"""
import pandas as pd
import numpy as np
from config import BreedingConfig

def create_founder_population(config: BreedingConfig, rng: np.random.Generator = None) -> pd.DataFrame:
    """
    Creates Generation 0 offspring according to nested half-sib/full-sib design.
    """
    if rng is None:
        rng = np.random.default_rng(config.random_seed)
        
    records = []
    ind_counter = 1
    
    for s in range(1, config.n_sires + 1):
        sire_id = f"G0_S{s:03d}"
        sire_family_id = f"SF_{s:03d}"
        for d in range(1, config.dams_per_sire + 1):
            dam_idx = (s - 1) * config.dams_per_sire + d
            dam_id = f"G0_D{dam_idx:03d}"
            family_id = f"FS_{s:03d}_{d:02d}"
            
            for _ in range(config.offspring_per_dam):
                sex = "M" if rng.random() < 0.5 else "F"
                records.append({
                    "id": f"G0_I{ind_counter:05d}",
                    "sire_id": sire_id,
                    "dam_id": dam_id,
                    "family_id": family_id,
                    "sire_family_id": sire_family_id,
                    "generation": 0,
                    "sex": sex
                })
                ind_counter += 1
                
    return pd.DataFrame(records)
