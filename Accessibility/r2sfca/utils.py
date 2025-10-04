"""
Utility functions for the R2SFCA package.

This module contains helper functions for evaluation, plotting, and data processing.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Optional, Tuple
from scipy.stats import pearsonr


def evaluate_model(
    fij: np.ndarray,
    tij: np.ndarray,
    observed_flow: Optional[np.ndarray] = None,
    metrics: List[str] = None,
    epsilon: float = 1e-15,
) -> Dict:
    """
    Evaluate model performance using various metrics.

    Parameters:
    -----------
    fij : np.ndarray
        Calculated Fij values
    tij : np.ndarray
        Calculated Tij values
    observed_flow : np.ndarray, optional
        Observed flow values for validation
    metrics : list, optional
        List of metrics to calculate. If None, calculates all available metrics.
    epsilon : float
        Small value to avoid division by zero

    Returns:
    --------
    dict
        Dictionary containing evaluation metrics
    """
    if metrics is None:
        metrics = ["cross_entropy", "correlation", "rmse", "mse", "mae"]
        if observed_flow is not None:
            metrics.extend(["fij_flow_correlation", "tij_flow_correlation"])

    results = {}

    # Normalize Fij and Tij for cross-entropy calculation
    fij_norm = fij / (np.sum(fij) + epsilon)
    tij_norm = tij / (np.sum(tij) + epsilon)

    for metric in metrics:
        if metric == "cross_entropy":
            results[metric] = -np.sum(fij_norm * np.log(tij_norm + epsilon))

        elif metric == "correlation":
            corr, _ = pearsonr(fij, tij)
            results[metric] = corr

        elif metric == "rmse":
            results[metric] = np.sqrt(np.mean((fij - tij) ** 2))

        elif metric == "mse":
            results[metric] = np.mean((fij - tij) ** 2)

        elif metric == "mae":
            results[metric] = np.mean(np.abs(fij - tij))

        elif metric == "fij_flow_correlation" and observed_flow is not None:
            corr, _ = pearsonr(fij, observed_flow)
            results[metric] = corr

        elif metric == "tij_flow_correlation" and observed_flow is not None:
            corr, _ = pearsonr(tij, observed_flow)
            results[metric] = corr

    return results


def plot_grid_search_results(
    results_df: pd.DataFrame,
    x_col: str = "beta",
    y_cols: List[str] = None,
    title: str = None,
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Plot grid search results showing how metrics change with parameters.

    Parameters:
    -----------
    results_df : pd.DataFrame
        Results from grid search
    x_col : str
        Column name for x-axis
    y_cols : list, optional
        List of column names for y-axis. If None, uses common metrics.
    title : str, optional
        Plot title. If None, generates from data.
    figsize : tuple
        Figure size
    save_path : str, optional
        Path to save the plot

    Returns:
    --------
    matplotlib.figure.Figure
        The created figure
    """
    if y_cols is None:
        # Find common metric columns
        metric_cols = [
            "cross_entropy",
            "correlation",
            "rmse",
            "mse",
            "mae",
            "fij_flow_correlation",
            "tij_flow_correlation",
        ]
        y_cols = [col for col in metric_cols if col in results_df.columns]

    if not y_cols:
        raise ValueError("No valid y-axis columns found in results dataframe")

    # Create figure
    fig, axes = plt.subplots(len(y_cols), 1, figsize=figsize, sharex=True)
    if len(y_cols) == 1:
        axes = [axes]

    # Get decay function from results
    decay_function = (
        results_df["decay_function"].iloc[0]
        if "decay_function" in results_df.columns
        else "Unknown"
    )

    for i, y_col in enumerate(y_cols):
        ax = axes[i]

        # Plot the metric
        ax.plot(results_df[x_col], results_df[y_col], "b-", linewidth=2)

        # Find and mark optimal values
        if y_col == "cross_entropy":
            # Minimum cross-entropy
            min_idx = results_df[y_col].idxmin()
            min_x = results_df.loc[min_idx, x_col]
            ax.axvline(x=min_x, color="red", linestyle="--", alpha=0.7)
            ax.text(
                min_x,
                ax.get_ylim()[1] * 0.9,
                f"Min: {min_x:.3f}",
                rotation=90,
                verticalalignment="top",
            )

        elif y_col in ["correlation", "fij_flow_correlation", "tij_flow_correlation"]:
            # Maximum correlation
            max_idx = results_df[y_col].idxmax()
            max_x = results_df.loc[max_idx, x_col]
            ax.axvline(x=max_x, color="red", linestyle="--", alpha=0.7)
            ax.text(
                max_x,
                ax.get_ylim()[1] * 0.9,
                f"Max: {max_x:.3f}",
                rotation=90,
                verticalalignment="top",
            )

        elif y_col in ["rmse", "mse", "mae"]:
            # Minimum error
            min_idx = results_df[y_col].idxmin()
            min_x = results_df.loc[min_idx, x_col]
            ax.axvline(x=min_x, color="red", linestyle="--", alpha=0.7)
            ax.text(
                min_x,
                ax.get_ylim()[1] * 0.9,
                f"Min: {min_x:.3f}",
                rotation=90,
                verticalalignment="top",
            )

        ax.set_ylabel(y_col.replace("_", " ").title())
        ax.grid(True, alpha=0.3)

    # Set x-axis label and title
    axes[-1].set_xlabel(x_col.replace("_", " ").title())

    if title is None:
        title = f"Grid Search Results - {decay_function.title()} Decay Function"
    fig.suptitle(title, fontsize=14, fontweight="bold")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def plot_model_comparison(
    results_dfs: List[pd.DataFrame],
    labels: List[str],
    x_col: str = "beta",
    y_col: str = "fij_flow_correlation",
    title: str = "Model Comparison",
    figsize: Tuple[int, int] = (12, 8),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Plot comparison of multiple models' performance.

    Parameters:
    -----------
    results_dfs : list
        List of DataFrames with results from different models
    labels : list
        Labels for each model
    x_col : str
        Column name for x-axis
    y_col : str
        Column name for y-axis
    title : str
        Plot title
    figsize : tuple
        Figure size
    save_path : str, optional
        Path to save the plot

    Returns:
    --------
    matplotlib.figure.Figure
        The created figure
    """
    if len(results_dfs) != len(labels):
        raise ValueError("Number of dataframes must match number of labels")

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Set style
    sns.set_style("whitegrid")

    # Plot each model
    colors = plt.cm.tab10(np.linspace(0, 1, len(results_dfs)))

    for i, (df, label) in enumerate(zip(results_dfs, labels)):
        ax.plot(
            df[x_col],
            df[y_col],
            color=colors[i],
            linewidth=2,
            label=label,
            marker="o",
            markersize=4,
        )

    # Customize plot
    ax.set_xlabel(x_col.replace("_", " ").title())
    ax.set_ylabel(y_col.replace("_", " ").title())
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(title="Model", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig


def create_summary_table(
    results_dfs: List[pd.DataFrame],
    labels: List[str] = None,
    metric: str = "cross_entropy",
    minimize: bool = True,
) -> pd.DataFrame:
    """
    Create a summary table showing optimal parameters for each model.

    Parameters:
    -----------
    results_dfs : list
        List of DataFrames with results from different models
    labels : list, optional
        Labels for each model. If None, uses decay function names.
    metric : str
        Metric to use for finding optimal parameters
    minimize : bool
        Whether to minimize (True) or maximize (False) the metric

    Returns:
    --------
    pd.DataFrame
        Summary table with optimal parameters
    """
    if labels is None:
        labels = [
            (
                df["decay_function"].iloc[0]
                if "decay_function" in df.columns
                else f"Model_{i}"
            )
            for i, df in enumerate(results_dfs)
        ]

    if len(results_dfs) != len(labels):
        raise ValueError("Number of dataframes must match number of labels")

    summary_data = []

    for df, label in zip(results_dfs, labels):
        if metric not in df.columns:
            continue

        # Find optimal parameters
        if minimize:
            optimal_idx = df[metric].idxmin()
        else:
            optimal_idx = df[metric].idxmax()

        optimal_row = df.loc[optimal_idx]

        # Extract relevant information
        summary_row = {
            "Model": label,
            "Optimal_Beta": optimal_row["beta"],
            f"Optimal_{metric}": optimal_row[metric],
        }

        # Add second parameter if available
        if "param2" in df.columns:
            summary_row["Optimal_Param2"] = optimal_row["param2"]

        # Add other metrics at optimal point
        for col in df.columns:
            if col not in ["beta", "param2", "decay_function"] and col != metric:
                summary_row[col] = optimal_row[col]

        summary_data.append(summary_row)

    return pd.DataFrame(summary_data)


def normalize_metrics(
    results_df: pd.DataFrame, metrics: List[str] = None
) -> pd.DataFrame:
    """
    Normalize metrics in results dataframe to 0-1 scale.

    Parameters:
    -----------
    results_df : pd.DataFrame
        Results dataframe
    metrics : list, optional
        List of metrics to normalize. If None, normalizes all numeric columns.

    Returns:
    --------
    pd.DataFrame
        Results dataframe with normalized metrics
    """
    df_normalized = results_df.copy()

    if metrics is None:
        # Find numeric columns that are not parameters
        exclude_cols = ["beta", "param2", "decay_function"]
        metrics = [
            col
            for col in df_normalized.columns
            if col not in exclude_cols
            and df_normalized[col].dtype in ["float64", "int64"]
        ]

    for metric in metrics:
        if metric in df_normalized.columns:
            min_val = df_normalized[metric].min()
            max_val = df_normalized[metric].max()

            if max_val > min_val:
                df_normalized[metric] = (df_normalized[metric] - min_val) / (
                    max_val - min_val
                )
            else:
                df_normalized[metric] = 0.0

    return df_normalized


def calculate_accessibility_metrics(
    accessibility_scores: pd.Series, crowdedness_scores: pd.Series
) -> Dict:
    """
    Calculate summary statistics for accessibility and crowdedness scores.

    Parameters:
    -----------
    accessibility_scores : pd.Series
        Accessibility scores
    crowdedness_scores : pd.Series
        Crowdedness scores

    Returns:
    --------
    dict
        Dictionary containing summary statistics
    """
    return {
        "accessibility_mean": accessibility_scores.mean(),
        "accessibility_std": accessibility_scores.std(),
        "accessibility_min": accessibility_scores.min(),
        "accessibility_max": accessibility_scores.max(),
        "accessibility_median": accessibility_scores.median(),
        "crowdedness_mean": crowdedness_scores.mean(),
        "crowdedness_std": crowdedness_scores.std(),
        "crowdedness_min": crowdedness_scores.min(),
        "crowdedness_max": crowdedness_scores.max(),
        "crowdedness_median": crowdedness_scores.median(),
        "accessibility_crowdedness_correlation": accessibility_scores.corr(
            crowdedness_scores
        ),
    }
