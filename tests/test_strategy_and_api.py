"""
Unit tests for 30% Milestone features:
- Family EBV vs Individual EBV calculation
- Simulation REST API engine execution
- Strategy comparison logic
"""
import pytest
import numpy as np
import pandas as pd
from config import BreedingConfig
from simulation.population import create_founder_population
from simulation.traits import assign_founder_traits
from genetics.breeding_value import individual_ebv, family_ebv
from api import SimulationRequest, run_simulation_engine, simulate, compare_strategies


def test_family_ebv_properties():
    """Verify that family EBV computes valid weights and correlates with family mean."""
    config = BreedingConfig(n_sires=5, dams_per_sire=2, offspring_per_dam=10)
    pop = create_founder_population(config)
    pop = assign_founder_traits(pop, config)

    ind_ebv = individual_ebv(pop, config.true_h2)
    fam_ebv = family_ebv(pop, config.true_h2, family_col="family_id")

    assert len(fam_ebv) == len(pop)
    # Family EBV within the same family_id should be identical
    first_fam = pop["family_id"].iloc[0]
    first_fam_ebvs = fam_ebv[pop["family_id"] == first_fam]
    assert np.allclose(first_fam_ebvs, first_fam_ebvs.iloc[0])

    # Means should be roughly centered around 0
    assert abs(ind_ebv.mean()) < 1e-4
    assert abs(fam_ebv.mean()) < 1e-4


def test_run_simulation_engine_api():
    """Verify API simulation engine executes and produces structured generation records (Gen 0 to Gen N)."""
    n_gens = 5
    req = SimulationRequest(
        n_sires=10,
        dams_per_sire=2,
        offspring_per_dam=10,
        n_generations=n_gens,
        target_h2=0.30,
        random_seed=123,
    )
    records = run_simulation_engine(req, strategy="individual_ebv")

    # Includes Generation 0 (Founder) + 5 selected generations = 6 records
    assert len(records) == n_gens + 1
    assert records[0]["generation"] == 0
    assert records[-1]["generation"] == n_gens

    # Check that breeding value progresses positively under selection
    assert records[-1]["mean_bv"] > records[0]["mean_bv"]

    # Check inbreeding increases monotonically
    for i in range(1, len(records)):
        assert records[i]["cumulative_F"] >= records[i - 1]["cumulative_F"]


def test_api_simulate_summary():
    """Verify simulate endpoint response summary matches expected fields."""
    n_gens = 3
    req = SimulationRequest(
        n_sires=10,
        dams_per_sire=2,
        offspring_per_dam=10,
        n_generations=n_gens,
        random_seed=42,
    )
    res = simulate(req)

    assert res.summary.initial_weight_mg > 0
    assert res.summary.final_weight_mg > res.summary.initial_weight_mg
    assert res.summary.total_genetic_gain_mg > 0
    assert res.summary.effective_population_size_Ne > 0
    assert len(res.generations) == n_gens + 1


def test_api_compare_strategies():
    """Verify strategy comparison returns both strategies with non-zero gains."""
    n_gens = 4
    req = SimulationRequest(
        n_sires=10,
        dams_per_sire=2,
        offspring_per_dam=10,
        n_generations=n_gens,
        random_seed=42,
    )
    comp = compare_strategies(req)

    assert "individual_ebv" in comp
    assert "family_ebv" in comp
    assert comp["individual_ebv"]["total_gain_mg"] > 0
    assert comp["family_ebv"]["total_gain_mg"] > 0
    assert len(comp["individual_ebv"]["records"]) == n_gens + 1
    assert len(comp["family_ebv"]["records"]) == n_gens + 1
