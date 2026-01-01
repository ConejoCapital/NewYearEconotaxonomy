"""
Generate reports and visualizations from simulation results.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional


def load_results(run_file: str, summary_file: Optional[str] = None) -> tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Load simulation results from parquet and CSV files.
    
    Parameters:
    -----------
    run_file : str
        Path to run parquet file
    summary_file : str, optional
        Path to summary CSV file
    
    Returns:
    --------
    tuple[pd.DataFrame, Optional[pd.DataFrame]]
        (firms_df, summary_df)
    """
    firms_df = pd.read_parquet(run_file)
    summary_df = None
    if summary_file:
        summary_df = pd.read_csv(summary_file)
    return firms_df, summary_df


def generate_text_report(summary_df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """
    Generate a text report from summary statistics.
    
    Parameters:
    -----------
    summary_df : pd.DataFrame
        Summary DataFrame from simulation
    output_path : str, optional
        Path to save report. If None, returns string only.
    
    Returns:
    --------
    str
        Report text
    """
    total_row = summary_df[summary_df["level"] == "total"].iloc[0]
    sector_rows = summary_df[summary_df["level"] == "sector"].copy()
    
    report_lines = [
        "=" * 80,
        "REPORTE DE SIMULACIÓN ECONÓMICA - 1-2 ENERO 2026",
        "=" * 80,
        "",
        f"Total de empresas simuladas: {int(total_row['n_firms']):,}",
        "",
        "--- DECISIONES DÍA FERIADO (1 de enero) ---",
        f"  Cerrar: {total_row['share_close']*100:.2f}%",
        f"  Abrir con descanso sustitutorio: {total_row['share_open_sub']*100:.2f}%",
        f"  Abrir sin descanso sustitutorio (3x): {total_row['share_open_no']*100:.2f}%",
        "",
        "--- DECISIONES DÍA NO LABORABLE (2 de enero) ---",
        f"  Operar normalmente: {total_row['share_operate']*100:.2f}%",
        f"  Adoptar día no laborable: {total_row['share_adopt_bridge']*100:.2f}%",
        "",
        "--- RESULTADOS FINANCIEROS ---",
        f"Ventas totales (1-2 enero): S/ {total_row['total_sales_combined']:,.2f}",
        f"  - Día 1 (feriado): S/ {total_row['total_sales_holiday']:,.2f}",
        f"  - Día 2 (bridge): S/ {total_row['total_sales_bridge']:,.2f}",
        "",
        f"Costos laborales totales (1-2 enero): S/ {total_row['total_labor_cost_combined']:,.2f}",
        f"  - Día 1 (feriado): S/ {total_row['total_labor_cost_holiday']:,.2f}",
        f"  - Día 2 (bridge): S/ {total_row['total_labor_cost_bridge']:,.2f}",
        "",
        f"Utilidad total (1-2 enero): S/ {total_row['total_profit_combined']:,.2f}",
        f"  - Día 1 (feriado): S/ {total_row['total_profit_holiday']:,.2f}",
        f"  - Día 2 (bridge): S/ {total_row['total_profit_bridge']:,.2f}",
        "",
        "--- POR SECTOR ---",
        ""
    ]
    
    for _, row in sector_rows.iterrows():
        report_lines.extend([
            f"Sector: {row['sector'].upper()}",
            f"  N empresas: {int(row['n_firms'])}",
            f"  Feriado - Cerrar: {row['share_close']*100:.2f}% | "
            f"Con descanso: {row['share_open_sub']*100:.2f}% | "
            f"Sin descanso (3x): {row['share_open_no']*100:.2f}%",
            f"  Bridge - Operar: {row['share_operate']*100:.2f}% | "
            f"Adoptar: {row['share_adopt_bridge']*100:.2f}%",
            f"  Ventas totales: S/ {row['total_sales_combined']:,.2f}",
            f"  Utilidad promedio: S/ {row['mean_profit_combined']:,.2f}",
            ""
        ])
    
    report_lines.append("=" * 80)
    
    report_text = "\n".join(report_lines)
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_text)
    
    return report_text


def plot_decisions_by_sector(firms_df: pd.DataFrame, output_path: Optional[str] = None):
    """
    Create bar plots showing decision shares by sector.
    
    Parameters:
    -----------
    firms_df : pd.DataFrame
        Firms DataFrame with action_holiday and action_bridge columns
    output_path : str, optional
        Path to save figure. If None, displays instead.
    """
    sectors = firms_df["sector"].unique()
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Holiday decisions
    holiday_data = []
    for sector in sectors:
        mask = firms_df["sector"] == sector
        if mask.sum() == 0:
            continue
        sector_df = firms_df[mask]
        holiday_data.append({
            "sector": sector,
            "close": (sector_df["action_holiday"] == "close").mean(),
            "open_sub": (sector_df["action_holiday"] == "open_sub").mean(),
            "open_no": (sector_df["action_holiday"] == "open_no").mean(),
        })
    
    holiday_df = pd.DataFrame(holiday_data)
    holiday_df.set_index("sector")[["close", "open_sub", "open_no"]].plot(
        kind="bar", stacked=True, ax=axes[0], 
        color=["#d62728", "#2ca02c", "#1f77b4"]
    )
    axes[0].set_title("Decisiones Día Feriado (1 enero)", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("Proporción")
    axes[0].set_xlabel("Sector")
    axes[0].legend(["Cerrar", "Abrir con descanso", "Abrir sin descanso (3x)"])
    axes[0].tick_params(axis="x", rotation=45)
    
    # Bridge decisions
    bridge_data = []
    for sector in sectors:
        mask = firms_df["sector"] == sector
        if mask.sum() == 0:
            continue
        sector_df = firms_df[mask]
        bridge_data.append({
            "sector": sector,
            "operate": (sector_df["action_bridge"] == "operate").mean(),
            "adopt_bridge": (sector_df["action_bridge"] == "adopt_bridge").mean(),
        })
    
    bridge_df = pd.DataFrame(bridge_data)
    bridge_df.set_index("sector")[["operate", "adopt_bridge"]].plot(
        kind="bar", stacked=True, ax=axes[1],
        color=["#2ca02c", "#d62728"]
    )
    axes[1].set_title("Decisiones Día No Laborable (2 enero)", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Proporción")
    axes[1].set_xlabel("Sector")
    axes[1].legend(["Operar", "Adoptar día no laborable"])
    axes[1].tick_params(axis="x", rotation=45)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
    else:
        plt.show()
    
    plt.close()


if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 1:
        run_file = sys.argv[1]
        summary_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        firms_df, summary_df = load_results(run_file, summary_file)
        
        if summary_df is not None:
            report = generate_text_report(summary_df)
            print(report)
        
        plot_decisions_by_sector(firms_df, "outputs/decisions_by_sector.png")

