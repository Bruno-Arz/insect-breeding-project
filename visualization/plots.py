"""
Plotting module using matplotlib.
Saves 3 PNG figures:
1. mean_bv_vs_generation.png
2. cumulative_inbreeding.png
3. predicted_vs_realized_gain.png
"""
import os
import pandas as pd
import matplotlib.pyplot as plt

def generate_plots(log_df: pd.DataFrame, output_dir: str):
    """
    Generates and saves three validation plots.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Mean Breeding Value vs Generation
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(log_df["generation"], log_df["mean_bv"], marker="o", color="#1f77b4", linewidth=2, label="Mean Genetic Value (A)")
    ax.fill_between(log_df["generation"], log_df["mean_bv"] - log_df["std_bv"], log_df["mean_bv"] + log_df["std_bv"], color="#1f77b4", alpha=0.2, label="+/- 1 Std Dev")
    ax.set_title("Larval Body Weight: Mean Breeding Value vs Generation", fontsize=12, fontweight="bold")
    ax.set_xlabel("Generation", fontsize=10)
    ax.set_ylabel("Breeding Value (mg deviation)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper left")
    fig.tight_layout()
    plot1_path = os.path.join(output_dir, "mean_bv_vs_generation.png")
    fig.savefig(plot1_path, dpi=150)
    plt.close(fig)
    
    # 2. Cumulative Inbreeding F vs Generation
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(log_df["generation"], log_df["cumulative_F"], marker="s", color="#d62728", linewidth=2, label="Cumulative Inbreeding (F)")
    ax.set_title("Cumulative Inbreeding Coefficient (F) vs Generation", fontsize=12, fontweight="bold")
    ax.set_xlabel("Generation", fontsize=10)
    ax.set_ylabel("Inbreeding Coefficient (F)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper left")
    fig.tight_layout()
    plot2_path = os.path.join(output_dir, "cumulative_inbreeding.png")
    fig.savefig(plot2_path, dpi=150)
    plt.close(fig)
    
    # 3. Predicted vs Realized Gain per Generation
    fig, ax = plt.subplots(figsize=(8, 5))
    # Generation > 0 has both predicted and realized gain
    gain_df = log_df[log_df["generation"] > 0]
    ax.plot(gain_df["generation"], gain_df["predicted_gain"], marker="^", linestyle="--", color="#ff7f0e", linewidth=2, label="Predicted Gain (R = h^2 * S)")
    ax.plot(gain_df["generation"], gain_df["realized_gain"], marker="o", linestyle="-", color="#2ca02c", linewidth=2, label="Realized Gain (Observed ΔBV)")
    ax.set_title("Predicted vs Realized Genetic Gain per Generation", fontsize=12, fontweight="bold")
    ax.set_xlabel("Generation", fontsize=10)
    ax.set_ylabel("Gain in Larval Weight (mg)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper right")
    fig.tight_layout()
    plot3_path = os.path.join(output_dir, "predicted_vs_realized_gain.png")
    fig.savefig(plot3_path, dpi=150)
    plt.close(fig)
    
    return [plot1_path, plot2_path, plot3_path]
