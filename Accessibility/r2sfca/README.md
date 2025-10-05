# r2SFCA: Reconciled Two-Step Floating Catchment Area Model

A Python package for spatial accessibility analysis that reconciles 2SFCA and i2SFCA methods through distance decay parameterization and cross-entropy minimization.

**Authors:** Lingbo Liu (lingboliu@fas.harvard.edu), Fahui Wang (fwang@lsu.edu)

## Overview

The r2SFCA package implements a unified framework for spatial accessibility analysis that:

- Reconciles demand-side (2SFCA) and supply-side (i2SFCA) accessibility measures
- Optimizes distance decay parameters through cross-entropy minimization
- Supports multiple decay functions with configurable parameters
- Provides comprehensive evaluation metrics and visualization tools
- Enables grid search and Adam optimization for parameter estimation

## Installation

```bash
pip install r2sfca
```

## Quick Start

```python
import pandas as pd
from r2sfca import R2SFCA

# Load your spatial accessibility data
df = pd.read_csv('your_data.csv')

# Initialize the R2SFCA model
model = R2SFCA(
    df=df,
    demand_col='Demand',
    supply_col='Supply',
    travel_cost_col='TravelCost',
    demand_id_col='DemandID',
    supply_id_col='SupplyID',
    observed_flow_col='O_Fij',  # Optional, for validation
    decay_function='gaussian'
)

# Calculate accessibility and crowdedness scores
accessibility = model.access_score(beta=2.5)
crowdedness = model.crowd_score(beta=2.5)

# Perform grid search to find optimal parameters
results = model.search_fij(
    beta_range=(0.0, 5.0, 0.1),
    # param2_range = (10, 20.0, 5.0),#optional for sigmoid and gaussian function
    # either parameter can be a fixed value
    metrics=['cross_entropy', 'correlation', 'rmse']
)

# Optimize parameters using Adam optimizer
optimization_result = model.solve_beta(
    metric='cross_entropy',
    # param2=20.0, #optional for sigmoid and gaussian function
    method='adam',
    num_epochs=400
)
```

## Data Requirements

Your input dataframe should contain the following columns:

- **Demand**: Demand values (e.g., population)
- **Supply**: Supply values (e.g., service capacity)
- **TravelCost**: Travel cost/distance between demand and supply locations
- **DemandID**: Unique identifiers for demand locations
- **SupplyID**: Unique identifiers for supply locations
- **O_Fij** (optional): Observed flow values for model validation

## Decay Functions

The package supports six distance decay functions:

### 1. Exponential Decay
```python
f(d) = exp(-β * d)
```

### 2. Power Decay
```python
f(d) = d^(-β)
```

### 3. Sigmoid Decay
```python
f(d) = 1 / (1 + exp(steepness * (d - β)))
```

### 4. Square Root Exponential Decay
```python
f(d) = exp(-β * sqrt(d))
```

### 5. Gaussian Decay
```python
f(d) = exp(-β * (d/d0)²)
```

### 6. Log-Squared Decay
```python
f(d) = exp(-β * log(d)²)
```

## API Reference

### R2SFCA Class

#### Constructor
```python
R2SFCA(df, demand_col, supply_col, travel_cost_col, demand_id_col, supply_id_col, 
       observed_flow_col=None, decay_function='exponential', epsilon=1e-15)
```

#### Methods

##### `dist_decay(beta, **kwargs)`
Calculate distance decay values using the specified decay function.

**Parameters:**
- `beta`: Primary decay parameter
- `**kwargs`: Additional parameters (steepness for sigmoid, d0 for gaussian)

**Note:** Uses the travel_cost data stored in the model during initialization.

**Returns:** Decay values

##### `fij(beta, **kwargs)`
Calculate Fij values (demand-side accessibility) using 2SFCA method.

**Parameters:**
- `beta`: Decay parameter
- `**kwargs`: Additional parameters for decay function

**Returns:** Fij values

##### `tij(beta, **kwargs)`
Calculate Tij values (supply-side accessibility) using i2SFCA method.

**Parameters:**
- `beta`: Decay parameter
- `**kwargs`: Additional parameters for decay function

**Returns:** Tij values

##### `search_fij(beta_range, param2_range=None, metrics=None, normalize=True)`
Perform grid search over parameter ranges to find optimal values.

**Parameters:**
- `beta_range`: (start, end, step) for beta parameter
- `param2_range`: (start, end, step) for second parameter
- `metrics`: List of evaluation metrics to calculate
- `normalize`: Whether to normalize Fij and Tij for cross-entropy calculation

**Returns:** DataFrame with grid search results

##### `solve_beta(metric='cross_entropy', param2=None, method='minimize', **kwargs)`
Solve for optimal beta parameter using optimization.

**Parameters:**
- `metric`: Metric to optimize
- `param2`: Second parameter value
- `method`: Optimization method ('minimize' or 'adam')
- `**kwargs`: Additional optimization parameters

**Returns:** Dictionary with optimization results

##### `access_score(beta, **kwargs)`
Calculate accessibility scores (Ai) for each demand location.

**Parameters:**
- `beta`: Decay parameter
- `**kwargs`: Additional parameters for decay function

**Returns:** Series with accessibility scores

##### `crowd_score(beta, **kwargs)`
Calculate crowdedness scores (Cj) for each supply location.

**Parameters:**
- `beta`: Decay parameter
- `**kwargs`: Additional parameters for decay function

**Returns:** Series with crowdedness scores

## Evaluation Metrics

The package provides several evaluation metrics:

