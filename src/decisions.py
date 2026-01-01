"""
Decision logic for firms on holiday (Jan 1) and bridge day (Jan 2).

Holiday decisions: close, open with substitute rest, or open without (3x pay).
Bridge decisions: operate normally or adopt bridge day (closed with compensation).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def decide_holiday(firms_df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Firms decide how to operate on January 1 (holiday).
    
    Three options:
    1. close: labor_cost = 1.0 * N*W, profit = -labor_cost
    2. open_sub: labor_cost = 2.0 * N*W + H, profit = R_t - C_t - labor_cost
    3. open_no: labor_cost = 3.0 * N*W, profit = R_t - C_t - labor_cost
    
    Choose option with maximum profit.
    If tie and behavioral.holiday_tie_breaker_prefer_sub=True, prefer open_sub.
    
    Parameters:
    -----------
    firms_df : pd.DataFrame
        Must have columns: R_t, C_t, N, W, H
    params : dict
        Parameters dictionary with legal_cost_multipliers and behavioral
    
    Returns:
    --------
    pd.DataFrame
        Original df with added columns: action_holiday, profit_holiday, labor_cost_holiday
    """
    firms_out = firms_df.copy()
    
    multipliers = params["legal_cost_multipliers"]
    tie_breaker = params.get("behavioral", {}).get("holiday_tie_breaker_prefer_sub", False)
    
    N = firms_out["N"].values
    W = firms_out["W"].values
    R_t = firms_out["R_t"].values
    C_t = firms_out["C_t"].values
    H = firms_out["H"].values
    
    # Compute profits for each option
    # Option 1: Close
    labor_close = multipliers["holiday_close_multiplier"] * N * W
    profit_close = 0 - 0 - labor_close
    
    # Option 2: Open with substitute rest
    labor_open_sub = multipliers["holiday_open_with_sub_multiplier"] * N * W + H
    profit_open_sub = R_t - C_t - labor_open_sub
    
    # Option 3: Open without substitute rest (3x pay)
    labor_open_no = multipliers["holiday_open_no_sub_multiplier"] * N * W
    profit_open_no = R_t - C_t - labor_open_no
    
    # Choose maximum profit
    profits_matrix = np.column_stack([profit_close, profit_open_sub, profit_open_no])
    action_indices = np.argmax(profits_matrix, axis=1)
    
    # Handle ties if tie_breaker is enabled
    if tie_breaker:
        max_profits = profits_matrix.max(axis=1)
        # Check for ties between open_sub and open_no
        for i in range(len(firms_out)):
            if action_indices[i] == 2:  # open_no selected
                # Check if open_sub would have same profit (within tolerance)
                if np.isclose(profit_open_sub[i], profit_open_no[i], rtol=1e-10, atol=1e-10):
                    action_indices[i] = 1  # Prefer open_sub
    
    # Map indices to action names
    action_map = {0: "close", 1: "open_sub", 2: "open_no"}
    actions = [action_map[idx] for idx in action_indices]
    
    # Compute final profits and labor costs based on selected actions
    profits = np.zeros(len(firms_out))
    profits[action_indices == 0] = profit_close[action_indices == 0]
    profits[action_indices == 1] = profit_open_sub[action_indices == 1]
    profits[action_indices == 2] = profit_open_no[action_indices == 2]
    
    labor_costs = np.zeros(len(firms_out))
    labor_costs[action_indices == 0] = labor_close[action_indices == 0]
    labor_costs[action_indices == 1] = labor_open_sub[action_indices == 1]
    labor_costs[action_indices == 2] = labor_open_no[action_indices == 2]
    
    firms_out["action_holiday"] = actions
    firms_out["profit_holiday"] = profits
    firms_out["labor_cost_holiday"] = labor_costs
    
    return firms_out


def decide_bridge(firms_df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Firms decide how to operate on January 2 (bridge day).
    
    Two options:
    1. operate: labor_cost = 1.0 * N*W, profit = R_t - C_t - labor_cost
    2. adopt_bridge: profit = 0 - 0 - Hcomp (closed with compensation cost)
    
    Choose option with maximum profit.
    
    Parameters:
    -----------
    firms_df : pd.DataFrame
        Must have columns: R_t, C_t, N, W, Hcomp
    params : dict
        Parameters dictionary (not directly used, but kept for consistency)
    
    Returns:
    --------
    pd.DataFrame
        Original df with added columns: action_bridge, profit_bridge, labor_cost_bridge
    """
    firms_out = firms_df.copy()
    
    N = firms_out["N"].values
    W = firms_out["W"].values
    R_t = firms_out["R_t"].values
    C_t = firms_out["C_t"].values
    Hcomp = firms_out["Hcomp"].values
    
    # Option 1: Operate normally
    labor_operate = 1.0 * N * W
    profit_operate = R_t - C_t - labor_operate
    
    # Option 2: Adopt bridge (close with compensation cost)
    profit_adopt = 0 - 0 - Hcomp
    
    # Choose maximum profit
    profits_matrix = np.column_stack([profit_operate, profit_adopt])
    action_indices = np.argmax(profits_matrix, axis=1)
    
    # Map indices to action names
    action_map = {0: "operate", 1: "adopt_bridge"}
    actions = [action_map[idx] for idx in action_indices]
    
    # Compute final profits and labor costs based on selected actions
    profits = np.zeros(len(firms_out))
    profits[action_indices == 0] = profit_operate[action_indices == 0]
    profits[action_indices == 1] = profit_adopt[action_indices == 1]
    
    labor_costs = np.zeros(len(firms_out))
    labor_costs[action_indices == 0] = labor_operate[action_indices == 0]
    labor_costs[action_indices == 1] = Hcomp[action_indices == 1]
    
    firms_out["action_bridge"] = actions
    firms_out["profit_bridge"] = profits
    firms_out["labor_cost_bridge"] = labor_costs
    
    return firms_out

