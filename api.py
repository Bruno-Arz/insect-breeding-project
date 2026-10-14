"""FastAPI Backend Server for Insect Selective Breeding Simulation.

Provides RESTful JSON endpoints with CORS enabled, allowing web frontends
(Bolt.new, Bolt.diy, React, Vue, Next.js) running on http://localhost:8502 or any origin
to execute simulations, retrieve metrics, and render interactive charts.
"""

from typing import List, Optional
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Core simulation modules
from config import BreedingConfig
from simulation.population import create_founder_population
from simulation.traits import assign_founder_traits, assign_offspring_traits
from genetics.heritability import estimate_heritability_anova, true_heritability
from genetics.breeding_value import individual_ebv, family_ebv
from selection.select import truncation_select
from selection.mating import nested_mating
from metrics.gain import predicted_gain, realized_gain
from metrics.inbreeding import effective_population_size, delta_inbreeding, cumulative_inbreeding

app = FastAPI(
    title="Insect Selective Breeding Simulation API",
    description="Backend API for quantitative genetics simulation in Black Soldier Fly & Mealworm",
    version="1.0.0",
)

# Enable CORS for Bolt.new / Bolt.diy running on localhost:8502 or any other frontend port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins including http://localhost:8502
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimulationRequest(BaseModel):
    n_sires: int = Field(default=20, ge=5, le=100, description="Number of breeding sires (males)")
    dams_per_sire: int = Field(default=3, ge=1, le=10, description="Dams mated to each sire")
    offspring_per_dam: int = Field(default=20, ge=5, le=50, description="Larvae per clutch")
    n_generations: int = Field(default=15, ge=1, le=50, description="Generations to simulate")
    mean_phenotype: float = Field(default=200.0, ge=50.0, le=500.0, description="Base larval weight in mg")
    target_h2: float = Field(default=0.30, ge=0.05, le=0.90, description="Target narrow-sense heritability")
    phenotypic_variance: float = Field(default=30.0, ge=5.0, le=200.0, description="Total phenotypic variance")
    selection_proportion: float = Field(default=0.20, ge=0.05, le=0.60, description="Proportion selected (top %)")
    strategy: str = Field(default="individual_ebv", description="'individual_ebv' or 'family_ebv'")
    random_seed: int = Field(default=42, description="Random seed for reproducibility")


class GenerationRecord(BaseModel):
    generation: int
    mean_phenotype: float
    std_phenotype: float
    mean_bv: float
    std_bv: float
    h2_anova: float
    h2_true: float
    selection_differential_S: float
    predicted_gain: float
    realized_gain: float
    cumulative_F: float
    Ne: float
    strategy: str


class SimulationSummary(BaseModel):
    initial_weight_mg: float
    final_weight_mg: float
    total_genetic_gain_mg: float
    gain_percentage: float
    final_inbreeding_F: float
    effective_population_size_Ne: float
    final_h2_anova: float
    target_h2: float
    inbreeding_safety_status: str


class SimulationResponse(BaseModel):
    summary: SimulationSummary
    generations: List[GenerationRecord]


