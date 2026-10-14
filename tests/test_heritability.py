"""
Sanity tests for heritability estimation via ANOVA.
Includes a multi-trial test to verify that average estimated h^2
lands within ~0.15 of true configured h^2 (0.30).
"""
import numpy as np
from config import BreedingConfig
from simulation.population import create_founder_population
from simulation.traits import assign_founder_traits
from genetics.heritability import estimate_heritability_anova, true_heritability

def test_heritability_recovery_multi_trial():
    """
    Runs repeated founder trials to test ANOVA heritability recovery.
    Because single-sample ANOVA estimates are noisy, the mean across trials
    must be close to true h^2 (0.30).
    """
    config = BreedingConfig(
        n_sires=25,
        dams_per_sire=4,
        offspring_per_dam=20,
        sigma_a2=9.0,
        sigma_e2=21.0  # true h^2 = 0.30
    )
    
    h2_estimates = []
    n_trials = 20
    
    for seed in range(n_trials):
        rng = np.random.default_rng(seed)
        pop = create_founder_population(config, rng=rng)
        pop = assign_founder_traits(pop, config, rng=rng)
        
        res = estimate_heritability_anova(pop)
        h2_estimates.append(res["h2_est"])
        
    mean_estimated_h2 = np.mean(h2_estimates)
    print(f"Mean ANOVA h^2 across {n_trials} trials: {mean_estimated_h2:.3f} (target: 0.30)")
    
    # Must land within 0.15 of true h^2
    assert abs(mean_estimated_h2 - config.true_h2) < 0.15
