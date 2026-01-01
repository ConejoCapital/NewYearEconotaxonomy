"""
Main simulation runner for the economic model.

Orchestrates the full simulation: firm generation, demand computation,
decision making, and output generation.
"""

import json
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from generate_firms import generate_firms
from demand import compute_day_sales_and_costs
from decisions import decide_holiday, decide_bridge


def load_params(params_path: str = "data/params.json") -> Dict[str, Any]:
    """Load parameters from JSON file."""
    with open(params_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_calendar(calendar_path: str = "data/calendar_2026.csv") -> pd.DataFrame:
    """Load calendar with day types."""
    return pd.read_csv(calendar_path, parse_dates=["date"])


def cfg_hash(cfg: Dict[str, Any]) -> str:
    """
    Compute hash of configuration for traceability.
    
    Parameters:
    -----------
    cfg : dict
        Configuration dictionary
    
    Returns:
    --------
    str
        First 12 characters of SHA256 hash
    """
    s = json.dumps(cfg, sort_keys=True).encode()
    return hashlib.sha256(s).hexdigest()[:12]


def run(
    seed: Optional[int] = None,
    params_path: str = "data/params.json",
    calendar_path: str = "data/calendar_2026.csv",
    output_dir: str = "outputs/runs"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run the complete simulation.
    
    Parameters:
    -----------
    seed : int, optional
        Random seed. If None, uses seed from params.json
    params_path : str
        Path to parameters JSON file
    calendar_path : str
        Path to calendar CSV file
    output_dir : str
        Directory to save outputs
    
    Returns:
    --------
    tuple[pd.DataFrame, pd.DataFrame]
        (firms_df_with_decisions, summary_df)
    """
    # Load inputs
    params = load_params(params_path)
    calendar = load_calendar(calendar_path)
    
    # Use seed from params if not provided
    if seed is None:
        seed = params["run"]["seed"]
    
    num_firms = params["run"]["num_firms"]
    
    print(f"Starting simulation with {num_firms} firms (seed={seed})")
    
    # Step 1: Generate firms
    print("Step 1: Generating synthetic firms...")
    firms_df = generate_firms(num_firms, params, seed=seed)
    
    # Step 2: Process each day
    # Day 1: Holiday (2026-01-01)
    print("Step 2a: Processing holiday (Jan 1)...")
    firms_df = compute_day_sales_and_costs(firms_df, "holiday", params)
    firms_df = decide_holiday(firms_df, params)
    
    # Rename R_t, C_t for day 1
    firms_df = firms_df.rename(columns={
        "R_t": "R_1",
        "C_t": "C_1"
    })
    
    # Day 2: Bridge (2026-01-02)
    print("Step 2b: Processing bridge day (Jan 2)...")
    firms_df = compute_day_sales_and_costs(firms_df, "bridge", params)
    firms_df = decide_bridge(firms_df, params)
    
    # Rename R_t, C_t for day 2
    firms_df = firms_df.rename(columns={
        "R_t": "R_2",
        "C_t": "C_2"
    })
    
    # Step 3: Compute aggregates and summary
    print("Step 3: Computing aggregates...")
    summary_df = compute_summary(firms_df, params)
    
    # Step 4: Save outputs
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_filename = f"run_{timestamp}_seed{seed}.parquet"
    summary_filename = f"summary_{timestamp}_seed{seed}.csv"
    
    firms_df.to_parquet(output_path / run_filename, index=False)
    summary_df.to_csv(output_path / summary_filename, index=False)
    
    print(f"Outputs saved:")
    print(f"  - {output_path / run_filename}")
    print(f"  - {output_path / summary_filename}")
    
    return firms_df, summary_df


def compute_summary(firms_df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Compute summary statistics by sector and overall.
    
    Returns:
    --------
    pd.DataFrame
        Summary table with metrics by sector and total
    """
    sectors = params["sectors"]
    
    summary_rows = []
    
    # Overall summary
    summary_rows.append({
        "level": "total",
        "sector": "all",
        "n_firms": len(firms_df),
        # Holiday actions
        "share_close": (firms_df["action_holiday"] == "close").mean(),
        "share_open_sub": (firms_df["action_holiday"] == "open_sub").mean(),
        "share_open_no": (firms_df["action_holiday"] == "open_no").mean(),
        # Bridge actions
        "share_operate": (firms_df["action_bridge"] == "operate").mean(),
        "share_adopt_bridge": (firms_df["action_bridge"] == "adopt_bridge").mean(),
        # Holiday totals
        "total_sales_holiday": firms_df["R_1"].sum(),
        "total_labor_cost_holiday": firms_df["labor_cost_holiday"].sum(),
        "total_profit_holiday": firms_df["profit_holiday"].sum(),
        "mean_profit_holiday": firms_df["profit_holiday"].mean(),
        "median_profit_holiday": firms_df["profit_holiday"].median(),
        # Bridge totals
        "total_sales_bridge": firms_df["R_2"].sum(),
        "total_labor_cost_bridge": firms_df["labor_cost_bridge"].sum(),
        "total_profit_bridge": firms_df["profit_bridge"].sum(),
        "mean_profit_bridge": firms_df["profit_bridge"].mean(),
        "median_profit_bridge": firms_df["profit_bridge"].median(),
        # Combined
        "total_sales_combined": firms_df["R_1"].sum() + firms_df["R_2"].sum(),
        "total_labor_cost_combined": firms_df["labor_cost_holiday"].sum() + firms_df["labor_cost_bridge"].sum(),
        "total_profit_combined": firms_df["profit_holiday"].sum() + firms_df["profit_bridge"].sum(),
        "mean_profit_combined": (firms_df["profit_holiday"] + firms_df["profit_bridge"]).mean(),
        "median_profit_combined": (firms_df["profit_holiday"] + firms_df["profit_bridge"]).median(),
    })
    
    # By sector
    for sector in sectors:
        mask = firms_df["sector"] == sector
        if mask.sum() == 0:
            continue
        
        sector_df = firms_df[mask]
        summary_rows.append({
            "level": "sector",
            "sector": sector,
            "n_firms": mask.sum(),
            # Holiday actions
            "share_close": (sector_df["action_holiday"] == "close").mean(),
            "share_open_sub": (sector_df["action_holiday"] == "open_sub").mean(),
            "share_open_no": (sector_df["action_holiday"] == "open_no").mean(),
            # Bridge actions
            "share_operate": (sector_df["action_bridge"] == "operate").mean(),
            "share_adopt_bridge": (sector_df["action_bridge"] == "adopt_bridge").mean(),
            # Holiday totals
            "total_sales_holiday": sector_df["R_1"].sum(),
            "total_labor_cost_holiday": sector_df["labor_cost_holiday"].sum(),
            "total_profit_holiday": sector_df["profit_holiday"].sum(),
            "mean_profit_holiday": sector_df["profit_holiday"].mean(),
            "median_profit_holiday": sector_df["profit_holiday"].median(),
            # Bridge totals
            "total_sales_bridge": sector_df["R_2"].sum(),
            "total_labor_cost_bridge": sector_df["labor_cost_bridge"].sum(),
            "total_profit_bridge": sector_df["profit_bridge"].sum(),
            "mean_profit_bridge": sector_df["profit_bridge"].mean(),
            "median_profit_bridge": sector_df["profit_bridge"].median(),
            # Combined
            "total_sales_combined": sector_df["R_1"].sum() + sector_df["R_2"].sum(),
            "total_labor_cost_combined": sector_df["labor_cost_holiday"].sum() + sector_df["labor_cost_bridge"].sum(),
            "total_profit_combined": sector_df["profit_holiday"].sum() + sector_df["profit_bridge"].sum(),
            "mean_profit_combined": (sector_df["profit_holiday"] + sector_df["profit_bridge"]).mean(),
            "median_profit_combined": (sector_df["profit_holiday"] + sector_df["profit_bridge"]).median(),
        })
    
    return pd.DataFrame(summary_rows)


def run_once(seed: int, config: Dict[str, Any], silent: bool = True) -> Dict[str, Any]:
    """
    Run a single simulation and return flat dictionary of aggregated metrics.
    
    This function is designed for batch runs with multiple seeds and scenarios.
    It does not save files, only returns metrics.
    
    Parameters:
    -----------
    seed : int
        Random seed for reproducibility
    config : dict
        Configuration dictionary (same format as params.json)
    silent : bool
        If True, suppress print statements
    
    Returns:
    --------
    dict
        Flat dictionary with all metrics (totals and by sector)
    """
    # Ensure seed is set in config for consistency
    config_copy = config.copy()
    config_copy["run"] = config_copy.get("run", {}).copy()
    config_copy["run"]["seed"] = seed
    
    num_firms = config_copy["run"]["num_firms"]
    
    if not silent:
        print(f"Running simulation: seed={seed}, firms={num_firms}")
    
    # Step 1: Generate firms
    firms_df = generate_firms(num_firms, config_copy, seed=seed)
    
    # Step 2: Process holiday day
    firms_df = compute_day_sales_and_costs(firms_df, "holiday", config_copy)
    firms_df = decide_holiday(firms_df, config_copy)
    firms_df = firms_df.rename(columns={"R_t": "R_1", "C_t": "C_1"})
    
    # Step 3: Process bridge day
    firms_df = compute_day_sales_and_costs(firms_df, "bridge", config_copy)
    firms_df = decide_bridge(firms_df, config_copy)
    firms_df = firms_df.rename(columns={"R_t": "R_2", "C_t": "C_2"})
    
    # Step 4: Compute metrics
    metrics = {}
    
    # Overall totals
    metrics["n_firms_total"] = len(firms_df)
    metrics["share_close_holiday_total"] = (firms_df["action_holiday"] == "close").mean()
    metrics["share_open_sub_holiday_total"] = (firms_df["action_holiday"] == "open_sub").mean()
    metrics["share_open_no_holiday_total"] = (firms_df["action_holiday"] == "open_no").mean()
    metrics["share_operate_bridge_total"] = (firms_df["action_bridge"] == "operate").mean()
    metrics["share_adopt_bridge_total"] = (firms_df["action_bridge"] == "adopt_bridge").mean()
    
    metrics["profit_day1_total"] = firms_df["profit_holiday"].sum()
    metrics["profit_day2_total"] = firms_df["profit_bridge"].sum()
    metrics["profit_total"] = metrics["profit_day1_total"] + metrics["profit_day2_total"]
    
    metrics["sales_day1_total"] = firms_df["R_1"].sum()
    metrics["sales_day2_total"] = firms_df["R_2"].sum()
    metrics["sales_total"] = metrics["sales_day1_total"] + metrics["sales_day2_total"]
    
    metrics["labor_cost_day1_total"] = firms_df["labor_cost_holiday"].sum()
    metrics["labor_cost_day2_total"] = firms_df["labor_cost_bridge"].sum()
    metrics["labor_cost_total"] = metrics["labor_cost_day1_total"] + metrics["labor_cost_day2_total"]
    
    # Derived metrics
    if metrics["profit_day1_total"] != 0:
        metrics["profit_ratio_day2_over_day1"] = metrics["profit_day2_total"] / abs(metrics["profit_day1_total"])
    else:
        metrics["profit_ratio_day2_over_day1"] = np.nan
    
    metrics["mean_profit_total"] = (firms_df["profit_holiday"] + firms_df["profit_bridge"]).mean()
    metrics["median_profit_total"] = (firms_df["profit_holiday"] + firms_df["profit_bridge"]).median()
    
    # By sector
    sectors = config_copy["sectors"]
    for sector in sectors:
        mask = firms_df["sector"] == sector
        if mask.sum() == 0:
            # Set defaults if no firms in sector
            metrics[f"n_firms_{sector}"] = 0
            metrics[f"holiday_close_share_{sector}"] = np.nan
            metrics[f"holiday_open_sub_share_{sector}"] = np.nan
            metrics[f"holiday_open_no_share_{sector}"] = np.nan
            metrics[f"bridge_operate_share_{sector}"] = np.nan
            metrics[f"bridge_adopt_share_{sector}"] = np.nan
            metrics[f"profit_total_{sector}"] = 0.0
            metrics[f"sales_total_{sector}"] = 0.0
            continue
        
        sector_df = firms_df[mask]
        metrics[f"n_firms_{sector}"] = mask.sum()
        metrics[f"holiday_close_share_{sector}"] = (sector_df["action_holiday"] == "close").mean()
        metrics[f"holiday_open_sub_share_{sector}"] = (sector_df["action_holiday"] == "open_sub").mean()
        metrics[f"holiday_open_no_share_{sector}"] = (sector_df["action_holiday"] == "open_no").mean()
        metrics[f"bridge_operate_share_{sector}"] = (sector_df["action_bridge"] == "operate").mean()
        metrics[f"bridge_adopt_share_{sector}"] = (sector_df["action_bridge"] == "adopt_bridge").mean()
        metrics[f"profit_total_{sector}"] = (sector_df["profit_holiday"] + sector_df["profit_bridge"]).sum()
        metrics[f"sales_total_{sector}"] = (sector_df["R_1"] + sector_df["R_2"]).sum()
        metrics[f"profit_day1_{sector}"] = sector_df["profit_holiday"].sum()
        metrics[f"profit_day2_{sector}"] = sector_df["profit_bridge"].sum()
    
    # Add config hash for traceability
    metrics["config_hash"] = cfg_hash(config_copy)
    
    return metrics


if __name__ == "__main__":
    # Run simulation
    firms_df, summary_df = run()
    
    print("\n=== Summary ===")
    print(summary_df.to_string())

