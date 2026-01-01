"""
Run multiple simulation seeds and scenarios for robustness analysis.

This script runs the simulation with different seeds and scenario configurations,
aggregating results for statistical analysis (mean, percentiles, etc.).
"""

import json
import time
import sys
import pandas as pd
from pathlib import Path
from copy import deepcopy
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from run import run_once


def apply_scenario(base_cfg: Dict[str, Any], patches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply scenario patches to base configuration.
    
    Parameters:
    -----------
    base_cfg : dict
        Base configuration dictionary
    patches : list
        List of patches, each with "path" (list of keys) and "mult" (multiplier)
    
    Returns:
    --------
    dict
        Modified configuration
    """
    cfg = deepcopy(base_cfg)
    
    for patch in patches:
        path = patch["path"]
        mult = patch["mult"]
        ref = cfg
        
        # Navigate to the parent of the target
        for p in path[:-1]:
            if isinstance(p, int):
                ref = ref[p]
            else:
                ref = ref[p]
        
        # Apply multiplier to the target value
        target_key = path[-1]
        
        # Handle nested structures (like distributions)
        if isinstance(target_key, str) and target_key in ref:
            if isinstance(ref[target_key], dict):
                # If it's a dict (like distribution params), apply to numeric values
                for k in ref[target_key]:
                    if isinstance(ref[target_key][k], (int, float)):
                        ref[target_key][k] *= mult
            elif isinstance(ref[target_key], (int, float)):
                ref[target_key] *= mult
            elif isinstance(ref[target_key], list):
                # If it's a list, multiply numeric elements
                ref[target_key] = [x * mult if isinstance(x, (int, float)) else x for x in ref[target_key]]
    
    return cfg


def scenario_grid() -> Dict[str, List[Dict[str, Any]]]:
    """
    Define scenario configurations as patches to apply to base config.
    
    Returns:
    --------
    dict
        Dictionary mapping scenario names to lists of patches
    """
    return {
        "base": [],
        
        "tourism_demand_high": [
            {"path": ["demand_shocks", "holiday", "lodging"], "mult": 1.2},
            {"path": ["demand_shocks", "holiday", "restaurants"], "mult": 1.2},
            {"path": ["demand_shocks", "holiday", "transport"], "mult": 1.2},
            {"path": ["demand_shocks", "bridge", "lodging"], "mult": 1.2},
            {"path": ["demand_shocks", "bridge", "restaurants"], "mult": 1.2},
            {"path": ["demand_shocks", "bridge", "transport"], "mult": 1.2},
        ],
        
        "tourism_demand_low": [
            {"path": ["demand_shocks", "holiday", "lodging"], "mult": 0.8},
            {"path": ["demand_shocks", "holiday", "restaurants"], "mult": 0.8},
            {"path": ["demand_shocks", "holiday", "transport"], "mult": 0.8},
            {"path": ["demand_shocks", "bridge", "lodging"], "mult": 0.8},
            {"path": ["demand_shocks", "bridge", "restaurants"], "mult": 0.8},
            {"path": ["demand_shocks", "bridge", "transport"], "mult": 0.8},
        ],
        
        "H_high": [
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "lodging", "max"], "mult": 1.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "lodging", "min"], "mult": 1.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "restaurants", "max"], "mult": 1.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "restaurants", "min"], "mult": 1.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "retail", "max"], "mult": 1.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "retail", "min"], "mult": 1.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "transport", "max"], "mult": 1.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "transport", "min"], "mult": 1.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "manufacturing_b2b", "max"], "mult": 1.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "manufacturing_b2b", "min"], "mult": 1.5},
        ],
        
        "H_low": [
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "lodging", "max"], "mult": 0.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "lodging", "min"], "mult": 0.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "restaurants", "max"], "mult": 0.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "restaurants", "min"], "mult": 0.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "retail", "max"], "mult": 0.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "retail", "min"], "mult": 0.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "transport", "max"], "mult": 0.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "transport", "min"], "mult": 0.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "manufacturing_b2b", "max"], "mult": 0.5},
            {"path": ["policy_costs", "H_substitute_rest_factor_of_NW", "manufacturing_b2b", "min"], "mult": 0.5},
        ],
        
        "bridge_attractive": [
            {"path": ["demand_shocks", "bridge", "lodging"], "mult": 1.2},
            {"path": ["demand_shocks", "bridge", "restaurants"], "mult": 1.2},
            {"path": ["demand_shocks", "bridge", "retail"], "mult": 1.2},
            {"path": ["demand_shocks", "bridge", "transport"], "mult": 1.2},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "lodging", "max"], "mult": 0.8},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "lodging", "min"], "mult": 0.8},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "restaurants", "max"], "mult": 0.8},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "restaurants", "min"], "mult": 0.8},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "retail", "max"], "mult": 0.8},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "retail", "min"], "mult": 0.8},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "transport", "max"], "mult": 0.8},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "transport", "min"], "mult": 0.8},
        ],
        
        "bridge_costly": [
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "lodging", "max"], "mult": 1.5},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "lodging", "min"], "mult": 1.5},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "restaurants", "max"], "mult": 1.5},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "restaurants", "min"], "mult": 1.5},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "retail", "max"], "mult": 1.5},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "retail", "min"], "mult": 1.5},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "transport", "max"], "mult": 1.5},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "transport", "min"], "mult": 1.5},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "manufacturing_b2b", "max"], "mult": 1.5},
            {"path": ["policy_costs", "Hcomp_bridge_factor_of_NW", "manufacturing_b2b", "min"], "mult": 1.5},
        ],
        
        "capacity_high": [
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "lodging", "max"], "mult": 1.2},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "lodging", "min"], "mult": 1.2},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "restaurants", "max"], "mult": 1.2},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "restaurants", "min"], "mult": 1.2},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "retail", "max"], "mult": 1.2},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "retail", "min"], "mult": 1.2},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "transport", "max"], "mult": 1.2},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "transport", "min"], "mult": 1.2},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "manufacturing_b2b", "max"], "mult": 1.2},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "manufacturing_b2b", "min"], "mult": 1.2},
        ],
        
        "capacity_low": [
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "lodging", "max"], "mult": 0.8},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "lodging", "min"], "mult": 0.8},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "restaurants", "max"], "mult": 0.8},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "restaurants", "min"], "mult": 0.8},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "retail", "max"], "mult": 0.8},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "retail", "min"], "mult": 0.8},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "transport", "max"], "mult": 0.8},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "transport", "min"], "mult": 0.8},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "manufacturing_b2b", "max"], "mult": 0.8},
            {"path": ["firm_generation", "capacity_multiplier_K_over_R", "manufacturing_b2b", "min"], "mult": 0.8},
        ],
    }


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate results by scenario, computing mean and percentiles.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with one row per simulation (seed + scenario)
    
    Returns:
    --------
    pd.DataFrame
        Summary DataFrame with aggregated statistics per scenario
    """
    # Identify metric columns (exclude metadata)
    exclude_cols = ["scenario", "seed", "timestamp", "config_hash"]
    metrics = [c for c in df.columns if c not in exclude_cols]
    
    agg = []
    for sc_name, group in df.groupby("scenario"):
        row = {"scenario": sc_name, "n": len(group)}
        
        for m in metrics:
            # Skip if all NaN
            if group[m].isna().all():
                continue
            
            row[f"{m}_mean"] = group[m].mean()
            row[f"{m}_p10"] = group[m].quantile(0.10)
            row[f"{m}_p50"] = group[m].quantile(0.50)
            row[f"{m}_p90"] = group[m].quantile(0.90)
            row[f"{m}_std"] = group[m].std()
        
        agg.append(row)
    
    return pd.DataFrame(agg).sort_values("scenario")


def main(num_seeds: int = 300, num_firms: int = None):
    """
    Run multiple simulations with different seeds and scenarios.
    
    Parameters:
    -----------
    num_seeds : int
        Number of random seeds to run (default: 300 for publication quality)
    num_firms : int, optional
        Number of firms per simulation. If None, uses value from params.json
    """
    base_dir = Path(__file__).parent.parent
    params_path = base_dir / "data" / "params.json"
    
    print(f"Loading base configuration from {params_path}")
    base_cfg = json.loads(params_path.read_text())
    
    # Override num_firms if provided
    if num_firms is not None:
        base_cfg["run"]["num_firms"] = num_firms
        print(f"  Overriding num_firms to {num_firms}")
    else:
        print(f"  Using num_firms={base_cfg['run']['num_firms']} from config")
    
    scenarios = scenario_grid()
    print(f"\nScenarios defined: {list(scenarios.keys())}")
    print(f"Running {num_seeds} seeds per scenario = {len(scenarios) * num_seeds} total runs\n")
    
    seeds = list(range(1, num_seeds + 1))
    out_rows = []
    
    total_runs = len(scenarios) * num_seeds
    run_count = 0
    start_time = time.time()
    
    for sc_name, patches in scenarios.items():
        print(f"Processing scenario: {sc_name} ({len(patches)} patches)")
        
        for seed_idx, seed in enumerate(seeds):
            run_count += 1
            
            # Apply scenario patches
            cfg = apply_scenario(base_cfg, patches)
            
            # Run simulation
            try:
                res = run_once(seed=seed, config=cfg, silent=True)
                res["scenario"] = sc_name
                res["seed"] = seed
                res["timestamp"] = int(time.time())
                out_rows.append(res)
                
                # Progress update every 50 runs
                if run_count % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = run_count / elapsed
                    remaining = (total_runs - run_count) / rate
                    print(f"  Progress: {run_count}/{total_runs} runs ({run_count/total_runs*100:.1f}%) "
                          f"| Elapsed: {elapsed/60:.1f}m | ETA: {remaining/60:.1f}m")
                
            except Exception as e:
                print(f"  ERROR in scenario={sc_name}, seed={seed}: {e}")
                continue
    
    print(f"\nCompleted {run_count} runs in {(time.time() - start_time)/60:.1f} minutes")
    
    # Convert to DataFrame
    print("\nAggregating results...")
    df = pd.DataFrame(out_rows)
    
    # Save raw results
    output_dir = base_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    raw_file = output_dir / "runs_many.parquet"
    df.to_parquet(raw_file, index=False)
    print(f"Saved raw results: {raw_file} ({len(df)} rows)")
    
    # Compute and save summary
    summary_df = summarize(df)
    summary_file = output_dir / "summary_many.csv"
    summary_df.to_csv(summary_file, index=False)
    print(f"Saved summary: {summary_file}")
    print(f"\nSummary preview:")
    print(summary_df[["scenario", "n"] + [c for c in summary_df.columns if "_mean" in c and "profit_total_mean" in c]][:3].to_string())
    
    return df, summary_df


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run multiple simulation seeds and scenarios")
    parser.add_argument("--seeds", type=int, default=300, help="Number of seeds to run (default: 300)")
    parser.add_argument("--firms", type=int, default=None, help="Number of firms per simulation (default: from params.json)")
    args = parser.parse_args()
    
    df, summary_df = main(num_seeds=args.seeds, num_firms=args.firms)

