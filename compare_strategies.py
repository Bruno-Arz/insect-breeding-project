"""Comparative evaluation script: Individual EBV vs. Family EBV Selection (30% Milestone).

Executes both breeding strategies under identical founder genetics and compares:
1. Rate and magnitude of realized genetic gain (mg).
2. Accumulation of inbreeding (F) and effective population dynamics.
3. Heritability trajectory over 15 generations.
Outputs publication-quality comparison plots to output/strategy_comparison.png.
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import BreedingConfig
from app import simulate_cohort

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_strategy_benchmark():
    cfg = BreedingConfig(
        n_sires=20,
        dams_per_sire=3,
        offspring_per_dam=20,
        n_generations=15,
        sigma_a2=9.0,
        sigma_e2=21.0,
        mean_phenotype=200.0,
        selection_proportion=0.20,
        random_seed=42,
    )

    print("=" * 75)
    print("  STRATEGY BENCHMARK: INDIVIDUAL EBV vs. FULL-SIB FAMILY EBV")
    print("=" * 75)
    print(f"Population: {cfg.n_sires} sires x {cfg.dams_per_sire} dams x {cfg.offspring_per_dam} offspring = {cfg.total_offspring_per_gen} larvae/gen")
    print(f"Base Weight: {cfg.mean_phenotype:.1f} mg | True h^2: {cfg.true_h2:.2f} | Selection: Top {int(cfg.selection_proportion*100)}%")
    print("-" * 75)

    print("Running Strategy 1: Individual EBV Selection...")
    df_ind = simulate_cohort(cfg, strategy="individual_ebv")

    print("Running Strategy 2: Full-Sib Family EBV Selection...")
    df_fam = simulate_cohort(cfg, strategy="family_ebv")

    # Metrics Summary
    ind_g0 = df_ind.iloc[0]
    ind_f15 = df_ind.iloc[-1]
    ind_gain = ind_f15["mean_bv"] - ind_g0["mean_bv"]

    fam_g0 = df_fam.iloc[0]
    fam_f15 = df_fam.iloc[-1]
    fam_gain = fam_f15["mean_bv"] - fam_g0["mean_bv"]

    summary_df = pd.DataFrame([
        {
            "Strategy": "Individual EBV",
            "Initial Weight (mg)": round(ind_g0["mean_phenotype"], 2),
            "Final Weight (mg)": round(ind_f15["mean_phenotype"], 2),
            "Cumulative Gain (mg)": round(ind_gain, 2),
            "Gain Boost (%)": round((ind_gain / ind_g0["mean_phenotype"]) * 100, 1),
            "Final Inbreeding F (%)": round(ind_f15["cumulative_F"] * 100, 2),
            "Ne": round(ind_f15["Ne"], 1),
            "Final ANOVA h^2": round(ind_f15["h2_anova"], 3),
        },
        {
            "Strategy": "Family EBV",
            "Initial Weight (mg)": round(fam_g0["mean_phenotype"], 2),
            "Final Weight (mg)": round(fam_f15["mean_phenotype"], 2),
            "Cumulative Gain (mg)": round(fam_gain, 2),
            "Gain Boost (%)": round((fam_gain / fam_g0["mean_phenotype"]) * 100, 1),
            "Final Inbreeding F (%)": round(fam_f15["cumulative_F"] * 100, 2),
            "Ne": round(fam_f15["Ne"], 1),
            "Final ANOVA h^2": round(fam_f15["h2_anova"], 3),
        }
    ])

    summary_csv = OUTPUT_DIR / "strategy_comparison_summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    print(f"\nSaved strategy summary to: {summary_csv}")
    print(summary_df.to_string(index=False))

    # Comparative Visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 9), dpi=300)

    gens = df_ind["generation"].values

    # 1. Genetic Gain Trajectory
    ax1.plot(gens, df_ind["mean_bv"], marker="o", color="#1F77B4", linewidth=2.2, label=f"Individual EBV (+{ind_gain:.1f} mg)")
    ax1.plot(gens, df_fam["mean_bv"], marker="s", color="#2E8540", linewidth=2.2, label=f"Family EBV (+{fam_gain:.1f} mg)")
    ax1.set_title("1. Cumulative Genetic Gain (Additive Breeding Value)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Generation")
    ax1.set_ylabel("Breeding Value (mg)")
    ax1.set_xticks(gens)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper left")

    # 2. Cumulative Inbreeding Accumulation
    ax2.plot(gens, df_ind["cumulative_F"] * 100, marker="o", color="#1F77B4", linewidth=2.2, label="Individual EBV")
    ax2.plot(gens, df_fam["cumulative_F"] * 100, marker="s", color="#D62728", linewidth=2.2, label="Family EBV")
    ax2.axhline(15.0, color="#E67E22", linestyle="--", linewidth=1.5, label="FAO Warning Threshold (15%)")
    ax2.set_title("2. Inbreeding Accumulation (Diversity Degradation)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Generation")
    ax2.set_ylabel("Inbreeding F (%)")
    ax2.set_xticks(gens)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper left")

    # 3. Phenotypic Harvest Weight Progression
    ax3.plot(gens, df_ind["mean_phenotype"], marker="o", color="#1F77B4", linewidth=2.2, label="Individual EBV")
    ax3.plot(gens, df_fam["mean_phenotype"], marker="s", color="#2E8540", linewidth=2.2, label="Family EBV")
    ax3.set_title("3. Larval Harvest Weight Progression (mg)", fontsize=11, fontweight="bold")
    ax3.set_xlabel("Generation")
    ax3.set_ylabel("Harvest Weight (mg)")
    ax3.set_xticks(gens)
    ax3.grid(True, linestyle="--", alpha=0.5)
    ax3.legend(loc="upper left")

    # 4. Trade-off Matrix (Gain vs. Inbreeding)
    strategies = ["Individual EBV", "Family EBV"]
    gains = [ind_gain, fam_gain]
    inbreedings = [ind_f15["cumulative_F"] * 100, fam_f15["cumulative_F"] * 100]

    x = np.arange(len(strategies))
    w = 0.35
    ax4.bar(x - w/2, gains, w, label="Genetic Gain (mg)", color="#1F77B4", alpha=0.85)
    ax4.bar(x + w/2, inbreedings, w, label="Inbreeding F (%)", color="#D62728", alpha=0.85)
    ax4.set_title("4. Trade-off Matrix: Progress vs. Inbreeding Risk", fontsize=11, fontweight="bold")
    ax4.set_xticks(x)
    ax4.set_xticklabels(strategies, fontweight="bold")
    ax4.grid(True, linestyle="--", alpha=0.4, axis="y")
    ax4.legend(loc="upper right")

    plt.tight_layout()
    plot_path = OUTPUT_DIR / "strategy_comparison.png"
    fig.savefig(plot_path, dpi=300)
    plt.close(fig)
    print(f"Saved 4-panel comparison plot to: {plot_path}")
    print("=" * 75)


if __name__ == "__main__":
    run_strategy_benchmark()
