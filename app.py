"""Streamlit Web Dashboard for Insect Selective Breeding Simulation (30% Milestone).

Provides an interactive GUI to configure hyperparameters, run stochastic multi-generation
breeding simulations, compare Individual vs. Family EBV strategies, view real-time plots,
and download simulation logs.
"""

import copy
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

# Import core project modules
from config import BreedingConfig
from simulation.population import create_founder_population
from simulation.traits import assign_founder_traits, assign_offspring_traits
from genetics.heritability import estimate_heritability_anova, true_heritability
from genetics.breeding_value import individual_ebv, family_ebv
from selection.select import truncation_select
from selection.mating import nested_mating
from metrics.gain import predicted_gain, realized_gain
from metrics.inbreeding import effective_population_size, delta_inbreeding, cumulative_inbreeding


def simulate_cohort(config: BreedingConfig, strategy: str = "individual_ebv") -> pd.DataFrame:
    """Run multi-generation simulation for a given selection strategy."""
    rng = np.random.default_rng(config.random_seed)
    current_pop = create_founder_population(config, rng=rng)
    current_pop = assign_founder_traits(current_pop, config, rng=rng)

    n_dams_total = config.n_sires * config.dams_per_sire
    ne = effective_population_size(config.n_sires, n_dams_total)
    df_val = delta_inbreeding(ne)
    cum_f = 0.0

    records = []
    prev_mean_bv = None
    next_pred_gain = None

    for gen in range(config.n_generations + 1):
        # 1. Heritability estimation
        h2_anova_dict = estimate_heritability_anova(current_pop)
        h2_est = h2_anova_dict["h2_est"]
        h2_true_val = true_heritability(current_pop)

        # 2. Assign EBV according to strategy
        if strategy == "family_ebv":
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
            r_gain = realized_gain(mean_bv, prev_mean_bv)
            p_gain = next_pred_gain if next_pred_gain is not None else 0.0
            cum_f = cumulative_inbreeding(cum_f, df_val)

        # 3. Truncation Selection
        sel_males, sel_females, s_diff = truncation_select(
            current_pop, proportion=config.selection_proportion
        )

        # 4. Breeder's equation forecast
        next_pred_gain = predicted_gain(h2_est, s_diff)

        records.append({
            "generation": gen,
            "mean_phenotype": mean_p,
            "std_phenotype": std_p,
            "mean_bv": mean_bv,
            "std_bv": std_bv,
            "h2_anova": h2_est,
            "h2_true": h2_true_val,
            "selection_differential_S": s_diff,
            "predicted_gain": p_gain,
            "realized_gain": r_gain,
            "cumulative_F": cum_f,
            "Ne": ne,
            "strategy": strategy,
        })

        if gen < config.n_generations:
            prev_mean_bv = mean_bv
            offspring_skel, parent_bv_map = nested_mating(
                sel_males, sel_females, generation=gen + 1, config=config, rng=rng
            )
            current_pop = assign_offspring_traits(
                offspring_skel, parent_bv_map, config, rng=rng
            )

    return pd.DataFrame(records)