- **Cross Entropy**: Measures the difference between Fij and Tij distributions
- **Correlation**: Pearson correlation coefficient between Fij and Tij
- **RMSE**: Root Mean Square Error
- **MSE**: Mean Square Error
- **MAE**: Mean Absolute Error
- **Fij-Flow Correlation**: Correlation between estimated Fij and observed flows
- **Tij-Flow Correlation**: Correlation between estimated Tij and observed flows

## Visualization

### Grid Search Results
```python
from r2sfca.utils import plot_grid_search_results

# Plot grid search results
fig = plot_grid_search_results(
    results_df=results,
    x_col='beta',
    y_cols=['cross_entropy', 'correlation'],
    title='Grid Search Results',
    save_path='grid_search.png'
)
```

### Model Comparison
```python
from r2sfca.utils import plot_model_comparison

# Compare multiple models
fig = plot_model_comparison(
    results_dfs=[results1, results2, results3],
    labels=['Gaussian', 'Exponential', 'Power'],
    y_col='fij_flow_correlation',
    title='Model Comparison',
    save_path='model_comparison.png'
)
```

### Summary Table
```python
from r2sfca.utils import create_summary_table

# Create summary table
summary = create_summary_table(
    results_dfs=[results1, results2, results3],
    labels=['Gaussian', 'Exponential', 'Power'],
    metric='cross_entropy',
    minimize=True
)
```

## Examples

### Example 1: Basic Usage
```python
import pandas as pd
import numpy as np
from r2sfca import R2SFCA

# Create sample data
np.random.seed(42)
n_demand = 100
n_supply = 50

data = []
for i in range(n_demand):
    for j in range(n_supply):
        data.append({
            'DemandID': i,
            'SupplyID': j,
            'Demand': np.random.poisson(1000),
            'Supply': np.random.poisson(100),
            'TravelCost': np.random.exponential(10),
            'O_Fij': np.random.poisson(50)
        })

df = pd.DataFrame(data)

# Initialize model
model = R2SFCA(
    df=df,
    demand_col='Demand',
    supply_col='Supply',
    travel_cost_col='TravelCost',
    demand_id_col='DemandID',
    supply_id_col='SupplyID',
    observed_flow_col='O_Fij',
    decay_function='gaussian'
)

# Calculate accessibility scores
accessibility = model.access_score(beta=2.0)
print(f"Accessibility scores: {accessibility.describe()}")
```

### Example 2: Parameter Optimization
```python
# Grid search
results = model.search_fij(
    beta_range=(0.0, 5.0, 0.2),
    metrics=['cross_entropy', 'correlation', 'rmse']
)

# Find optimal beta
optimal_idx = results['cross_entropy'].idxmin()
optimal_beta = results.loc[optimal_idx, 'beta']
print(f"Optimal beta: {optimal_beta}")

# Adam optimization
optimization_result = model.solve_beta(
    metric='cross_entropy',
    method='adam',
    num_epochs=200
)
print(f"Optimized beta: {optimization_result['optimal_beta']}")
```

### Example 3: Model Comparison
```python
# Compare different decay functions
decay_functions = ['exponential', 'power', 'gaussian', 'sigmoid']
results_list = []
labels = []

for decay_func in decay_functions:
    model_temp = R2SFCA(
        df=df,
        demand_col='Demand',
        supply_col='Supply',
        travel_cost_col='TravelCost',
        demand_id_col='DemandID',
        supply_id_col='SupplyID',
        observed_flow_col='O_Fij',
        decay_function=decay_func
    )
    
    results = model_temp.search_fij(
        beta_range=(0.0, 3.0, 0.1),
        metrics=['cross_entropy', 'fij_flow_correlation']
    )
    
    results_list.append(results)
    labels.append(decay_func.title())

# Plot comparison
from r2sfca.utils import plot_model_comparison

fig = plot_model_comparison(
    results_dfs=results_list,
    labels=labels,
    y_col='fij_flow_correlation',
    title='Decay Function Comparison'
)
```

## Advanced Usage

### Custom Decay Function Parameters
```python
# Gaussian decay with custom d0 parameter
model = R2SFCA(df, decay_function='gaussian')
fij = model.fij(beta=2.0, d0=30.0)  # Custom d0 value

# Sigmoid decay with custom steepness
model = R2SFCA(df, decay_function='sigmoid')
fij = model.fij(beta=1.5, steepness=5.0)  # Custom steepness
```

### Multiple Parameter Optimization
```python
# Grid search with second parameter
results = model.search_fij(
    beta_range=(0.0, 3.0, 0.1),
    param2_range=(1.0, 10.0, 0.5),  # For sigmoid steepness
    metrics=['cross_entropy', 'correlation']
)
```

### Custom Evaluation Metrics
```python
# Use custom metrics
results = model.search_fij(
    beta_range=(0.0, 3.0, 0.1),
    metrics=['cross_entropy', 'rmse', 'mae', 'fij_flow_correlation']
)
```

## Performance Considerations

- For large datasets, consider using the Adam optimizer instead of grid search
- The package uses vectorized operations for efficiency
- Memory usage scales with the number of demand-supply pairs
- Consider sampling for very large datasets during parameter optimization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this package in your research, please cite:

```
@article{r2sfca2025,
   author = {Liu, Lingbo and Wang, Fahui},
   title = {Reconciling 2SFCA and i2SFCA via distance decay parameterization},
   journal = {International Journal of Geographical Information Science},
   pages = {1-18},
   note = {doi: 10.1080/13658816.2025.2562255},
   ISSN = {1365-8816},
   DOI = {10.1080/13658816.2025.2562255},
   url = {https://doi.org/10.1080/13658816.2025.2562255},
   year = {2025},
   type = {Journal Article}
}
```

## Support

For questions and support, please open an issue on GitHub or contact the development team.
