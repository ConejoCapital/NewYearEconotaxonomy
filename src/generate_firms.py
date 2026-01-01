"""
Generate synthetic firms for the economic simulation.

Each firm has attributes: firm_id, sector, W (salary), N (workers),
R_base (base revenue), C_base (base non-labor costs), K (capacity),
H (substitute rest cost), Hcomp (bridge compensation cost).
"""

import numpy as np
import pandas as pd
from typing import Dict, Any


def sample_from_distribution(dist_params: Dict[str, Any], size: int, rng: np.random.Generator) -> np.ndarray:
    """
    Sample values from a distribution specified by parameters.
    
    Supported distributions:
    - uniform: min, max
    - lognormal: median, sigma (converts to mu, then samples), min, max (for clipping)
    - discrete: values, weights
    """
    dist_type = dist_params["dist"]
    
    if dist_type == "uniform":
        values = rng.uniform(dist_params["min"], dist_params["max"], size)
    elif dist_type == "lognormal":
        # Convert median and sigma to mu for lognormal
        # median = exp(mu) => mu = log(median)
        mu = np.log(dist_params["median"])
        sigma = dist_params["sigma"]
        values = rng.lognormal(mu, sigma, size)
        # Clip to [min, max]
        values = np.clip(values, dist_params["min"], dist_params["max"])
    elif dist_type == "discrete":
        values_array = np.array(dist_params["values"])
        weights_array = np.array(dist_params["weights"])
        # Normalize weights
        weights_normalized = weights_array / weights_array.sum()
        values = rng.choice(values_array, size=size, p=weights_normalized)
    else:
        raise ValueError(f"Unknown distribution type: {dist_type}")
    
    return values


def generate_firms(num_firms: int, params: Dict[str, Any], seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic firms with attributes based on sector distributions.
    
    Parameters:
    -----------
    num_firms : int
        Number of firms to generate
    params : dict
        Parameters dictionary from params.json
    seed : int
        Random seed for reproducibility
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: firm_id, sector, W, N, R_base, C_base, K, H, Hcomp
    """
    rng = np.random.default_rng(seed)
    
    sectors = params["sectors"]
    sector_weights = params["sector_weights"]
    
    # Assign sectors based on weights
    sector_probs = [sector_weights[s] for s in sectors]
    sector_probs = np.array(sector_probs) / sum(sector_probs)  # Normalize
    firm_sectors = rng.choice(sectors, size=num_firms, p=sector_probs)
    
    # Initialize arrays
    firm_ids = np.arange(1, num_firms + 1)
    W_values = np.zeros(num_firms)
    N_values = np.zeros(num_firms, dtype=int)
    R_base_values = np.zeros(num_firms)
    C_base_values = np.zeros(num_firms)
    K_values = np.zeros(num_firms)
    H_values = np.zeros(num_firms)
    Hcomp_values = np.zeros(num_firms)
    
    # Generate attributes per sector
    firm_gen_params = params["firm_generation"]
    policy_costs = params["policy_costs"]
    
    for sector in sectors:
        mask = firm_sectors == sector
        n_sector = mask.sum()
        
        if n_sector == 0:
            continue
        
        # Sample W (salary per worker)
        W_params = firm_gen_params["salary_W_pen_per_worker"][sector]
        W_values[mask] = sample_from_distribution(W_params, n_sector, rng)
        
        # Sample N (number of workers)
        N_params = firm_gen_params["workers_N"][sector]
        N_values[mask] = sample_from_distribution(N_params, n_sector, rng).astype(int)
        
        # Sample R_base (base revenue)
        R_params = firm_gen_params["revenue_R_base_pen"][sector]
        R_base_values[mask] = sample_from_distribution(R_params, n_sector, rng)
        
        # Sample cost ratio and compute C_base
        cost_ratio_params = firm_gen_params["nonlabor_cost_ratio_C_over_R"][sector]
        cost_ratios = sample_from_distribution(cost_ratio_params, n_sector, rng)
        C_base_values[mask] = R_base_values[mask] * cost_ratios
        
        # Sample capacity multiplier and compute K
        capacity_params = firm_gen_params["capacity_multiplier_K_over_R"][sector]
        capacity_multipliers = sample_from_distribution(capacity_params, n_sector, rng)
        K_values[mask] = R_base_values[mask] * capacity_multipliers
        
        # Sample H factor (substitute rest cost factor)
        H_factor_params = policy_costs["H_substitute_rest_factor_of_NW"][sector]
        H_factors = sample_from_distribution(H_factor_params, n_sector, rng)
        H_values[mask] = H_factors * (N_values[mask] * W_values[mask])
        
        # Sample Hcomp factor (bridge compensation cost factor)
        Hcomp_factor_params = policy_costs["Hcomp_bridge_factor_of_NW"][sector]
        Hcomp_factors = sample_from_distribution(Hcomp_factor_params, n_sector, rng)
        Hcomp_values[mask] = Hcomp_factors * (N_values[mask] * W_values[mask])
    
    # Create DataFrame
    firms_df = pd.DataFrame({
        "firm_id": firm_ids,
        "sector": firm_sectors,
        "W": W_values,
        "N": N_values,
        "R_base": R_base_values,
        "C_base": C_base_values,
        "K": K_values,
        "H": H_values,
        "Hcomp": Hcomp_values
    })
    
    return firms_df

