"""
Core functionality for the R2SFCA package.

This module contains the main R2SFCA class and decay function implementations.
"""

import numpy as np
import pandas as pd
from enum import Enum
from typing import Optional, Dict, List, Tuple, Union
from scipy.optimize import minimize
from scipy.stats import pearsonr
import warnings


class DecayFunction(Enum):
    """Enumeration of available distance decay functions."""

    EXPONENTIAL = "exponential"
    POWER = "power"
    SIGMOID = "sigmoid"
    SQRT_EXPONENTIAL = "sqrt_exponential"
    GAUSSIAN = "gaussian"
    LOG_SQUARED = "log_squared"


class R2SFCA:
    """
    Reconciled Two-Step Floating Catchment Area (R2SFCA) model.

    This class implements the R2SFCA methodology that reconciles 2SFCA and i2SFCA
    methods through distance decay parameterization and cross-entropy minimization.

    Parameters:
    -----------
    df : pandas.DataFrame
        Input dataframe containing spatial accessibility data
    demand_col : str
        Column name for demand values
    supply_col : str
        Column name for supply values
    travel_cost_col : str
        Column name for travel cost/distance values
    demand_id_col : str
        Column name for demand location IDs
    supply_id_col : str
        Column name for supply location IDs
    observed_flow_col : str, optional
        Column name for observed flow values (for validation)
    decay_function : str or DecayFunction, default 'exponential'
        Type of decay function to use
    epsilon : float, default 1e-15
        Small value to avoid division by zero
    """

    def __init__(
        self,
        df: pd.DataFrame,
        demand_col: str = "Demand",
        supply_col: str = "Supply",
        travel_cost_col: str = "TravelCost",
        demand_id_col: str = "DemandID",
        supply_id_col: str = "SupplyID",
        observed_flow_col: Optional[str] = None,
        decay_function: Union[str, DecayFunction] = "exponential",
        epsilon: float = 1e-15,
    ):

        # Validate input dataframe
        required_cols = [
            demand_col,
            supply_col,
            travel_cost_col,
            demand_id_col,
            supply_id_col,
        ]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Store column names
        self.demand_col = demand_col
        self.supply_col = supply_col
        self.travel_cost_col = travel_cost_col
        self.demand_id_col = demand_id_col
        self.supply_id_col = supply_id_col
        self.observed_flow_col = observed_flow_col

        # Store data
        self.df = df.copy()
        self.demand = df[demand_col].values
        self.supply = df[supply_col].values
        self.travel_cost = df[travel_cost_col].values
        self.demand_ids = df[demand_id_col].values
        self.supply_ids = df[supply_id_col].values
        self.observed_flow = df[observed_flow_col].values if observed_flow_col else None

        # Store parameters
        self.epsilon = epsilon
        self.decay_function = (
            DecayFunction(decay_function)
            if isinstance(decay_function, str)
            else decay_function
        )

        # Calculate median travel cost for sigmoid scaling
        self.median_travel_cost = np.median(self.travel_cost)

        # Print info for sigmoid function
        if self.decay_function == DecayFunction.SIGMOID:
            print(
                f"Using median value of travel cost ({self.median_travel_cost:.2f}) for scaling beta in sigmoid function"
            )

        # Default parameters for different decay functions
        self._default_params = {
            DecayFunction.EXPONENTIAL: {"beta": 1.0},
            DecayFunction.POWER: {"beta": 1.0},
            DecayFunction.SIGMOID: {"beta": 1.0, "steepness": 3.0},
            DecayFunction.SQRT_EXPONENTIAL: {"beta": 1.0},
            DecayFunction.GAUSSIAN: {"beta": 1.0, "d0": 20.0},
            DecayFunction.LOG_SQUARED: {"beta": 1.0},
        }

    def dist_decay(self, beta: float, **kwargs) -> np.ndarray:
        """
        Calculate distance decay values using the specified decay function.

        Parameters:
        -----------
        beta : float
            Primary decay parameter
        **kwargs
            Additional parameters for specific decay functions:
            - steepness: for SIGMOID function (default: 3.0)
            - d0: for GAUSSIAN function (default: 20.0)

        Returns:
        --------
        np.ndarray
            Decay values
        """
        # Use the travel_cost stored in the model
        distance = self.travel_cost

        # Get default parameters for this decay function
        default_params = self._default_params[self.decay_function].copy()
        default_params.update(kwargs)

        # Allow epsilon to be overridden by kwargs
        epsilon = kwargs.get("epsilon", self.epsilon)

        if self.decay_function == DecayFunction.EXPONENTIAL:
            return np.exp(-beta * distance)

        elif self.decay_function == DecayFunction.POWER:
            return np.power(distance + epsilon, -beta)

        elif self.decay_function == DecayFunction.SIGMOID:
            steepness = default_params.get("steepness", 3.0)
            # Use beta * median_travel_cost as the scale parameter
            scale_beta = beta * self.median_travel_cost
            # Calculate argument with overflow protection
            arg = steepness * (distance - scale_beta)
            # Clip argument to prevent overflow/underflow
            arg = np.clip(arg, -500, 500)
            return 1.0 / (1 + np.exp(arg))

        elif self.decay_function == DecayFunction.SQRT_EXPONENTIAL:
            return np.exp(-beta * np.sqrt(distance + epsilon))

        elif self.decay_function == DecayFunction.GAUSSIAN:
            d0 = default_params.get("d0", 20.0)
            return np.exp(-beta * np.power(distance / d0, 2))

        elif self.decay_function == DecayFunction.LOG_SQUARED:
            return np.exp(-beta * np.power(np.log(distance + epsilon), 2))

        else:
            raise ValueError(f"Unknown decay function: {self.decay_function}")

    def fij(self, beta: float, **kwargs) -> np.ndarray:
        """
        Calculate Fij values (demand-side accessibility) using 2SFCA method.

        Parameters:
        -----------
        beta : float
            Decay parameter
        **kwargs
            Additional parameters for decay function

        Returns:
        --------
        np.ndarray
            Fij values
        """
        # Calculate supply-side decay coefficients
        decay_values = self.dist_decay(beta, **kwargs)
        sf_d = self.supply * decay_values

        # Get unique demand IDs
        unique_demand_ids = np.unique(self.demand_ids)

        # Initialize Fij result array
        fij = np.zeros_like(sf_d)

        # Calculate Fij for each demand location
        for d_id in unique_demand_ids:
            # Get indices where demand ID matches current ID
            d_mask = self.demand_ids == d_id

            # Get demand value for this ID
            d_value = self.demand[d_mask][0]

            # Calculate sum of supply * decay for this demand location
            sum_sf_d = np.sum(sf_d[d_mask])

            # Calculate Fij
            if sum_sf_d > 0:
                fij[d_mask] = d_value * sf_d[d_mask] / sum_sf_d

        return fij

    def tij(self, beta: float, **kwargs) -> np.ndarray:
        """
        Calculate Tij values (supply-side accessibility) using i2SFCA method.

        Parameters:
        -----------
        beta : float
            Decay parameter
        **kwargs
            Additional parameters for decay function

        Returns:
        --------
        np.ndarray
            Tij values
        """
        # Calculate demand-side decay coefficients
        decay_values = self.dist_decay(beta, **kwargs)
        df_d = self.demand * decay_values

        # Get unique supply IDs
        unique_supply_ids = np.unique(self.supply_ids)

        # Initialize Tij result array
        tij = np.zeros_like(df_d)

        # Calculate Tij for each supply location
        for s_id in unique_supply_ids:
            # Get indices where supply ID matches current ID
            s_mask = self.supply_ids == s_id

            # Get supply value for this ID
            s_value = self.supply[s_mask][0]

            # Calculate sum of demand * decay for this supply location
            sum_df_d = np.sum(df_d[s_mask])

            # Calculate Tij
            if sum_df_d > 0:
                tij[s_mask] = s_value * df_d[s_mask] / sum_df_d

        return tij

    def search_fij(
        self,
        beta_range: Union[float, Tuple[float, float, float]] = (0.0, 2.0, 0.1),
        param2_range: Optional[Union[float, Tuple[float, float, float]]] = None,
        metrics: List[str] = ["cross_entropy", "correlation", "rmse"],
        normalize: bool = True,
    ) -> pd.DataFrame:
        """
        Perform grid search over parameter ranges to find optimal values.

        Parameters:
        -----------
        beta_range : float or tuple
            If float: fixed beta value
            If tuple: (start, end, step) for beta parameter range
        param2_range : float or tuple, optional
            If float: fixed second parameter value
            If tuple: (start, end, step) for second parameter range
            If None: use default range based on decay function
        metrics : list
            List of evaluation metrics to calculate
        normalize : bool
            Whether to normalize Fij and Tij for cross-entropy calculation

        Returns:
        --------
        pd.DataFrame
            Results of grid search with evaluation metrics
        """
        # Validate and process beta_range
        if isinstance(beta_range, (int, float)):
            # Fixed beta value
            beta_values = np.array([beta_range])
        elif isinstance(beta_range, (tuple, list)) and len(beta_range) == 3:
            # Beta range (start, end, step)
            beta_start, beta_end, beta_step = beta_range
            beta_values = np.arange(beta_start, beta_end + beta_step, beta_step)
        else:
            raise ValueError(
                "beta_range must be a single number or a tuple of (start, end, step)"
            )

        # Validate and process param2_range
        if param2_range is None:
            # Use default range based on decay function
            if self.decay_function == DecayFunction.SIGMOID:
                param2_range = (1.0, 10.0, 0.5)  # steepness
            elif self.decay_function == DecayFunction.GAUSSIAN:
                param2_range = (10.0, 50.0, 5.0)  # d0
            else:
                param2_range = (1.0, 1.0, 1.0)  # dummy range

        if isinstance(param2_range, (int, float)):
            # Fixed param2 value
            param2_values = np.array([param2_range])
        elif isinstance(param2_range, (tuple, list)) and len(param2_range) == 3:
            # Param2 range (start, end, step)
            param2_start, param2_end, param2_step = param2_range
            param2_values = np.arange(
                param2_start, param2_end + param2_step, param2_step
            )
        else:
            raise ValueError(
                "param2_range must be a single number or a tuple of (start, end, step)"
            )

        # Check if both parameters are fixed (no search needed)
        if len(beta_values) == 1 and len(param2_values) == 1:
            raise ValueError(
                "Both beta_range and param2_range are fixed values. At least one parameter must have a range for grid search."
            )

        results = []

        for beta in beta_values:
            for param2 in param2_values:
                # Calculate Fij and Tij
                if self.decay_function == DecayFunction.SIGMOID:
                    fij = self.fij(beta, steepness=param2)
                    tij = self.tij(beta, steepness=param2)
                elif self.decay_function == DecayFunction.GAUSSIAN:
                    fij = self.fij(beta, d0=param2)
                    tij = self.tij(beta, d0=param2)
                else:
                    fij = self.fij(beta)
                    tij = self.tij(beta)

                # Calculate evaluation metrics
                eval_metrics = self._calculate_metrics(fij, tij, metrics, normalize)

                # Store results
                result = {
                    "beta": beta,
                    "param2": param2,
                    "decay_function": self.decay_function.value,
                    **eval_metrics,
                }
                results.append(result)

        return pd.DataFrame(results)

    def solve_beta(
        self,
        metric: str = "cross_entropy",
        param2: Optional[float] = None,
        method: str = "minimize",
        **kwargs,
    ) -> Dict:
        """
        Solve for optimal beta parameter using optimization.

        Parameters:
        -----------
        metric : str
            Metric to optimize ('cross_entropy', 'correlation', 'rmse', 'mse', 'mae')
        param2 : float, optional
            Second parameter value (steepness for sigmoid, d0 for gaussian)
        method : str
            Optimization method ('minimize' or 'adam')
        **kwargs
            Additional parameters for optimization

        Returns:
        --------
        dict
            Optimization results including optimal beta and metrics
        """
        if param2 is None:
            if self.decay_function == DecayFunction.SIGMOID:
                param2 = 3.0  # default steepness
            elif self.decay_function == DecayFunction.GAUSSIAN:
                param2 = np.median(self.travel_cost)  # default d0
            else:
                param2 = 1.0

        if method == "minimize":
            return self._solve_beta_minimize(metric, param2, **kwargs)
        elif method == "adam":
            return self._solve_beta_adam(metric, param2, **kwargs)
        else:
            raise ValueError(f"Unknown optimization method: {method}")

    def access_score(self, beta: float, **kwargs) -> pd.Series:
        """
        Calculate accessibility scores (Ai) for each demand location.

        Parameters:
        -----------
        beta : float
            Decay parameter
        **kwargs
            Additional parameters for decay function

        Returns:
        --------
        pd.Series
            Accessibility scores indexed by demand IDs
        """
        tij = self.tij(beta, **kwargs)

        # Calculate accessibility for each demand location
        unique_demand_ids = np.unique(self.demand_ids)
        accessibility = {}

        for d_id in unique_demand_ids:
            d_mask = self.demand_ids == d_id
            d_value = self.demand[d_mask][0]

            if d_value > 0:
                accessibility[d_id] = np.sum(tij[d_mask]) / d_value
            else:
                accessibility[d_id] = 0.0

        # Create series with all demand IDs, filling missing values with 0
        all_demand_ids = np.unique(self.demand_ids)
        access_series = pd.Series(0.0, index=all_demand_ids)
        for d_id, score in accessibility.items():
            access_series[d_id] = score

        return access_series

    def crowd_score(self, beta: float, **kwargs) -> pd.Series:
        """
        Calculate crowdedness scores (Cj) for each supply location.

        Parameters:
        -----------
        beta : float
            Decay parameter
        **kwargs
            Additional parameters for decay function

        Returns:
        --------
        pd.Series
            Crowdedness scores indexed by supply IDs
        """
        fij = self.fij(beta, **kwargs)

        # Calculate crowdedness for each supply location
        unique_supply_ids = np.unique(self.supply_ids)
        crowdedness = {}

        for s_id in unique_supply_ids:
            s_mask = self.supply_ids == s_id
            s_value = self.supply[s_mask][0]

            if s_value > 0:
                crowdedness[s_id] = np.sum(fij[s_mask]) / s_value
            else:
                crowdedness[s_id] = 0.0

        # Create series with all supply IDs, filling missing values with 0
        all_supply_ids = np.unique(self.supply_ids)
        crowd_series = pd.Series(0.0, index=all_supply_ids)
        for s_id, score in crowdedness.items():
            crowd_series[s_id] = score

        return crowd_series

    def _calculate_metrics(
        self,
        fij: np.ndarray,
        tij: np.ndarray,
        metrics: List[str],
        normalize: bool = True,
    ) -> Dict:
        """Calculate evaluation metrics between Fij and Tij."""
        results = {}

        if normalize:
            fij_norm = fij / (np.sum(fij) + self.epsilon)
            tij_norm = tij / (np.sum(tij) + self.epsilon)
        else:
            fij_norm = fij
            tij_norm = tij

        for metric in metrics:
            if metric == "cross_entropy":
                results[metric] = -np.sum(fij_norm * np.log(tij_norm + self.epsilon))

            elif metric == "correlation":
                corr, _ = pearsonr(fij, tij)
                results[metric] = corr

            elif metric == "rmse":
                results[metric] = np.sqrt(np.mean((fij - tij) ** 2))

            elif metric == "mse":
                results[metric] = np.mean((fij - tij) ** 2)

            elif metric == "mae":
                results[metric] = np.mean(np.abs(fij - tij))

            elif metric == "fij_flow_correlation" and self.observed_flow is not None:
                corr, _ = pearsonr(fij, self.observed_flow)
                results[metric] = corr

            elif metric == "tij_flow_correlation" and self.observed_flow is not None:
                corr, _ = pearsonr(tij, self.observed_flow)
                results[metric] = corr

        return results

    def _solve_beta_minimize(self, metric: str, param2: float, **kwargs) -> Dict:
        """Solve for optimal beta using scipy.optimize.minimize."""

        def objective(beta):
            if self.decay_function == DecayFunction.SIGMOID:
                fij = self.fij(beta[0], steepness=param2)
                tij = self.tij(beta[0], steepness=param2)
            elif self.decay_function == DecayFunction.GAUSSIAN:
                fij = self.fij(beta[0], d0=param2)
                tij = self.tij(beta[0], d0=param2)
            else:
                fij = self.fij(beta[0])
                tij = self.tij(beta[0])

            eval_metrics = self._calculate_metrics(fij, tij, [metric])

            # For metrics that should be maximized, return negative value
            if metric == "correlation" or metric.endswith("_correlation"):
                return -eval_metrics[
                    metric
                ]  # Maximize correlation = minimize negative correlation
            else:
                return eval_metrics[metric]  # Minimize error metrics

        # Set up optimization bounds
        bounds = [(0.001, 10.0)]  # beta must be positive

        # Initial guess
        x0 = [1.0]

        # Optimize
        result = minimize(objective, x0, bounds=bounds, method="L-BFGS-B", **kwargs)

        optimal_beta = result.x[0]

        # Calculate final metrics
        if self.decay_function == DecayFunction.SIGMOID:
            fij = self.fij(optimal_beta, steepness=param2)
            tij = self.tij(optimal_beta, steepness=param2)
        elif self.decay_function == DecayFunction.GAUSSIAN:
            fij = self.fij(optimal_beta, d0=param2)
            tij = self.tij(optimal_beta, d0=param2)
        else:
            fij = self.fij(optimal_beta)
            tij = self.tij(optimal_beta)

        final_metrics = self._calculate_metrics(
            fij, tij, ["cross_entropy", "correlation", "rmse", "mse", "mae"]
        )

        return {
            "optimal_beta": optimal_beta,
            "param2": param2,
            "optimization_success": result.success,
            "optimization_message": result.message,
            "final_metrics": final_metrics,
            "fij": fij,
            "tij": tij,
        }

    def _solve_beta_adam(
        self,
        metric: str,
        param2: float,
        num_epochs: int = 400,
        learning_rate: float = 0.01,
        **kwargs,
    ) -> Dict:
        """Solve for optimal beta using Adam optimizer."""
        # Initialize parameters
        log_beta = np.log(1.0)  # Use log space for stability

        # Adam parameters
        m_beta = 0.0
        v_beta = 0.0
        beta1 = 0.9
        beta2 = 0.999
        epsilon = 1e-8

        best_loss = float("inf")
        best_beta = 1.0
        best_fij = None
        best_tij = None

        for epoch in range(num_epochs):
            try:
                beta = np.exp(log_beta)

                # Calculate Fij and Tij
                if self.decay_function == DecayFunction.SIGMOID:
                    fij = self.fij(beta, steepness=param2)
                    tij = self.tij(beta, steepness=param2)
                elif self.decay_function == DecayFunction.GAUSSIAN:
                    fij = self.fij(beta, d0=param2)
                    tij = self.tij(beta, d0=param2)
                else:
                    fij = self.fij(beta)
                    tij = self.tij(beta)

                # Calculate loss
                eval_metrics = self._calculate_metrics(fij, tij, [metric])

                # For metrics that should be maximized, negate the value
                if metric == "correlation" or metric.endswith("_correlation"):
                    loss = -eval_metrics[
                        metric
                    ]  # Maximize correlation = minimize negative correlation
                else:
                    loss = eval_metrics[metric]  # Minimize error metrics

                # Add regularization
                regularization = 0.001 * (log_beta**2)
                total_loss = loss + regularization

                if np.isnan(total_loss):
                    continue

                # Calculate gradient using finite differences
                h = 1e-8
                log_beta_plus = log_beta + h
                beta_plus = np.exp(log_beta_plus)

                if self.decay_function == DecayFunction.SIGMOID:
                    fij_plus = self.fij(beta_plus, steepness=param2)
                    tij_plus = self.tij(beta_plus, steepness=param2)
                elif self.decay_function == DecayFunction.GAUSSIAN:
                    fij_plus = self.fij(beta_plus, d0=param2)
                    tij_plus = self.tij(beta_plus, d0=param2)
                else:
                    fij_plus = self.fij(beta_plus)
                    tij_plus = self.tij(beta_plus)

                eval_metrics_plus = self._calculate_metrics(
                    fij_plus, tij_plus, [metric]
                )

                # Apply same logic for maximization metrics
                if metric == "correlation" or metric.endswith("_correlation"):
                    loss_plus = -eval_metrics_plus[metric] + 0.001 * (log_beta_plus**2)
                else:
                    loss_plus = eval_metrics_plus[metric] + 0.001 * (log_beta_plus**2)

                grad_log_beta = (loss_plus - total_loss) / h

                # Adam update
                t = epoch + 1
                m_beta = beta1 * m_beta + (1 - beta1) * grad_log_beta
                v_beta = beta2 * v_beta + (1 - beta2) * (grad_log_beta**2)
                m_hat = m_beta / (1 - beta1**t)
                v_hat = v_beta / (1 - beta2**t)

                log_beta -= learning_rate * m_hat / (np.sqrt(v_hat) + epsilon)

                # Track best parameters
                if total_loss < best_loss:
                    best_loss = total_loss
                    best_beta = beta
                    best_fij = fij.copy()
                    best_tij = tij.copy()

            except Exception as e:
                warnings.warn(f"Error at epoch {epoch+1}: {str(e)}")
                continue

        # Calculate final metrics
        final_metrics = self._calculate_metrics(
            best_fij, best_tij, ["cross_entropy", "correlation", "rmse", "mse", "mae"]
        )

        return {
            "optimal_beta": best_beta,
            "param2": param2,
            "optimization_success": True,
            "optimization_message": f"Adam optimization completed after {num_epochs} epochs",
            "final_metrics": final_metrics,
            "fij": best_fij,
            "tij": best_tij,
        }
