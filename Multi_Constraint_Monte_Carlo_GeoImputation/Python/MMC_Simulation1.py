import knime.scripting.io as knio
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

# Input data
df_target_cancer = knio.input_tables[0].to_pandas()
df_target_pop = knio.input_tables[1].to_pandas()
df_upper_incidence = knio.input_tables[2].to_pandas()  # State incidence data (single row)

X = 'Total'

# Columns focused on the Total series
columns = [
    f'AllRace_{X}', f'W_{X}', f'B_{X}', f'I_{X}', 
    f'A_{X}', f'H_{X}', f'O_{X}'
]

# Categories for data filling
categories = [
    f'W_{X}', f'B_{X}', f'I_{X}', 
    f'A_{X}', f'H_{X}', f'O_{X}'
]

# Step 1: Create constraints for handling deterministic values
def constrains(df_target_cancer):
    # Identify rows with missing values in the specified cancer columns
    cancer_missing_rows = df_target_cancer[df_target_cancer[columns].isna().any(axis=1)].copy()
    cancer_missing_rows.sort_values(by='FIPS', inplace=True)
    cancer_missing_rows.reset_index(drop=True, inplace=True)

    # Prepare data matrices
    cancer_data = cancer_missing_rows[categories].values  # Missing cancer data to fill
    
    # Target totals for each category
    county_totals = cancer_missing_rows[f'AllRace_{X}'].values
    return cancer_missing_rows, cancer_data, county_totals

# Step 2: Function to fill missing values using both row and column constraints
def fill_missing_values(df_target_cancer):
    cancer_missing_rows, cancer_data, county_totals = constrains(df_target_cancer)
    n_rows, n_cols = cancer_data.shape

    # Row-wise filling based on Total series
    for i in range(n_rows):
        known_row_sum = np.nansum(cancer_data[i, :])
        row_missing_indices = np.where(np.isnan(cancer_data[i, :]))[0]

        if len(row_missing_indices) == 1:
            cancer_data[i, row_missing_indices[0]] = county_totals[i] - known_row_sum

    # Step 3: After filling missing values, update the original df_target_cancer
    for i, fips_code in enumerate(cancer_missing_rows['FIPS']):
        mask = df_target_cancer['FIPS'] == fips_code
        df_target_cancer.loc[mask, categories] = cancer_data[i, :]

    return df_target_cancer,cancer_missing_rows, cancer_data, county_totals

# Step 3: Call the updated function
df_target_cancer,cancer_missing_rows, cancer_data, county_totals  = fill_missing_values(df_target_cancer)

# Step 4: Proportional filling for missing counties
cancer_missing_pop = df_target_pop[df_target_pop['FIPS'].isin(cancer_missing_rows['FIPS'])].copy()
pop_data = cancer_missing_pop[categories].values
fillable_mask = np.isnan(cancer_data)
overall_incidence = df_upper_incidence[categories].iloc[0].values

nanvalue = county_totals.sum() - np.nansum(cancer_data)
adjusted_populations = pop_data * overall_incidence

# Step 5: Update County total
for i in range(len(cancer_data)):
    county_totals[i] -= np.nansum(cancer_data[i, :]) 


for i in range(len(cancer_data)):
    remaining_total = county_totals[i]
    ratio = (nanvalue - 3000) / nanvalue
    distribute_90 = int(remaining_total * ratio)
    proportions = adjusted_populations[i] / adjusted_populations[i].sum()
    fill_values = np.floor(proportions * distribute_90).astype(int)

    for j in range(len(categories)):
        if fillable_mask[i, j]:
            cancer_data[i, j] = fill_values[j]

    county_totals[i] -= np.sum(fill_values[fillable_mask[i, :]])


# Simulation function (from previous code)
def run_simulation():
    cancer_data_sim = np.copy(cancer_data)
    county_totals_sim = county_totals.copy()
    fillable_mask_sim = fillable_mask.copy()
    n_rows, n_cols = cancer_data_sim.shape
    cancer_data_sim[np.isnan(cancer_data_sim)] = 0

    while True:
        adjusted_populations = np.copy(pop_data) * overall_incidence
        adjusted_populations *= fillable_mask_sim

        row_weights = county_totals_sim / county_totals_sim.sum() if county_totals_sim.sum() != 0 else np.zeros_like(county_totals_sim)
        col_weights = np.ones(n_cols) / n_cols  # Equal column weights since no state-level constraints

        joint_probabilities = np.outer(row_weights, col_weights) * adjusted_populations
        valid_indices = np.where(fillable_mask_sim.flatten())[0]
        valid_joint_probabilities = joint_probabilities.flatten()[valid_indices]

        if valid_joint_probabilities.sum() == 0:
            break
        cumulative_probabilities = np.cumsum(valid_joint_probabilities / valid_joint_probabilities.sum())
        random_number = np.random.rand()
        selected_index_in_valid = np.searchsorted(cumulative_probabilities, random_number)

        selected_index = valid_indices[selected_index_in_valid]
        i, j = divmod(selected_index, n_cols)

        if county_totals_sim[i] > 0:
            cancer_data_sim[i, j] += 1
            county_totals_sim[i] -= 1

            if county_totals_sim[i] == 0:
                fillable_mask_sim[i, :] = False

        if np.all(fillable_mask_sim == False) or np.sum(county_totals_sim) == 0:
            break

    return cancer_data_sim

# Multi-process simulation execution using joblib
def run_simulations_with_joblib(num_simulations=100, n_jobs=-1):
    # Execute simulations in parallel
    results = Parallel(n_jobs=n_jobs)(
        delayed(run_simulation)() for _ in range(num_simulations)
    )
    return results

# Step 5: Run the simulation 1000 times using joblib
num_simulations = 200
simulations = run_simulations_with_joblib(num_simulations, n_jobs=-1) 

# Step 6: Calculate the average of all simulations
simulations_array = np.stack(simulations, axis=0)

# Mean
average_simulation = np.nanmean(simulations_array, axis=0)

# Step 7: Find the simulation with the smallest variance to the average
variances_to_average = [
    np.nanvar(sim - average_simulation) for sim in simulations
]


best_simulation_index = np.argmin(variances_to_average)
best_simulation = simulations[best_simulation_index]

# Step 8: Update the original DataFrame with the best simulation
for i, fips_code in enumerate(cancer_missing_rows['FIPS']):
    mask = df_target_cancer['FIPS'] == fips_code
    df_target_cancer.loc[mask, categories] = best_simulation[i, :]

# Output the updated DataFrame
knio.output_tables[0] = knio.Table.from_pandas(df_target_cancer)