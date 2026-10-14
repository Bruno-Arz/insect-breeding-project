"""
Tests for truncation selection and breeding values.
"""
from config import BreedingConfig
from simulation.population import create_founder_population
from simulation.traits import assign_founder_traits
from genetics.breeding_value import individual_ebv
from selection.select import truncation_select

def test_truncation_selection():
    config = BreedingConfig(n_sires=10, dams_per_sire=2, offspring_per_dam=20, selection_proportion=0.20)
    pop = create_founder_population(config)
    pop = assign_founder_traits(pop, config)
    pop["ebv"] = individual_ebv(pop, config.true_h2)
    
    sel_m, sel_f, S = truncation_select(pop, proportion=0.20)
    
    # Selected proportions
    males_total = (pop["sex"] == "M").sum()
    females_total = (pop["sex"] == "F").sum()
    
    assert len(sel_m) == int(males_total * 0.20)
    assert len(sel_f) == int(females_total * 0.20)
    
    # Selection differential S must be strictly positive
    assert S > 0.0
    
    # Selected animals should have higher mean phenotype and EBV than population
    assert sel_m["phenotype"].mean() > pop[pop["sex"] == "M"]["phenotype"].mean()
    assert sel_f["phenotype"].mean() > pop[pop["sex"] == "F"]["phenotype"].mean()
