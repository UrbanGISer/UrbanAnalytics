import knime.scripting.io as knio

# Input the data from the node
df = knio.input_tables[0].to_pandas()

# List of races
races = ['AllRace','W', 'B', 'I', 'A', 'H', 'O']

# Function to fill missing values by summing male and female subfields and age groups
def fill_missing_values(df, race):
    # Fill '_50-' by summing '_Male_50-' and '_Female_50-'
    idx_50_minus = df[f'{race}_50-'].isna()
    df.loc[idx_50_minus, f'{race}_50-'] = df.loc[idx_50_minus, [f'{race}_Male_50-', f'{race}_Female_50-']].sum(axis=1)

    # Fill '_50-65' by summing '_Male_50-65' and '_Female_50-65'
    idx_50_65 = df[f'{race}_50-65'].isna()
    df.loc[idx_50_65, f'{race}_50-65'] = df.loc[idx_50_65, [f'{race}_Male_50-65', f'{race}_Female_50-65']].sum(axis=1)

    # Fill '_65+' by summing '_Male_65+' and '_Female_65+'
    idx_65_plus = df[f'{race}_65+'].isna()
    df.loc[idx_65_plus, f'{race}_65+'] = df.loc[idx_65_plus, [f'{race}_Male_65+', f'{race}_Female_65+']].sum(axis=1)

    # Fill '_Male' by summing '_Male_50-', '_Male_50-65', and '_Male_65+'
    idx_male = df[f'{race}_Male'].isna()
    df.loc[idx_male, f'{race}_Male'] = df.loc[idx_male, [f'{race}_Male_50-', f'{race}_Male_50-65', f'{race}_Male_65+']].sum(axis=1)

    # Fill '_Female' by summing '_Female_50-', '_Female_50-65', and '_Female_65+'
    idx_female = df[f'{race}_Female'].isna()
    df.loc[idx_female, f'{race}_Female'] = df.loc[idx_female, [f'{race}_Female_50-', f'{race}_Female_50-65', f'{race}_Female_65+']].sum(axis=1)

    return df

# Apply the function for each race
for race in races:
    df = fill_missing_values(df, race)

# Output the processed data back to KNIME
knio.output_tables[0] = knio.Table.from_pandas(df)
