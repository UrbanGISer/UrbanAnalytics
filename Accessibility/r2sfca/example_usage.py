"""
Example usage of the R2SFCA package.

This script demonstrates the main features and usage patterns of the R2SFCA package.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from r2sfca import R2SFCA, DecayFunction
from r2sfca.utils import (
    plot_grid_search_results,
    plot_model_comparison,
    create_summary_table,
)


def create_sample_data(n_demand=50, n_supply=20, seed=42):
    """Create sample spatial accessibility data."""
    np.random.seed(seed)

    data = []
    for i in range(n_demand):
        for j in range(n_supply):
            # Create realistic spatial relationships
            distance = np.random.exponential(15)  # Travel cost
            demand = np.random.poisson(1000)  # Population
            supply = np.random.poisson(100)  # Service capacity

            # Create observed flow based on distance decay
            decay_factor = np.exp(-0.1 * distance)
            observed_flow = np.random.poisson(demand * supply * decay_factor / 10000)

            data.append(
                {
                    "DemandID": i,
                    "SupplyID": j,
                    "Demand": demand,
                    "Supply": supply,
                    "TravelCost": distance,
                    "O_Fij": observed_flow,
                }
            )

    return pd.DataFrame(data)


def example_basic_usage():
    """Demonstrate basic usage of R2SFCA."""
    print("=== Basic Usage Example ===")

    # Create sample data
    df = create_sample_data()
    print(f"Created sample data with {len(df)} demand-supply pairs")

    # Initialize model
    model = R2SFCA(
        df=df,
        demand_col="Demand",
        supply_col="Supply",
        travel_cost_col="TravelCost",
        demand_id_col="DemandID",
        supply_id_col="SupplyID",
        observed_flow_col="O_Fij",
        decay_function="gaussian",
    )

    # Calculate Fij and Tij
    beta = 2.0
    fij = model.fij(beta)
    tij = model.tij(beta)

    print(f"Calculated Fij and Tij with beta={beta}")
    print(f"Fij range: [{fij.min():.4f}, {fij.max():.4f}]")
    print(f"Tij range: [{tij.min():.4f}, {tij.max():.4f}]")

    # Calculate accessibility and crowdedness
    accessibility = model.access_score(beta)
    crowdedness = model.crowd_score(beta)

    print(
        f"Accessibility scores: mean={accessibility.mean():.4f}, std={accessibility.std():.4f}"
    )
    print(
        f"Crowdedness scores: mean={crowdedness.mean():.4f}, std={crowdedness.std():.4f}"
    )

    return model, df


def example_grid_search():
    """Demonstrate grid search functionality."""
    print("\n=== Grid Search Example ===")

    # Create sample data
    df = create_sample_data(n_demand=30, n_supply=15)

    # Initialize model
    model = R2SFCA(
        df=df,
        demand_col="Demand",
        supply_col="Supply",
        travel_cost_col="TravelCost",
        demand_id_col="DemandID",
        supply_id_col="SupplyID",
        observed_flow_col="O_Fij",
        decay_function="gaussian",
    )

    # Perform grid search
    print("Performing grid search...")
    results = model.search_fij(
        beta_range=(0.0, 3.0, 0.2),
        metrics=["cross_entropy", "correlation", "rmse", "fij_flow_correlation"],
    )

    print(f"Grid search completed with {len(results)} parameter combinations")

    # Find optimal parameters
    optimal_idx = results["cross_entropy"].idxmin()
    optimal_beta = results.loc[optimal_idx, "beta"]
    optimal_cross_entropy = results.loc[optimal_idx, "cross_entropy"]

    print(f"Optimal beta: {optimal_beta:.3f}")
    print(f"Optimal cross-entropy: {optimal_cross_entropy:.4f}")

    # Plot results
    fig = plot_grid_search_results(
        results_df=results,
        x_col="beta",
        y_cols=["cross_entropy", "fij_flow_correlation"],
        title="Grid Search Results - Gaussian Decay",
        save_path="grid_search_example.png",
    )
    print("Grid search plot saved as 'grid_search_example.png'")

    return results


def example_optimization():
    """Demonstrate parameter optimization."""
    print("\n=== Parameter Optimization Example ===")

    # Create sample data
    df = create_sample_data(n_demand=25, n_supply=10)

    # Initialize model
    model = R2SFCA(
        df=df,
        demand_col="Demand",
        supply_col="Supply",
        travel_cost_col="TravelCost",
        demand_id_col="DemandID",
        supply_id_col="SupplyID",
        observed_flow_col="O_Fij",
        decay_function="exponential",
    )

    # Adam optimization
    print("Running Adam optimization...")
    optimization_result = model.solve_beta(
        metric="cross_entropy", method="adam", num_epochs=100, learning_rate=0.01
    )

    print(
        f"Optimization completed successfully: {optimization_result['optimization_success']}"
    )
    print(f"Optimal beta: {optimization_result['optimal_beta']:.4f}")
    print(
        f"Final cross-entropy: {optimization_result['final_metrics']['cross_entropy']:.4f}"
    )
    print(
        f"Final correlation: {optimization_result['final_metrics']['correlation']:.4f}"
    )

    return optimization_result


def example_model_comparison():
    """Demonstrate model comparison across different decay functions."""
    print("\n=== Model Comparison Example ===")

    # Create sample data
    df = create_sample_data(n_demand=20, n_supply=8)

    # Compare different decay functions
    decay_functions = ["exponential", "power", "gaussian"]
    results_list = []
    labels = []

    for decay_func in decay_functions:
        print(f"Testing {decay_func} decay function...")

        model = R2SFCA(
            df=df,
            demand_col="Demand",
            supply_col="Supply",
            travel_cost_col="TravelCost",
            demand_id_col="DemandID",
            supply_id_col="SupplyID",
            observed_flow_col="O_Fij",
            decay_function=decay_func,
        )

        # Grid search
        results = model.search_fij(
            beta_range=(0.0, 2.0, 0.1),
            metrics=["cross_entropy", "fij_flow_correlation"],
        )

        results_list.append(results)
        labels.append(decay_func.title())

    # Create comparison plot
    fig = plot_model_comparison(
        results_dfs=results_list,
        labels=labels,
        y_col="fij_flow_correlation",
        title="Decay Function Comparison",
        save_path="model_comparison_example.png",
    )
    print("Model comparison plot saved as 'model_comparison_example.png'")

    # Create summary table
    summary = create_summary_table(
        results_dfs=results_list, labels=labels, metric="cross_entropy", minimize=True
    )
    print("\nSummary Table:")
    print(summary.to_string(index=False))

    return results_list, labels


def example_custom_parameters():
    """Demonstrate usage with custom decay function parameters."""
    print("\n=== Custom Parameters Example ===")

    # Create sample data
    df = create_sample_data(n_demand=15, n_supply=6)

    # Gaussian decay with custom d0 parameter
    model_gaussian = R2SFCA(
        df=df,
        demand_col="Demand",
        supply_col="Supply",
        travel_cost_col="TravelCost",
        demand_id_col="DemandID",
        supply_id_col="SupplyID",
        observed_flow_col="O_Fij",
        decay_function="gaussian",
    )

    # Test different d0 values
    d0_values = [10, 20, 30, 40]
    beta = 1.0

    print(f"Testing Gaussian decay with different d0 values (beta={beta}):")
    for d0 in d0_values:
        fij = model_gaussian.fij(beta, d0=d0)
        tij = model_gaussian.tij(beta, d0=d0)

        # Calculate correlation
        correlation = np.corrcoef(fij, tij)[0, 1]
        print(f"  d0={d0:2d}: Fij-Tij correlation = {correlation:.4f}")

    # Sigmoid decay with custom steepness
    model_sigmoid = R2SFCA(
        df=df,
        demand_col="Demand",
        supply_col="Supply",
        travel_cost_col="TravelCost",
        demand_id_col="DemandID",
        supply_id_col="SupplyID",
        observed_flow_col="O_Fij",
        decay_function="sigmoid",
    )

    # Test different steepness values
    steepness_values = [1, 3, 5, 10]
    beta = 1.0

    print(f"\nTesting Sigmoid decay with different steepness values (beta={beta}):")
    for steepness in steepness_values:
        fij = model_sigmoid.fij(beta, steepness=steepness)
        tij = model_sigmoid.tij(beta, steepness=steepness)

        # Calculate correlation
        correlation = np.corrcoef(fij, tij)[0, 1]
        print(f"  steepness={steepness:2d}: Fij-Tij correlation = {correlation:.4f}")


def main():
    """Run all examples."""
    print("R2SFCA Package Examples")
    print("=" * 50)

    try:
        # Run examples
        model, df = example_basic_usage()
        results = example_grid_search()
        optimization_result = example_optimization()
        results_list, labels = example_model_comparison()
        example_custom_parameters()

        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("Check the generated plots:")
        print("- grid_search_example.png")
        print("- model_comparison_example.png")

    except Exception as e:
        print(f"Error running examples: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
