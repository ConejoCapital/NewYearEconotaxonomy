"""
Compute daily sales and non-labor costs for firms based on demand shocks.

For each day type (holiday, bridge), applies sector-specific demand shocks
and cost shocks to base revenue and costs.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def compute_day_sales_and_costs(
    firms_df: pd.DataFrame,
    day_type: str,
    params: Dict[str, Any]
) -> pd.DataFrame:
    """
    Compute actual sales (R_t) and non-labor costs (C_t) for each firm
    based on day type and sector-specific shocks.
    
    Parameters:
    -----------
    firms_df : pd.DataFrame
        DataFrame with columns: firm_id, sector, R_base, C_base, K
    day_type : str
        Either "holiday" or "bridge"
    params : dict
        Parameters dictionary with demand_shocks and nonlabor_cost_shocks
    
    Returns:
    --------
    pd.DataFrame
        Original firms_df with added columns: R_t, C_t
    """
    firms_out = firms_df.copy()
    
    demand_shocks = params["demand_shocks"][day_type]
    cost_shocks = params["nonlabor_cost_shocks"][day_type]
    
    sectors = params["sectors"]
    
    # Initialize arrays
    R_t = np.zeros(len(firms_out))
    C_t = np.zeros(len(firms_out))
    
    for sector in sectors:
        mask = firms_out["sector"] == sector
        if mask.sum() == 0:
            continue
        
        # Apply demand shock: R_t = min(R_base * (1 + ΔD), K)
        delta_D = demand_shocks[sector]
        R_potential = firms_out.loc[mask, "R_base"] * (1 + delta_D)
        R_t[mask] = np.minimum(R_potential, firms_out.loc[mask, "K"])
        
        # Apply cost shock: C_t = C_base * (1 + ΔC)
        delta_C = cost_shocks[sector]
        C_t[mask] = firms_out.loc[mask, "C_base"] * (1 + delta_C)
    
    firms_out["R_t"] = R_t
    firms_out["C_t"] = C_t
    
    return firms_out

