import knime.scripting.io as knio
import numpy as np
from joblib import Parallel, delayed


### Input Data
# Read Data for cancer and population at the target level 
# and incidence at the upper level
df_target_cancer = knio.input_tables[0].to_pandas()
df_target_pop = knio.input_tables[1].to_pandas()
df_upper_incidence = knio.input_tables[2].to_pandas()  # State incidence data (single row)


### Define Population Subgroups in the Loop
groups = ['AllRace','W','B', 'I', 'A', 'H', 'O']
# groups = ['AllRace']

### Main Funciton
def process_group(X, df_target_cancer, df_upper_incidence, df_target_pop):
    print(f"Processing {X}")

    columns = [
        f'{X}_Total', f'{X}_50-', f'{X}_50-65', f'{X}_65+',
        f'{X}_Male', f'{X}_Male_50-', f'{X}_Male_50-65', f'{X}_Male_65+',
        f'{X}_Female', f'{X}_Female_50-', f'{X}_Female_50-65', f'{X}_Female_65+'
    ]

    categories = [
        f'{X}_Male_50-', f'{X}_Male_50-65', f'{X}_Male_65+',
        f'{X}_Female_50-', f'{X}_Female_50-65', f'{X}_Female_65+'
    ]
    overall_incidence = df_upper_incidence[categories].iloc[0].values.astype(float)

    # Step 1:  Create constrains for Handle deterministic values
    def constrains(df_target_cancer):
        # Step 1: Identify rows with missing values in the specified cancer columns
        cancer_missing_rows = df_target_cancer[df_target_cancer[columns].isna().any(axis=1)].copy()
        # Step 2: Sort both dataframes by FIPS to ensure alignment
        cancer_missing_rows.sort_values(by='FIPS', inplace=True)
        cancer_missing_rows.reset_index(drop=True, inplace=True)
        # Step 3:Prepare data matrices
        cancer_data = cancer_missing_rows[categories].values.astype(float)     
        # Step 4: Define constraints based on higher-level groupings
        county_totals = cancer_missing_rows[f'{X}_Total'].values.astype(float)
        male_totals = cancer_missing_rows[f'{X}_Male'].values.astype(float)
        female_totals = cancer_missing_rows[f'{X}_Female'].values.astype(float)
        age_50_totals = cancer_missing_rows[[f'{X}_50-']].values.astype(float)
        age_50_65_totals = cancer_missing_rows[[f'{X}_50-65']].values.astype(float)
        age_65_totals = cancer_missing_rows[[f'{X}_65+']].values.astype(float)
          
        return cancer_missing_rows, cancer_data, county_totals, male_totals, female_totals, age_50_totals, age_50_65_totals, age_65_totals

    # Step 2:  Fill missing values using both row and column constraints
    def fill_missing_values(df_target_cancer):
        cancer_missing_rows, cancer_data,  county_totals, male_totals, female_totals, age_50_totals, age_50_65_totals, age_65_totals = constrains(df_target_cancer)
        n_rows, n_cols = cancer_data.shape
        
        # # Step A: Row-wise filling based on male, female, and age totals
        for i in range(n_rows):
            row = cancer_data[i, :]

            # Known sums for each category (male and female)            
            known_male_sum = np.nansum(row[0:3])
            known_female_sum = np.nansum(row[3:6])

            # Fill in missing male values
            male_missing_indices = np.where(np.isnan(row[0:3]))[0]
            if len(male_missing_indices) == 1:
                row[male_missing_indices[0]] = male_totals[i] - known_male_sum

            female_missing_indices = np.where(np.isnan(row[3:6]))[0]
            if len(female_missing_indices) == 1:
                row[3 + female_missing_indices[0]] = female_totals[i] - known_female_sum

            if np.isnan(row[0]) and not np.isnan(row[3]):
                row[0] = age_50_totals[i] - row[3]
            elif np.isnan(row[3]) and not np.isnan(row[0]):
                row[3] = age_50_totals[i] - row[0]

            if np.isnan(row[1]) and not np.isnan(row[4]):
                row[1] = age_50_65_totals[i] - row[4]
            elif np.isnan(row[4]) and not np.isnan(row[1]):
                row[4] = age_50_65_totals[i] - row[1]

            if np.isnan(row[2]) and not np.isnan(row[5]):
                row[2] = age_65_totals[i] - row[5]
            elif np.isnan(row[5]) and not np.isnan(row[2]):
                row[5] = age_65_totals[i] - row[2]


        # Step B: After filling missing values, update the original df_target_cancer
        for i, fips_code in enumerate(cancer_missing_rows['FIPS']):
            mask = df_target_cancer['FIPS'] == fips_code
            df_target_cancer.loc[mask, categories] = cancer_data[i, :]

        return df_target_cancer, cancer_data
    
    # Step 3: Call the updated function with both row and column constraints
    df_target_cancer, cancer_data = fill_missing_values(df_target_cancer)

    if not np.isnan(cancer_data).any():
        return df_target_cancer[categories]

    # Step 4: if cancer_data still contains missing value, update constraint and  continue simulation
    cancer_missing_rows, cancer_data, county_totals, male_totals, female_totals, age_50_totals, age_50_65_totals, age_65_totals = constrains(df_target_cancer)

    # Step 5: Align population data for the missing counties using FIPS codes
    cancer_missing_pop = df_target_pop[df_target_pop['FIPS'].isin(cancer_missing_rows['FIPS'])].copy()
    pop_data = cancer_missing_pop[categories].values.astype(float)   
    fillable_mask = np.isnan(cancer_data) 
    overall_incidence = df_upper_incidence[categories].iloc[0].values

    # Step 6: update constraints
    # Step 6A Update county_totals by subtracting the sum of known values (row sums)

    row_sums = np.nansum(cancer_data, axis=1)
    county_totals -= row_sums

    # Step 6B Update male_totals by subtracting the sum of known values for male categories (columns 0, 1, 2)
    male_sums = np.nansum(cancer_data[:, 0:3], axis=1)
    male_totals -= male_sums
    female_sums = np.nansum(cancer_data[:, 3:6], axis=1)
    female_totals -= female_sums
    # Step 6C Update age group totals by subtracting known values
    age_50_sums = np.nansum(cancer_data[:, [0, 3]], axis=1)
    age_50_totals = age_50_totals.flatten().astype(float)
    age_50_totals -= age_50_sums 

    age_50_65_sums = np.nansum(cancer_data[:, [1, 4]], axis=1)
    age_50_65_totals = age_50_65_totals.flatten().astype(float)
    age_50_65_totals -= age_50_65_sums

    age_65_sums = np.nansum(cancer_data[:, [2, 5]], axis=1)
    age_65_totals = age_65_totals.flatten().astype(float)
    age_65_totals -= age_65_sums 


    # Step 7: Preparation for simulation 
    cancer_data_sim = np.copy(cancer_data)
    county_totals_sim, male_totals_sim, female_totals_sim, age_50_totals_sim, age_50_65_totals_sim, age_65_totals_sim,  fillable_mask_sim = (
        county_totals.copy(), male_totals.copy(), female_totals.copy(), age_50_totals.copy(), age_50_65_totals.copy(), age_65_totals.copy(), fillable_mask.copy()
    )
    # Step 7A Set massive assingment portion
    n_rows, n_cols = cancer_data_sim.shape
    # Initialize cancer_data by setting missing values to 0
    cancer_data_sim[np.isnan(cancer_data_sim)] = 0

    # Probability based on population weighted by incidence
    adjusted_populations = np.copy(pop_data) * overall_incidence 

    # Step 7B: update constraints by simulation case times
    n_sim_pre=20000
    nanvalue =county_totals_sim.sum()-np.nansum(cancer_data_sim)
    if nanvalue > n_sim_pre:
        ratio = (nanvalue - n_sim_pre) / nanvalue

        for i in range(len(cancer_data_sim)):
            remaining_total = county_totals[i]
            distribute_90 = int(remaining_total * ratio)
            proportions = adjusted_populations[i] / adjusted_populations[i].sum()
            fill_values = np.floor(proportions * distribute_90).astype(int)
            for j in range(len(categories)):
                if fillable_mask[i, j]:
                    cancer_data_sim[i, j] = fill_values[j]
            
            masked_fill_values = np.where(fillable_mask[i, :], fill_values, 0)   
            county_totals_sim[i] -= np.sum(masked_fill_values)
            male_totals_sim[i] -= np.sum(masked_fill_values[0:3])
            female_totals_sim[i] -= np.sum(masked_fill_values[3:6])
            age_50_totals_sim[i] -=np.sum(masked_fill_values[[0, 3]])
            age_50_65_totals_sim[i] -=np.sum(masked_fill_values[[1, 4]])
            age_65_totals_sim[i] -=np.sum(masked_fill_values[[2, 5]])

    num_simulations = 100
    simulation_results = []

    for sim in range(num_simulations):
        cancer_data_simx = np.copy(cancer_data_sim)
        county_totals_simx = county_totals_sim.copy().astype(float)
        male_totals_simx= male_totals_sim.copy().astype(float)
        female_totals_simx = female_totals_sim.copy().astype(float)
        age_50_totals_simx = age_50_totals_sim.copy().astype(float)
        age_50_65_totals_simx = age_50_65_totals_sim.copy().astype(float)
        age_65_totals_simx = age_65_totals_sim.copy().astype(float)
        fillable_mask_simx = fillable_mask_sim.copy()

        n_rows, n_cols = cancer_data_simx.shape
        cancer_data_simx[np.isnan(cancer_data_simx)] = 0

        constraints_met = False
        k = 0
        while not constraints_met:  # 添加最大迭代次数限制
            k += 1
            if k % 1000 == 0:  # 每1000次迭代打印一次进度
                print(f"Iteration {k}")

            if (county_totals_simx <= 0).all() :
                break
            # Adjusted probability
            adjusted_populations = np.copy(pop_data) * overall_incidence
            adjusted_populations *= fillable_mask_simx

            # Dynamic generation probability
            row_weights = county_totals_simx / county_totals_simx.sum()  
            col_weights = np.ones(n_cols)
            joint_probabilities = np.outer(row_weights, col_weights) * adjusted_populations

            # Unfilled cells
            valid_indices = np.where(fillable_mask_simx.flatten())[0]
            if len(valid_indices) == 0:
                break
            valid_joint_probabilities = joint_probabilities.flatten()[valid_indices]
            if valid_joint_probabilities.sum() == 0:
                break

            cumulative_probabilities = np.cumsum(valid_joint_probabilities / valid_joint_probabilities.sum())
            random_number = np.random.rand()
            selected_index_in_valid = np.searchsorted(cumulative_probabilities, random_number)

            if selected_index_in_valid >= len(valid_indices):
                break

            selected_index = valid_indices[selected_index_in_valid]
            i, j = divmod(selected_index, n_cols)

            cancer_data_simx[i, j] += 1

            county_totals_simx[i] = max(0, county_totals_simx[i] - 1)

            # Only update if not NA
            if not np.isnan(male_totals_simx[i]):
                male_totals_simx[i] = max(0, male_totals_simx[i] - (1 if j in [0, 1, 2] else 0))

            if not np.isnan(female_totals_simx[i]):
                female_totals_simx[i] = max(0, female_totals_simx[i] - (1 if j in [3, 4, 5] else 0))

            if not np.isnan(age_50_totals_simx[i]) and j in [0, 3]:
                age_50_totals_simx[i] = max(0, age_50_totals_simx[i] - 1)
            elif not np.isnan(age_50_65_totals_simx[i]) and j in [1, 4]:
                age_50_65_totals_simx[i] = max(0, age_50_65_totals_simx[i] - 1)
            elif not np.isnan(age_65_totals_simx[i]) and j in [2, 5]:
                age_65_totals_simx[i] = max(0, age_65_totals_simx[i] - 1)

            if county_totals_simx[i] <= 0:
                fillable_mask_simx[i, :] = False
            if male_totals_simx[i] <= 0:
                fillable_mask_simx[i, 0:3] = False
            if female_totals_simx[i] <= 0:
                fillable_mask_simx[i, 3:6] = False
            if age_50_totals_simx[i] <= 0:
                fillable_mask_simx[i, [0, 3]] = False
            if age_50_65_totals_simx[i] <= 0:
                fillable_mask_simx[i, [1, 4]] = False
            if age_65_totals_simx[i] <= 0:
                fillable_mask_simx[i, [2, 5]] = False

            constraints_met = np.all(fillable_mask_simx == False)

        simulation_results.append(cancer_data_simx)

    if len(simulation_results) > 0:
        variances = [np.var(simulation_result) for simulation_result in simulation_results]
        best_simulation_index = np.argmin(variances)
        best_simulation = simulation_results[best_simulation_index]

        for i, fips_code in enumerate(cancer_missing_rows['FIPS']):
            mask = df_target_cancer['FIPS'] == fips_code
            df_target_cancer.loc[mask, categories] = best_simulation[i, :]

    return df_target_cancer[categories]

# Run parallel processing
results = Parallel(n_jobs=-1)(
    delayed(process_group)(X, df_target_cancer.copy(), df_upper_incidence, df_target_pop) for X in groups
)

# Merge results back to the original dataframe
for result, group in zip(results, groups):
    df_target_cancer.update(result)

knio.output_tables[0] = knio.Table.from_pandas(df_target_cancer)