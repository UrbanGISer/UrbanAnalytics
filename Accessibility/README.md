# r2SFCA: Reconciled Two-Step Floating Catchment Area Model

[![PyPI version](https://badge.fury.io/py/r2sfca.svg)](https://pypi.org/project/r2sfca/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A Python package for spatial accessibility analysis that reconciles 2SFCA and i2SFCA methods through distance decay parameterization and cross-entropy minimization.

**Authors:** Lingbo Liu (lingboliu@fas.harvard.edu), Fahui Wang (fwang@lsu.edu)

<img width="882" height="360" alt="image" src="https://github.com/user-attachments/assets/5b866b93-f18b-42e0-bf5d-57a8cb6725a0" />

## 📖 Abstract

Understanding spatial accessibility and facility crowdedness is central to public service planning, yet existing methods often treat these two metrics separately. The Two-Step Floating Catchment Area (2SFCA) method measures accessibility from the demand side, while the inverted 2SFCA (i2SFCA) assesses crowdedness from the supply side. However, without proper integration, these two measures may diverge, raising concerns of their validity. This study introduces a distance decay parameterization framework to reconcile 2SFCA and i2SFCA by optimizing a unified distance decay function through cross-entropy minimization. We demonstrate that aligning demand-side and supply-side flows effectively enforces a behavioral equilibrium between accessibility and crowdedness.

## 🔗 Links

- **PyPI Package**: [https://pypi.org/project/r2sfca/](https://pypi.org/project/r2sfca/)
- **Research Paper**: [Liu, L., & Wang, F. (2025). Reconciling 2SFCA and i2SFCA: A distance decay parameterization approach through cross-entropy minimization. International Journal of Geographical Information Science](https://doi.org/10.1080/13658816.2025.2562255)

## 🚀 Quick Start

### Installation

```bash
pip install r2sfca
```

### Basic Usage

```python
import pandas as pd
from r2sfca import R2SFCA

# Load your spatial accessibility data
url = 'https://raw.githubusercontent.com/UrbanGISer/UrbanAnalytics/refs/heads/main/Accessibility/r2SFCA_data.csv.gz'
df = pd.read_csv(url)

# Initialize the R2SFCA model
model = R2SFCA(
    df=df,
    demand_col='Demand',
    supply_col='Supply',
    travel_cost_col='TravelCost',
    demand_id_col='DemandID',
    supply_id_col='SupplyID',
    decay_function='exponential'  # or 'gaussian', 'sigmoid', etc.
)

# Optimize parameters using cross-entropy minimization
optimization_result = model.solve_beta(
    metric='cross_entropy',
    method='minimize'
)

print(f"Optimal beta: {optimization_result['optimal_beta']}")
print(f"Cross-entropy: {optimization_result['final_metrics']['cross_entropy']}")
print(f"Correlation: {optimization_result['final_metrics']['correlation']}")

# Calculate accessibility and crowdedness scores
opt_beta = optimization_result['optimal_beta']
accessibility = 1000 * model.access_score(beta=opt_beta)  # Scale for readability
crowdedness = model.crowd_score(beta=opt_beta)

# Convert to DataFrames
accessibility_df = pd.DataFrame({
    'DemandID': accessibility.index,
    'Accessibility': accessibility.values
})

crowdedness_df = pd.DataFrame({
    'SupplyID': crowdedness.index,
    'Crowdedness': crowdedness.values
})

print("Accessibility by Demand ID:")
print(accessibility_df.head())
print("\nCrowdedness by Supply ID:")
print(crowdedness_df.head())
```

## 🔧 Advanced Usage

### Grid Search for Parameter Optimization

```python
# Perform grid search to find optimal parameters
results = model.search_fij(
    beta_range=(0.0, 4.0, 0.2),
    metrics=['cross_entropy', 'correlation', 'rmse']
)

# Find optimal parameters
best_idx = results['cross_entropy'].idxmin()
optimal_beta = results.loc[best_idx, 'beta']
print(f"Grid search optimal beta: {optimal_beta}")
```

### Gaussian Decay Function with Custom Parameters

```python
# Initialize with Gaussian decay
model_gaussian = R2SFCA(
    df=df,
    demand_col='Demand',
    supply_col='Supply',
    travel_cost_col='TravelCost',
    demand_id_col='DemandID',
    supply_id_col='SupplyID',
    decay_function='gaussian'
)

# Optimize with custom d0 parameter
optimization_result = model_gaussian.solve_beta(
    metric='cross_entropy',
    param2=20.0,  # d0 parameter for Gaussian decay
    method='minimize'
)

print(f"Gaussian optimal beta: {optimization_result['optimal_beta']}")
print(f"Cross-entropy: {optimization_result['final_metrics']['cross_entropy']}")
```

### Adam Optimizer for Large Datasets

```python
# Use Adam optimizer for faster convergence
optimization_adam = model.solve_beta(
    metric='cross_entropy',
    method='adam',
    num_epochs=600
)

print(f"Adam optimal beta: {optimization_adam['optimal_beta']}")
```

### Multi-Parameter Grid Search

```python
# Grid search with second parameter (e.g., d0 for Gaussian)
results = model_gaussian.search_fij(
    beta_range=(0.0, 4.0, 0.2),
    param2_range=(10, 50, 10),  # d0 range for Gaussian
    metrics=['cross_entropy', 'correlation', 'rmse']
)

print("Grid search results:")
print(results.head())
```

## 📊 Supported Decay Functions

The package supports six distance decay functions:

1. **Exponential**: `f(d) = exp(-β * d)`
2. **Power**: `f(d) = d^(-β)`
3. **Sigmoid**: `f(d) = 1 / (1 + exp(steepness * (d - β)))`
4. **Square Root Exponential**: `f(d) = exp(-β * sqrt(d))`
5. **Gaussian**: `f(d) = exp(-β * (d/d0)²)`
6. **Log-Squared**: `f(d) = exp(-β * log(d)²)`

```python
from r2sfca import DecayFunction

# Available decay functions
print([func.value for func in DecayFunction])
# Output: ['exponential', 'power', 'sigmoid', 'sqrt_exponential', 'gaussian', 'log_squared']
```

## 📈 Data Requirements

Your input DataFrame should contain:

| Column | Description | Example |
|--------|-------------|---------|
| `Demand` | Demand values (e.g., population) | 1000, 2000, 1500 |
| `Supply` | Supply values (e.g., service capacity) | 50, 75, 60 |
| `TravelCost` | Travel cost/distance between locations | 10, 20, 15 |
| `DemandID` | Unique identifiers for demand locations | 1, 2, 3 |
| `SupplyID` | Unique identifiers for supply locations | 1, 2, 3 |
| `O_Fij` | Observed flow values (optional, for validation) | 5, 10, 8 |

## 🔍 Evaluation Metrics

The package provides comprehensive evaluation metrics:

- **Cross Entropy**: Measures difference between Fij and Tij distributions
- **Correlation**: Pearson correlation between Fij and Tij
- **RMSE**: Root Mean Square Error
- **MSE**: Mean Square Error
- **MAE**: Mean Absolute Error
- **Fij-Flow Correlation**: Correlation with observed flows (if available)
- **Tij-Flow Correlation**: Correlation with observed flows (if available)

## 📊 Visualization

### Grid Search Results

```python
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler

# Normalize metrics for comparison
metrics_to_normalize = ['cross_entropy', 'correlation', 'rmse']
results_normalized = results.copy()
scaler = MinMaxScaler()
results_normalized[metrics_to_normalize] = scaler.fit_transform(results[metrics_to_normalize])

# Create visualization
results_melted = results_normalized.melt(
    id_vars=['beta'],
    value_vars=metrics_to_normalize,
    var_name='Metric',
    value_name='Normalized Value'
)

plt.figure(figsize=(10, 6))
sns.lineplot(data=results_melted, x='beta', y='Normalized Value', hue='Metric')
plt.title('Normalized Metrics vs. Beta')
plt.xlabel('Beta')
plt.ylabel('Normalized Value')
plt.grid(True)
plt.show()
```

## 🎯 Best Practices

### 1. Parameter Selection Strategy

```python
# Test multiple decay functions
decay_functions = ['exponential', 'gaussian', 'sigmoid']
results_comparison = {}

for decay_func in decay_functions:
    model_temp = R2SFCA(
        df=df,
        demand_col='Demand',
        supply_col='Supply',
        travel_cost_col='TravelCost',
        demand_id_col='DemandID',
        supply_id_col='SupplyID',
        decay_function=decay_func
    )
    
    optimization = model_temp.solve_beta(metric='cross_entropy')
    results_comparison[decay_func] = {
        'beta': optimization['optimal_beta'],
        'cross_entropy': optimization['final_metrics']['cross_entropy'],
        'correlation': optimization['final_metrics']['correlation']
    }

# Compare results
comparison_df = pd.DataFrame(results_comparison).T
print("Decay Function Comparison:")
print(comparison_df)
```

### 2. Validation with Observed Flows

```python
# Use observed flows for validation
model_with_flows = R2SFCA(
    df=df,
    demand_col='Demand',
    supply_col='Supply',
    travel_cost_col='TravelCost',
    demand_id_col='DemandID',
    supply_id_col='SupplyID',
    observed_flow_col='O_Fij',  # Include observed flows
    decay_function='gaussian'
)

# Optimize and validate
optimization = model_with_flows.solve_beta(metric='cross_entropy')
print(f"Fij-Flow Correlation: {optimization['final_metrics']['fij_flow_correlation']}")
print(f"Tij-Flow Correlation: {optimization['final_metrics']['tij_flow_correlation']}")
```

### 3. Sensitivity Analysis

```python
# Test different parameter ranges
param_ranges = {
    'exponential': (0.0, 2.0, 0.1),
    'gaussian': (0.0, 5.0, 0.2),
    'sigmoid': (0.0, 3.0, 0.1)
}

for decay_func, beta_range in param_ranges.items():
    model_temp = R2SFCA(df=df, decay_function=decay_func)
    results = model_temp.search_fij(beta_range=beta_range)
    best_beta = results.loc[results['cross_entropy'].idxmin(), 'beta']
    print(f"{decay_func}: optimal beta = {best_beta:.3f}")
```

## 🛠️ API Reference

### R2SFCA Class

```python
R2SFCA(
    df,                    # Input DataFrame
    demand_col,           # Demand column name
    supply_col,           # Supply column name
    travel_cost_col,      # Travel cost column name
    demand_id_col,        # Demand ID column name
    supply_id_col,        # Supply ID column name
    observed_flow_col=None,  # Observed flow column (optional)
    decay_function='exponential',  # Decay function type
    epsilon=1e-15         # Small value for numerical stability
)
```

### Key Methods

- `solve_beta()`: Optimize beta parameter using cross-entropy minimization
- `search_fij()`: Grid search for parameter optimization
- `access_score()`: Calculate accessibility scores for demand locations
- `crowd_score()`: Calculate crowdedness scores for supply locations
- `fij()`: Calculate Fij values (demand-side accessibility)
- `tij()`: Calculate Tij values (supply-side accessibility)

## 📚 Citation

If you use this package in your research, please cite:

```bibtex
@article{liu2025reconciling,
  title={Reconciling 2SFCA and i2SFCA: A distance decay parameterization approach through cross-entropy minimization},
  author={Liu, Lingbo and Wang, Fahui},
  journal={International Journal of Geographical Information Science},
  year={2025},
  doi={10.1080/13658816.2025.2562255}
}
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [UrbanAnalytics](https://github.com/UrbanGISer/UrbanAnalytics) - Urban analytics research repository
- [2SFCA Methods](https://doi.org/10.1080/13658816.2025.2562255) - Original research paper

## 📞 Support

For questions and support:
- Open an issue on GitHub
- Contact: lingboliu@fas.harvard.edu, fwang@lsu.edu

---

**Made with ❤️ by the Urban Analytics Research Group**