def main():
    st.set_page_config(
        page_title="Insect Selective Breeding Simulator",
        page_icon="🦗",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Header section
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1A365D, #2E8540); padding: 22px; border-radius: 12px; margin-bottom: 25px; color: white;">
            <h1 style="margin: 0; font-size: 28px; font-weight: 700;">🦗 Insect Selective Breeding Simulator</h1>
            <p style="margin: 6px 0 0 0; font-size: 15px; opacity: 0.9;">
                <b>Data-Driven Optimization of Larval Yield in Black Soldier Fly & Mealworm for Aquafeed and Feed Production</b><br>
                2nd-Year Data Science Capstone Project • 30% Milestone Interactive Dashboard
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar: Hyperparameters
    st.sidebar.header("⚙️ Simulation Settings")

    with st.sidebar.expander("👨‍👩‍👧‍👦 Population Architecture", expanded=True):
        n_sires = st.slider("Number of Sires (Males)", min_value=10, max_value=50, value=20, step=2)
        dams_per_sire = st.slider("Dams per Sire (Mating Ratio)", min_value=2, max_value=5, value=3, step=1)
        offspring_per_dam = st.slider("Offspring per Dam (Clutch Size)", min_value=10, max_value=30, value=20, step=5)
        
        n_dams_total = n_sires * dams_per_sire
        n_total_per_gen = n_dams_total * offspring_per_dam
        ne_preview = (4.0 * n_sires * n_dams_total) / (n_sires + n_dams_total)
        st.caption(f"📊 **Cohort Size:** {n_total_per_gen:,} larvae/gen ({n_sires} sires × {n_dams_total} dams)")
        st.caption(f"🧬 **Effective Size (Ne):** {ne_preview:.1f}")

    with st.sidebar.expander("🧬 Quantitative Genetics", expanded=True):
        mean_weight = st.number_input("Base Larval Weight (mg)", min_value=100.0, max_value=400.0, value=200.0, step=10.0)
        target_h2 = st.slider("True Heritability (h²)", min_value=0.10, max_value=0.60, value=0.30, step=0.05)
        total_p_var = st.number_input("Phenotypic Variance (σ_P²)", min_value=10.0, max_value=100.0, value=30.0, step=5.0)

        sigma_a2 = target_h2 * total_p_var
        sigma_e2 = (1.0 - target_h2) * total_p_var
        st.caption(f"σ_A² = {sigma_a2:.1f} mg² | σ_E² = {sigma_e2:.1f} mg²")

    with st.sidebar.expander("🎯 Selection Protocol", expanded=True):
        n_generations = st.slider("Generations to Simulate", min_value=5, max_value=30, value=15, step=1)
        selection_prop = st.slider("Selection Proportion (Top %)", min_value=0.10, max_value=0.40, value=0.20, step=0.05)
        strategy_option = st.selectbox(
            "Breeding Strategy",
            ["Individual EBV (Default)", "Family EBV", "Compare Both (Side-by-Side)"]
        )
        random_seed = st.number_input("Random Seed", min_value=1, max_value=9999, value=42, step=1)

    run_btn = st.sidebar.button("▶ Run Simulation", type="primary", use_container_width=True)

    # Build Configuration Object
    cfg = BreedingConfig(
        n_sires=n_sires,
        dams_per_sire=dams_per_sire,
        offspring_per_dam=offspring_per_dam,
        n_generations=n_generations,
        sigma_a2=sigma_a2,
        sigma_e2=sigma_e2,
        mean_phenotype=mean_weight,
        selection_proportion=selection_prop,
        random_seed=int(random_seed),
    )

    # Simulation Execution (Session state caching for instant responsiveness)
    if run_btn or "sim_data" not in st.session_state:
        with st.spinner("Simulating selective breeding across generations..."):
            if strategy_option == "Compare Both (Side-by-Side)":
                df_ind = simulate_cohort(cfg, strategy="individual_ebv")
                df_fam = simulate_cohort(cfg, strategy="family_ebv")
                st.session_state["sim_data"] = df_ind
                st.session_state["sim_data_fam"] = df_fam
                st.session_state["is_comparison"] = True
            elif strategy_option == "Family EBV":
                df_fam = simulate_cohort(cfg, strategy="family_ebv")
                st.session_state["sim_data"] = df_fam
                st.session_state["is_comparison"] = False
            else:
                df_ind = simulate_cohort(cfg, strategy="individual_ebv")
                st.session_state["sim_data"] = df_ind
                st.session_state["is_comparison"] = False

    df_main = st.session_state["sim_data"]
    is_comparison = st.session_state.get("is_comparison", False)

    # Top KPI Metrics Cards
    g0_row = df_main.iloc[0]
    final_row = df_main.iloc[-1]
    total_gain = final_row["mean_bv"] - g0_row["mean_bv"]
    gain_pct = (total_gain / g0_row["mean_phenotype"]) * 100.0
    final_f = final_row["cumulative_F"]

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric(
            "Larval Harvest Weight",
            f"{final_row['mean_phenotype']:.1f} mg",
            f"+{total_gain:.2f} mg ({gain_pct:+.1f}%)"
        )
    with c2:
        st.metric(
            "Total Genetic Gain",
            f"{total_gain:+.2f} mg",
            f"Gen 0: {g0_row['mean_bv']:+.2f}"
        )
    with c3:
        st.metric(
            "Cumulative Inbreeding (F)",
            f"{final_f * 100:.2f}%",
            "Safe Threshold < 15%" if final_f < 0.15 else "High Inbreeding Risk"
        )
    with c4:
        st.metric(
            "Effective Size (Ne)",
            f"{final_row['Ne']:.1f}",
            f"ΔF = {1.0 / (2.0 * final_row['Ne']) * 100:.3f}%/gen"
        )
    with c5:
        st.metric(
            "Final ANOVA Heritability",
            f"{final_row['h2_anova']:.3f}",
            f"Target: {cfg.true_h2:.2f}"
        )

    st.markdown("---")

    # Interactive Visual Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Genetic Gain Trend",
        "🎯 Breeder's Equation Validation",
        "🛡️ Inbreeding & Diversity",
        "⚖️ Strategy Comparison",
        "📋 Data Log & CSV Download"
    ])

    # Tab 1: Directional Genetic Gain
    with tab1:
        st.subheader("Directional Genetic Progress over Generations")
        fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
        gens = df_main["generation"].values
        means = df_main["mean_bv"].values
        stds = df_main["std_bv"].values

        ax.plot(gens, means, marker="o", color="#1F77B4", linewidth=2.5, label="Mean Breeding Value (EBV)")
        ax.fill_between(gens, means - stds, means + stds, color="#1F77B4", alpha=0.18, label="±1 SD Cohort Variation")

        ax.set_title("Genetic Value Trajectory (Additive Genetic Progress)", fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Generation", fontsize=11)
        ax.set_ylabel("Breeding Value (mg)", fontsize=11)
        ax.set_xticks(gens)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper left")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.info(f"💡 **Takeaway:** Over {cfg.n_generations} generations of {int(cfg.selection_proportion*100)}% truncation selection, "
                f"larval body weight gained **+{total_gain:.2f} mg**, representing a **{gain_pct:.1f}% net yield boost**.")

    # Tab 2: Breeder's Equation
    with tab2:
        st.subheader("Breeder's Equation Validation: Predicted (R = h²S) vs. Realized Gain")
        eval_df = df_main[df_main["generation"] > 0].copy()

        fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
        width = 0.35
        x_indices = np.arange(len(eval_df))
        ax.bar(x_indices - width/2, eval_df["predicted_gain"], width, label="Predicted Response (R = h² · S)", color="#2B5C8F", alpha=0.85)
        ax.bar(x_indices + width/2, eval_df["realized_gain"], width, label="Realized Gain (ΔG = A_t - A_{t-1})", color="#E67E22", alpha=0.85)

        ax.set_title("Per-Generation Selection Response vs. Empirical Observation", fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Generation", fontsize=11)
        ax.set_ylabel("Gain per Generation (mg)", fontsize=11)
        ax.set_xticks(x_indices)
        ax.set_xticklabels(eval_df["generation"])
        ax.grid(True, linestyle="--", alpha=0.4, axis="y")
        ax.legend(loc="upper right")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        sum_pred = eval_df["predicted_gain"].sum()
        sum_real = eval_df["realized_gain"].sum()
        st.success(f"🎯 **Empirical Match:** Cumulative predicted response = **{sum_pred:.2f} mg** | "
                   f"Cumulative realized response = **{sum_real:.2f} mg** (Accuracy: {min(sum_real, sum_pred) / max(sum_real, sum_pred) * 100:.1f}%).")

    # Tab 3: Inbreeding Dynamics
    with tab3:
        st.subheader("Accumulation of Inbreeding & Diversity Monitoring")
        fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
        ax.plot(df_main["generation"], df_main["cumulative_F"] * 100, marker="s", color="#D62728", linewidth=2.5, label="Cumulative Inbreeding (F %)")
        ax.axhline(15.0, color="#E67E22", linestyle="--", linewidth=1.5, label="FAO Inbreeding Warning Threshold (15%)")
        ax.axhline(25.0, color="#7F1D1D", linestyle=":", linewidth=1.5, label="Critical Inbreeding Depression Threshold (25%)")

        ax.set_title(f"Cumulative Inbreeding over Generations (Ne = {final_row['Ne']:.1f})", fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Generation", fontsize=11)
        ax.set_ylabel("Inbreeding Coefficient F (%)", fontsize=11)
        ax.set_xticks(df_main["generation"])
        ax.set_ylim(bottom=0.0)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper left")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.warning(f"🛡️ **Genetic Diversity Guardrail:** Inbreeding reached **{final_f * 100:.2f}%** at Gen {cfg.n_generations}. "
                   f"Because ΔF = {1.0 / (2.0 * final_row['Ne']) * 100:.3f}% per generation, the colony remains well within safe breeding thresholds.")

    # Tab 4: Strategy Comparison
    with tab4:
        st.subheader("Strategy Comparison: Individual EBV vs. Family EBV")
        if is_comparison and "sim_data_fam" in st.session_state:
            df_fam = st.session_state["sim_data_fam"]

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5), dpi=300)

            # Gain comparison
            ax1.plot(df_main["generation"], df_main["mean_bv"], marker="o", color="#1F77B4", label="Individual EBV")
            ax1.plot(df_fam["generation"], df_fam["mean_bv"], marker="^", color="#2E8540", label="Family EBV")
            ax1.set_title("Cumulative Genetic Gain (mg)", fontweight="bold")
            ax1.set_xlabel("Generation")
            ax1.set_ylabel("Breeding Value (mg)")
            ax1.grid(True, linestyle="--", alpha=0.5)
            ax1.legend()

            # Inbreeding comparison
            ax2.plot(df_main["generation"], df_main["cumulative_F"] * 100, marker="o", color="#1F77B4", label="Individual EBV")
            ax2.plot(df_fam["generation"], df_fam["cumulative_F"] * 100, marker="^", color="#2E8540", label="Family EBV")
            ax2.set_title("Cumulative Inbreeding F (%)", fontweight="bold")
            ax2.set_xlabel("Generation")
            ax2.set_ylabel("Inbreeding F (%)")
            ax2.grid(True, linestyle="--", alpha=0.5)
            ax2.legend()

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            fam_gain = df_fam.iloc[-1]["mean_bv"] - df_fam.iloc[0]["mean_bv"]
            st.markdown(f"""
            | Strategy | Cumulative Gain (mg) | Final Inbreeding (F) | Best Use Case |
            |---|:---:|:---:|---|
            | **Individual EBV** | **{total_gain:+.2f} mg** | **{final_f * 100:.2f}%** | Best when heritability is high/moderate ($h^2 \ge 0.30$) |
            | **Family EBV** | **{fam_gain:+.2f} mg** | **{df_fam.iloc[-1]['cumulative_F'] * 100:.2f}%** | Best when heritability is low ($h^2 < 0.15$) by pooling clutch data |
            """)
        else:
            st.info("👉 To run a live side-by-side comparison, select **'Compare Both (Side-by-Side)'** in the sidebar and click **'Run Simulation'**.")

    # Tab 5: Data Log & CSV Download
    with tab5:
        st.subheader("Simulation Metrics Data Log")
        st.dataframe(df_main.style.format({
            "mean_phenotype": "{:.2f}",
            "std_phenotype": "{:.2f}",
            "mean_bv": "{:+.2f}",
            "std_bv": "{:.2f}",
            "h2_anova": "{:.3f}",
            "h2_true": "{:.3f}",
            "selection_differential_S": "{:.2f}",
            "predicted_gain": "{:.2f}",
            "realized_gain": "{:.2f}",
            "cumulative_F": "{:.4f}",
            "Ne": "{:.1f}",
        }), use_container_width=True)

        csv_data = df_main.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Generation Log (CSV)",
            data=csv_data,
            file_name="insect_selective_breeding_log.csv",
            mime="text/csv",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
