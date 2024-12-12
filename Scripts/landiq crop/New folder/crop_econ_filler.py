# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 23:24:16 2024

@author: armen
"""
# This code fills missing price values using a hierarchical approach by
# calculating average prices for neighboring counties, HRs, and the state 

import pandas as pd
import ast

crop_data = pd.read_csv('../../Datasets/econ_crop_data/processed_usda_crops_20.csv')

# Convert string representations of lists into actual lists for 'Neighboring Counties' and 'Neighboring HR'
crop_data['Neighboring Counties'] = crop_data['Neighboring Counties'].apply(ast.literal_eval)
crop_data['Neighboring HR'] = crop_data['Neighboring HR'].apply(ast.literal_eval)


# =============================================================================
# 1. Calculate average price for neighboring counties
# =============================================================================

# Explode 'Neighboring Counties' to create separate rows for each county
expanded_crop_data = crop_data.explode('Neighboring Counties')

# Merge with crop price data for neighboring counties
merged_crop_data = pd.merge(
    expanded_crop_data,
    crop_data[['Crop_OpenAg', 'County', 'price_2020']],
    left_on=['Neighboring Counties', 'Crop_OpenAg'],
    right_on=['County', 'Crop_OpenAg'],
    suffixes=('', '_neighbor'),
    how='left'
)
merged_crop_data = merged_crop_data[['Crop_OpenAg', 'usda crop', 'County', 'HR_NAME', 'ACRES', 'price_2020', 'Neighboring Counties', 'Neighboring HR', 'price_2020_neighbor']]

# Calculate the average price of neighboring counties for each crop and county
avg_neighbor_prices = merged_crop_data.groupby(['Crop_OpenAg', 'County'])['price_2020_neighbor'].mean()
avg_neighbor_prices_dict = avg_neighbor_prices.to_dict()

# Map the calculated average prices back to the original DataFrame
crop_data['neighboring_county_avg_price'] = crop_data.set_index(['Crop_OpenAg', 'County']).index.map(avg_neighbor_prices_dict)


# =============================================================================
# 2. Calculate average price for each crop in HRs
# =============================================================================

# Calculate the HR average prices and convert to a dictionary
hr_avg_prices = crop_data.groupby(['Crop_OpenAg', 'HR_NAME'])['price_2020'].mean()
hr_avg_prices_dict = hr_avg_prices.to_dict()

# Map HR average prices back to the original DataFrame
crop_data['hr_avg_price'] = crop_data.set_index(['Crop_OpenAg', 'HR_NAME']).index.map(hr_avg_prices_dict)

# =============================================================================
# 3. Calculate average price for neighboring HRs
# =============================================================================

counties_hr = pd.read_csv('../../Datasets/econ_crop_data/counties_hr_neighbors.csv')

# Create a DataFrame of HR average prices
hr_avg_prices_df = pd.DataFrame(hr_avg_prices).reset_index()

# Merge HR prices with neighboring HR data
hr_avg_prices_with_neighbors = hr_avg_prices_df.merge(
    counties_hr[['HR_NAME', 'Neighboring HR']],
    how='left',
    on='HR_NAME'
).drop_duplicates()


# Convert 'Neighboring HR' to actual lists and explode DataFrame to create a row for each neighboring HR
# Merge prices from neighboring HRs
hr_avg_prices_with_neighbors['Neighboring HR'] = hr_avg_prices_with_neighbors['Neighboring HR'].apply(ast.literal_eval)
expanded_hr_avg_prices = hr_avg_prices_with_neighbors.explode('Neighboring HR')
hr_avg_prices_with_neighbor_prices = expanded_hr_avg_prices.merge(
    hr_avg_prices_df[['Crop_OpenAg', 'HR_NAME', 'price_2020']],
    how='left',
    left_on=['Crop_OpenAg', 'Neighboring HR'],
    right_on=['Crop_OpenAg', 'HR_NAME'])
# Drop unnecessary columns and rename for clarity
hr_avg_prices_with_neighbor_prices = hr_avg_prices_with_neighbor_prices.drop(columns=['HR_NAME_y'])
hr_avg_prices_with_neighbor_prices = hr_avg_prices_with_neighbor_prices.rename(columns={
    'HR_NAME_x': 'HR_NAME',
    'price_2020_x': 'base_hr_price',
    'price_2020_y': 'neighbor_hr_price'})

# Calculate the mean price for neighboring HRs and map it back to the original DataFrame
mean_neighbor_hr_prices = hr_avg_prices_with_neighbor_prices.groupby(['Crop_OpenAg', 'HR_NAME'])['neighbor_hr_price'].mean()
mean_neighbor_hr_prices_dict = mean_neighbor_hr_prices.to_dict()

crop_data['neighboring_hr_avg_price'] = crop_data.set_index(['Crop_OpenAg', 'HR_NAME']).index.map(mean_neighbor_hr_prices_dict)

 
# =============================================================================
# 4. Calculate average price for each crop across the entire state
# =============================================================================
avg_state_prices = crop_data.groupby('Crop_OpenAg')['price_2020'].mean()
crop_data['state_avg_price'] = crop_data['Crop_OpenAg'].map(avg_state_prices)


# =============================================================================
# 5. Fill missing price values using a hierarchical approach, and track the source of each price
# =============================================================================
def fill_price(row):
    if pd.notna(row['price_2020']):
        return row['price_2020'], 'price_2020'
    elif pd.notna(row['neighboring_county_avg_price']):
        return row['neighboring_county_avg_price'], 'neighboring_county_avg_price'
    elif pd.notna(row['hr_avg_price']):
        return row['hr_avg_price'], 'hr_avg_price'
    else:
        return row['state_avg_price'], 'state_avg_price'

# Apply the fill_price function to create new columns
crop_data[['final_price', 'price_source']] = crop_data.apply(
    lambda row: pd.Series(fill_price(row)), axis=1)

# =============================================================================
# Calculate the total acres for each price source and determine the percentage of acres
# =============================================================================
acres_by_price_source = crop_data.groupby('price_source')['ACRES'].sum()
acres_percentage_by_price_source = (acres_by_price_source / acres_by_price_source.sum()) * 100

#%%
# same thing for yield
# Calculate average yield for neighboring counties in crop_data
exploded_crops = crop_data.explode('Neighboring Counties')

# Merge exploded DataFrame with crop yield data to associate neighboring county yields
merged_crops_yield = pd.merge(
    exploded_crops,
    crop_data[['Crop_OpenAg', 'County', 'yield_2020']],
    left_on=['Neighboring Counties', 'Crop_OpenAg'],
    right_on=['County', 'Crop_OpenAg'],
    suffixes=('', '_neighbor'),
    how='left'
)
merged_crops_yield = merged_crops_yield[['Crop_OpenAg', 'usda crop', 'County', 'HR_NAME', 'ACRES', 'yield_2020', 'Neighboring Counties', 'Neighboring HR', 'yield_2020_neighbor']]

# Calculate the average yield of neighboring counties for each crop and county and convert it to dict
average_neighbor_yields = merged_crops_yield.groupby(['Crop_OpenAg', 'County'])['yield_2020_neighbor'].mean()
average_neighbor_yields_dict = average_neighbor_yields.to_dict()

# Map the calculated average yields to the original DataFrame
crop_data['neighbor_county_avg_yield'] = crop_data.set_index(['Crop_OpenAg', 'County']).index.map(average_neighbor_yields_dict)

# Calculate average yield for each crop in HRs
hr_avg_yields = crop_data.groupby(['Crop_OpenAg', 'HR_NAME'])['yield_2020'].mean()
hr_avg_yields_dict = hr_avg_yields.to_dict()

# Map HR average yields to the original DataFrame
crop_data['hr_avg_yield'] = crop_data.set_index(['Crop_OpenAg', 'HR_NAME']).index.map(hr_avg_yields_dict)

# Calculate nearby average yield for each crop in HRs
counties_hr = pd.read_csv('../../Datasets/econ_crop_data/counties_hr_neighbors.csv')

hr_avg_yields_df = pd.DataFrame(hr_avg_yields).reset_index()

# Merge average yields with neighboring HR data and remove duplicates
hr_avg_yields_with_neighbors = hr_avg_yields_df.merge(
    counties_hr[['HR_NAME', 'Neighboring HR']],
    how='left',
    on='HR_NAME').drop_duplicates()

hr_avg_yields_with_neighbors['Neighboring HR'] = hr_avg_yields_with_neighbors['Neighboring HR'].apply(ast.literal_eval)

# Explode the DataFrame to create a row for each neighboring HR and merge yields from the neighboring HRs
average_yields_exploded = hr_avg_yields_with_neighbors.explode('Neighboring HR')
average_yields_with_neighbor_yields = average_yields_exploded.merge(
    hr_avg_yields_df[['Crop_OpenAg', 'HR_NAME', 'yield_2020']],
    how='left',
    left_on=['Crop_OpenAg', 'Neighboring HR'],
    right_on=['Crop_OpenAg', 'HR_NAME'])

# Drop unnecessary columns and rename for clarity
average_yields_with_neighbor_yields = average_yields_with_neighbor_yields.drop(columns=['HR_NAME_y'])
average_yields_with_neighbor_yields = average_yields_with_neighbor_yields.rename(columns={
    'HR_NAME_x': 'HR_NAME',
    'yield_2020_x': 'base_hr_yield',
    'yield_2020_y': 'neighbor_hr_yield'})

# Group by crop and HR, calculating the mean neighboring HR yield
mean_neighbor_yields_by_hr = average_yields_with_neighbor_yields.groupby(['Crop_OpenAg', 'HR_NAME'])['neighbor_hr_yield'].mean()
mean_neighbor_yields_by_hr_dict = mean_neighbor_yields_by_hr.to_dict()

crop_data['state_avg_yield'] = crop_data.set_index(['Crop_OpenAg', 'HR_NAME']).index.map(mean_neighbor_yields_by_hr_dict)

# Calculate average yield for each crop across the dataset and map the calculated averages back to the DataFrame
avg_state_yields = crop_data.groupby('Crop_OpenAg')['yield_2020'].mean()
crop_data['state_avg_yield'] = crop_data['Crop_OpenAg'].map(avg_state_yields)

# Fill missing yields with a hierarchical approach and track the source column
def fill_yield(row):
    if not pd.isna(row['yield_2020']):
        return row['yield_2020'], 'yield_2020'
    elif not pd.isna(row['neighbor_county_avg_yield']):
        return row['neighbor_county_avg_yield'], 'neighbor_county_avg_yield'
    elif not pd.isna(row['hr_avg_yield']):
        return row['hr_avg_yield'], 'hr_avg_yield'
    else:
        return row['state_avg_yield'], 'state_avg_yield'

# Apply the logic to create new columns
crop_data[['final_yield', 'yield_source']] = crop_data.apply(
    lambda row: pd.Series(fill_yield(row)), axis=1
)

# Calculate total acres by each yield source
yield_source_acres = crop_data.groupby('yield_source')['ACRES'].sum()

# Calculate the percentage of acres for each yield source
yield_source_percentage = (yield_source_acres / yield_source_acres.sum()) * 100

#%%
# crop_data = crop_data [['Crop_OpenAg', 'County', 'HR_NAME',
#                         'ACRES', 'Neighboring Counties', 'Neighboring HR', 'usda crop',
#                         'price_2020', 'final_price', 'price_source',
#                         'yield_2020', 'final_yield', 'yield_source']]

filtered_crop_data = crop_data[~crop_data['price_source'].isin(['price_2020'])]
filtered_crop_data = crop_data[~crop_data['HR_NAME'].isin(['San Joaquin River', 'Sacramento River', 'Tulare Lake'])]

crop_data = crop_data.iloc[:,1:]
crop_data.to_csv('../../Datasets/econ_crop_data/meta_crop_economic_data.csv')

crop_data = crop_data[['Crop_OpenAg', 'County', 'HR_NAME', 'ACRES','final_price','final_yield']]
crop_data.to_csv('../../Datasets/econ_crop_data/final_crop_economic_data.csv')