def run_simulation_engine(req: SimulationRequest, strategy: Optional[str] = None) -> List[dict]:
    """Execute simulation engine and return serializable records."""
    active_strategy = strategy or req.strategy
    sigma_a2 = req.target_h2 * req.phenotypic_variance
    sigma_e2 = (1.0 - req.target_h2) * req.phenotypic_variance

    cfg = BreedingConfig(
        n_sires=req.n_sires,
        dams_per_sire=req.dams_per_sire,
        offspring_per_dam=req.offspring_per_dam,
        n_generations=req.n_generations,
        sigma_a2=sigma_a2,
        sigma_e2=sigma_e2,
        mean_phenotype=req.mean_phenotype,
        selection_proportion=req.selection_proportion,
        random_seed=req.random_seed,
    )

    rng = np.random.default_rng(cfg.random_seed)
    current_pop = create_founder_population(cfg, rng=rng)
    current_pop = assign_founder_traits(current_pop, cfg, rng=rng)

    n_dams_total = cfg.n_sires * cfg.dams_per_sire
    ne = effective_population_size(cfg.n_sires, n_dams_total)
    df_val = delta_inbreeding(ne)
    cum_f = 0.0

    records = []
    prev_mean_bv = None
    next_pred_gain = None

    for gen in range(cfg.n_generations + 1):
        h2_anova_dict = estimate_heritability_anova(current_pop)
        h2_est = float(h2_anova_dict["h2_est"])
        h2_true_val = float(true_heritability(current_pop))

        if active_strategy == "family_ebv":
            current_pop["ebv"] = family_ebv(current_pop, h2_est)
        else:
            current_pop["ebv"] = individual_ebv(current_pop, h2_est)

        mean_bv = float(current_pop["genetic_value"].mean())
        std_bv = float(current_pop["genetic_value"].std())
        mean_p = float(current_pop["phenotype"].mean())
        std_p = float(current_pop["phenotype"].std())

        if gen == 0:
            r_gain = 0.0
            p_gain = 0.0
        else:
            r_gain = float(realized_gain(mean_bv, prev_mean_bv))
            p_gain = float(next_pred_gain if next_pred_gain is not None else 0.0)
            cum_f = float(cumulative_inbreeding(cum_f, df_val))

        sel_males, sel_females, s_diff = truncation_select(
            current_pop, proportion=cfg.selection_proportion
        )
        next_pred_gain = float(predicted_gain(h2_est, s_diff))

        records.append({
            "generation": gen,
            "mean_phenotype": round(mean_p, 2),
            "std_phenotype": round(std_p, 2),
            "mean_bv": round(mean_bv, 2),
            "std_bv": round(std_bv, 2),
            "h2_anova": round(h2_est, 3),
            "h2_true": round(h2_true_val, 3),
            "selection_differential_S": round(float(s_diff), 2),
            "predicted_gain": round(p_gain, 2),
            "realized_gain": round(r_gain, 2),
            "cumulative_F": round(cum_f, 4),
            "Ne": round(ne, 1),
            "strategy": active_strategy,
        })

        if gen < cfg.n_generations:
            prev_mean_bv = mean_bv
            offspring_skel, parent_bv_map = nested_mating(
                sel_males, sel_females, generation=gen + 1, config=cfg, rng=rng
            )
            current_pop = assign_offspring_traits(
                offspring_skel, parent_bv_map, cfg, rng=rng
            )

    return records


@app.get("/")
def root():
    return {
        "service": "Insect Selective Breeding Simulation API",
        "status": "online",
        "docs_url": "/docs",
        "endpoints": {
            "health": "/api/health",
            "simulate": "/api/simulate",
            "compare": "/api/compare",
            "default_config": "/api/config",
        },
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "insect-breeding-api", "version": "1.0.0"}


@app.get("/api/config")
def get_default_config():
    return {
        "n_sires": 20,
        "dams_per_sire": 3,
        "offspring_per_dam": 20,
        "n_generations": 15,
        "mean_phenotype": 200.0,
        "target_h2": 0.30,
        "phenotypic_variance": 30.0,
        "selection_proportion": 0.20,
        "strategy": "individual_ebv",
        "random_seed": 42,
    }


@app.post("/api/simulate", response_model=SimulationResponse)
def simulate(req: SimulationRequest):
    try:
        records = run_simulation_engine(req)
        g0 = records[0]
        final = records[-1]
        gain = final["mean_bv"] - g0["mean_bv"]
        gain_pct = (gain / g0["mean_phenotype"]) * 100.0 if g0["mean_phenotype"] > 0 else 0.0

        f_val = final["cumulative_F"]
        status = "Safe (<10%)" if f_val < 0.10 else ("Warning (10-15%)" if f_val <= 0.15 else "Critical (>15%)")

        summary = SimulationSummary(
            initial_weight_mg=g0["mean_phenotype"],
            final_weight_mg=final["mean_phenotype"],
            total_genetic_gain_mg=round(gain, 2),
            gain_percentage=round(gain_pct, 1),
            final_inbreeding_F=f_val,
            effective_population_size_Ne=final["Ne"],
            final_h2_anova=final["h2_anova"],
            target_h2=req.target_h2,
            inbreeding_safety_status=status,
        )

        return SimulationResponse(summary=summary, generations=records)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare")
def compare_strategies(req: SimulationRequest):
    """Run both Individual EBV and Family EBV and return side-by-side data."""
    try:
        ind_records = run_simulation_engine(req, strategy="individual_ebv")
        fam_records = run_simulation_engine(req, strategy="family_ebv")

        ind_gain = ind_records[-1]["mean_bv"] - ind_records[0]["mean_bv"]
        fam_gain = fam_records[-1]["mean_bv"] - fam_records[0]["mean_bv"]

        return {
            "individual_ebv": {
                "total_gain_mg": round(ind_gain, 2),
                "final_inbreeding_F": ind_records[-1]["cumulative_F"],
                "records": ind_records,
            },
            "family_ebv": {
                "total_gain_mg": round(fam_gain, 2),
                "final_inbreeding_F": fam_records[-1]["cumulative_F"],
                "records": fam_records,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
