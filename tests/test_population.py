"""
Tests for population structure and pedigree hierarchy.
"""
from config import BreedingConfig
from simulation.population import create_founder_population
from simulation.traits import assign_founder_traits

def test_founder_population_structure():
    config = BreedingConfig(n_sires=10, dams_per_sire=2, offspring_per_dam=15)
    pop = create_founder_population(config)
    
    expected_size = 10 * 2 * 15  # 300
    assert len(pop) == expected_size
    assert set(pop.columns) >= {"id", "sire_id", "dam_id", "family_id", "sire_family_id", "generation", "sex"}
    
    # Check sire families
    assert pop["sire_family_id"].nunique() == 10
    # Check full-sib families
    assert pop["family_id"].nunique() == 20
    # Check sex distribution is roughly balanced
    male_count = (pop["sex"] == "M").sum()
    assert 100 < male_count < 200

def test_trait_assignment():
    config = BreedingConfig(n_sires=5, dams_per_sire=2, offspring_per_dam=10, mean_phenotype=200.0)
    pop = create_founder_population(config)
    pop = assign_founder_traits(pop, config)
    
    assert "genetic_value" in pop.columns
    assert "env_effect" in pop.columns
    assert "phenotype" in pop.columns
    # Mean phenotype should be close to 200 mg
    assert 185.0 < pop["phenotype"].mean() < 215.0
