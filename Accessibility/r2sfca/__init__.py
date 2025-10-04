"""
R2SFCA: Reconciled Two-Step Floating Catchment Area Model

A Python package for spatial accessibility analysis that reconciles 2SFCA and i2SFCA
methods through distance decay parameterization and cross-entropy minimization.

Main Classes:
    R2SFCA: Main class for spatial accessibility analysis
    DecayFunction: Enum for available decay functions

Example:
    >>> import pandas as pd
    >>> from r2sfca import R2SFCA
    >>>
    >>> # Load your data
    >>> df = pd.read_csv('your_data.csv')
    >>>
    >>> # Initialize the model
    >>> model = R2SFCA(df,
    ...                 demand_col='Demand',
    ...                 supply_col='Supply',
    ...                 travel_cost_col='TravelCost',
    ...                 demand_id_col='DemandID',
    ...                 supply_id_col='SupplyID',
    ...                 decay_function='gaussian')
    >>>
    >>> # Calculate accessibility and crowdedness
    >>> accessibility = model.access_score(beta=2.5)
    >>> crowdedness = model.crowd_score(beta=2.5)
"""

from .core import R2SFCA, DecayFunction
from .utils import evaluate_model, plot_grid_search_results

__version__ = "1.0.0"
__author__ = "Lingbo Liu, Fahui Wang"
__email__ = "lingbo.liu@harvard.edu, fahui.wang@lsu.edu"

__all__ = ["R2SFCA", "DecayFunction", "evaluate_model", "plot_grid_search_results"]
