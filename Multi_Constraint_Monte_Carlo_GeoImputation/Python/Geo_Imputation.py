import knime.scripting.io as knio
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

# Read the two input tables
dfcancer = knio.input_tables[1].to_pandas()
dfpop = knio.input_tables[0].to_pandas()

columns = [
    'Male_50-', 'Male_50-65', 'Male_65+',
    'Female_50-', 'Female_50-65', 'Female_65+'
]

groups = ['W', 'B', 'I', 'H', 'A', 'O']

def process_fips(fips_code, dfcancer, dfpop):
    # Select cancer and population data for a specific FIPS code (county)
    cancer_data_fips = dfcancer[dfcancer['FIPS'] == fips_code]
    pop_data_fips = dfpop[dfpop['FIPS'] == fips_code]
    
    # Initialize an output DataFrame with NaNs for case counts
    dfcancer1 = pop_data_fips.copy()
    dfcancer1.iloc[:, 1:-1] = np.nan
    nbin = pop_data_fips.shape[0]

    # Process each race/ethnicity group separately
    for gp in groups:
        for col in columns:
            allrace_total = cancer_data_fips[f'{gp}_{col}'].values[0]
            population_weights = pop_data_fips[f'{gp}_{col}'].values

            # If the total cancer count is 0, set all related subgroup counts to 0
            if allrace_total == 0:
                dfcancer1[f'{gp}_{col}'] = 0
                continue

            # Create cumulative probability distribution based on subgroup populations
            cumulative_distribution = np.cumsum(population_weights / np.sum(population_weights))

            # Simulate random allocations: generate 1000 simulations
            simulations = np.random.rand(1000, int(allrace_total))

            # Allocate each case to a subgroup based on population share
            assigned_bins = np.searchsorted(cumulative_distribution, simulations, side='right')

            # Count the number of cases assigned to each ZCTA
            simulation_results = np.apply_along_axis(lambda x: np.bincount(x, minlength=nbin), axis=1, arr=assigned_bins)

            # Calculate the average distribution across simulations
            avg_simulation = np.mean(simulation_results, axis=0)

            # Select the simulation with the smallest variance from the mean
            variances = np.sum((simulation_results - avg_simulation) ** 2, axis=1)
            best_simulation = simulation_results[np.argmin(variances)]

            dfcancer1[f'{gp}_{col}'] = best_simulation

    # Aggregate results for each broader category (Male, Female, Age groups, Total) within each racial/ethnic group
    for X in groups:
        dfcancer1[f'{X}_Male'] = dfcancer1[[f'{X}_Male_50-', f'{X}_Male_50-65', f'{X}_Male_65+']].sum(axis=1)
        dfcancer1[f'{X}_Female'] = dfcancer1[[f'{X}_Female_50-', f'{X}_Female_50-65', f'{X}_Female_65+']].sum(axis=1)
        dfcancer1[f'{X}_50-'] = dfcancer1[[f'{X}_Male_50-', f'{X}_Female_50-']].sum(axis=1)
        dfcancer1[f'{X}_50-65'] = dfcancer1[[f'{X}_Male_50-65', f'{X}_Female_50-65']].sum(axis=1)
        dfcancer1[f'{X}_65+'] = dfcancer1[[f'{X}_Male_65+', f'{X}_Female_65+']].sum(axis=1)
        dfcancer1[f'{X}_Total'] = dfcancer1[[f'{X}_Male', f'{X}_Female']].sum(axis=1)

    # Aggregate results for AllRace category
    for col in columns:
        group_columns = [f'{x}_{col}' for x in groups]
        dfcancer1[f'AllRace_{col}'] = dfcancer1[group_columns].sum(axis=1)

    X = 'AllRace'
    dfcancer1[f'{X}_Male'] = dfcancer1[[f'{X}_Male_50-', f'{X}_Female_50-']].sum(axis=1)
    dfcancer1[f'{X}_Female'] = dfcancer1[[f'{X}_Male_50-65', f'{X}_Female_50-65']].sum(axis=1)
    dfcancer1[f'{X}_50-'] = dfcancer1[[f'{X}_Male_50-', f'{X}_Female_50-']].sum(axis=1)
    dfcancer1[f'{X}_50-65'] = dfcancer1[[f'{X}_Male_50-65', f'{X}_Female_50-65']].sum(axis=1)
    dfcancer1[f'{X}_65+'] = dfcancer1[[f'{X}_Male_65+', f'{X}_Female_65+']].sum(axis=1)
    dfcancer1[f'{X}_Total'] = dfcancer1[[f'{X}_Male', f'{X}_Female']].sum(axis=1)

    return dfcancer1

# Get the list of unique FIPS codes (counties)
fips_list = dfcancer['FIPS'].unique()

# Process each FIPS in parallel (n_jobs=-1 uses all available cores)
df_output_list = Parallel(n_jobs=-1)(delayed(process_fips)(fips, dfcancer, dfpop) for fips in fips_list)

# Concatenate the results into a single DataFrame
df_output = pd.concat(df_output_list, ignore_index=True)

# Output the processed data table
knio.output_tables[0] = knio.Table.from_pandas(df_output)
