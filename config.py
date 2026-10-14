"""
Configuration parameters for the insect selective breeding simulation.
Centralizes all simulation and biological parameters.
"""
from dataclasses import dataclass

@dataclass
class BreedingConfig:
    # Population structure
    n_sires: int = 20           # Number of breeding sires per generation
    dams_per_sire: int = 3      # Number of dams mated to each sire (nested half-sib)
    offspring_per_dam: int = 20 # Offspring per dam (full-sib family size)
    n_generations: int = 15     # Number of generations to simulate
    
    # Quantitative genetics parameters
    sigma_a2: float = 9.0       # Additive genetic variance (mg^2)
    sigma_e2: float = 21.0      # Environmental variance (mg^2) -> true h^2 = 9 / (9+21) = 0.30
    mean_phenotype: float = 200.0  # Base larval body weight (mg)
    
    # Selection parameters
    selection_proportion: float = 0.20  # Proportion selected (top 20%)
    
    # Reproducibility
    random_seed: int = 42

    @property
    def true_h2(self) -> float:
        return self.sigma_a2 / (self.sigma_a2 + self.sigma_e2)

    @property
    def total_offspring_per_gen(self) -> int:
        return self.n_sires * self.dams_per_sire * self.offspring_per_dam

DEFAULT_CONFIG = BreedingConfig()
