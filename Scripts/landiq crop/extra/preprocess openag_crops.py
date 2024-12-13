# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 17:17:52 2024

@author: armen
"""

import pickle
import pandas as pd


# Load HR crop analysis results
with open('../../Datasets/econ_crop_data/hr_crop_analysis_results.pkl', 'rb') as file:
    hr_crop_analysis_results = pickle.load(file)

usda_data = pd.read_csv('../../Datasets/econ_crop_data/processed_usda_crops_18_22.csv', index_col=0)
crop_combinations = pd.read_csv('../../Datasets/econ_crop_data/ca_county_openag_crop_combinations.csv', index_col=0)

# Extract proxy crops for each HR and create a unified DataFrame
proxy_crop_info_by_hr = {}
proxy_crops_list = []
for hr_name, result in hr_crop_analysis_results.items():
    proxy_crop_info_by_hr[hr_name] = result['agg_crops']
    proxy_crops_df = result['proxy crop']
    proxy_crops_df['HR_NAME'] = hr_name
    proxy_crops_list.append(proxy_crops_df)
proxy_crops_df = pd.concat(proxy_crops_list, ignore_index=True)
proxy_crops_df['Crop_OpenAg'] = proxy_crops_df['Crop_OpenAg'].str.replace('^WA_', '', regex=True)

# Extract economic data for proxy crops
usda_data = usda_data[['Crop Name', 'County', 'HR_NAME', 'Neighboring Counties', 
                       'Neighboring HR', 'price_2020', 'Production_2020', 'Acres_2020', 'yield_2020']]
usda_data['County'] = usda_data['County'].str.title()
usda_data = usda_data.merge(proxy_crops_df, how='outer', on=['Crop Name', 'HR_NAME'])
usda_data = usda_data.merge(crop_combinations, on=['Crop_OpenAg', 'County'], how='right')
usda_data.rename(columns={
    'Crop Name': 'usda_crop',
    'HR_NAME_y': 'HR_NAME',
    'Neighboring Counties_y': 'Neighboring Counties',
    'Neighboring HR_y': 'Neighboring HR'
}, inplace=True)
usda_data = usda_data[['Crop_OpenAg', 'usda_crop', 'County', 'HR_NAME', 'Neighboring Counties', 'Neighboring HR', 'price_2020', 'Production_2020', 'Acres_2020', 'yield_2020']]

#%%
# this is for exceptional crops (tomato and grapes) where we're further subclassfying, we get fraction price and yield 
# Separate and process tomatoes and grapes
def process_crop_type(data, crop_name_1, crop_name_2, rename_map_1, rename_map_2, crop_label):
    """Helper function to process and merge crop types."""
    crop_1 = data[data['Crop Name'] == crop_name_1].rename(columns=rename_map_1).drop('Crop Name', axis=1)
    crop_2 = data[data['Crop Name'] == crop_name_2].rename(columns=rename_map_2).drop('Crop Name', axis=1)
    combined = pd.merge(crop_1, crop_2, how='outer', on=['County', 'HR_NAME'])
    combined['Crop_Type'] = crop_label
    return combined

# Load and filter USDA crop data
crop_data_path = '../../Datasets/econ_crop_data/processed_usda_crops_18_22.csv'
crop_data = pd.read_csv(crop_data_path, index_col=0)
crop_data = crop_data[['Crop Name', 'County', 'HR_NAME', 'price_2020', 'Acres_2020', 'yield_2020']]
crop_data['County'] = crop_data['County'].str.title()

# Separate tomatoes by category (Fresh Market and Processing)
fresh_tomatoes = crop_data[crop_data["Crop Name"] == "Tomatoes Fresh Market"].rename(
    columns={"price_2020": "price_1", "Acres_2020": "acres_1", "yield_2020": "yield_1"}).drop('Crop Name', axis=1)
processing_tomatoes = crop_data[crop_data["Crop Name"] == "Tomatoes Processing"].rename(
    columns={"price_2020": "price_2", "Acres_2020": "acres_2", "yield_2020": "yield_2"}).drop('Crop Name', axis=1)
tomatoes_split = pd.merge(fresh_tomatoes, processing_tomatoes, how="outer", on=['County', 'HR_NAME'])
tomatoes_split['Crop_Type'] = 'Tomatoes'

# Separate grapes by type (Table and Wine)
wine_grapes = crop_data[crop_data["Crop Name"] == "Grapes Wine"].rename(
    columns={"price_2020": "price_1", "Acres_2020": "acres_1", "yield_2020": "yield_1"}).drop('Crop Name', axis=1)
table_grapes = crop_data[crop_data["Crop Name"] == "Grapes Table"].rename(
    columns={"price_2020": "price_2", "Acres_2020": "acres_2", "yield_2020": "yield_2"}).drop('Crop Name', axis=1)

grapes_split = pd.merge(wine_grapes, table_grapes, how="outer", on=['County', 'HR_NAME'])
grapes_split['Crop_Type'] = 'Grapes'

# Combine data and clean up
combined_crops = pd.concat([grapes_split, tomatoes_split])
combined_crops['total_acres'] = combined_crops[['acres_1', 'acres_2']].sum(axis=1, skipna=True)
combined_crops['fraction_1'] = combined_crops['acres_1'] / combined_crops['total_acres']
combined_crops['fraction_2'] = 1 - combined_crops['fraction_1']
combined_crops.rename(columns={'Crop_Type':'Crop_OpenAg'},inplace=True)
combined_crops = combined_crops.set_index(['County', 'HR_NAME', 'Crop_OpenAg']).dropna(how='all').reset_index()

# Map neighboring counties and HRs
geo_data = pd.read_csv('../../Datasets/econ_crop_data/counties_hr_neighbors.csv')
county_neighbors = pd.Series(geo_data['Neighboring Counties'].values, index=geo_data['County']).to_dict()
hr_neighbors = pd.Series(geo_data['Neighboring HR'].values, index=geo_data['HR_NAME']).to_dict()
combined_crops['Neighboring Counties'] = combined_crops['County'].map(county_neighbors)
combined_crops['Neighboring HR'] = combined_crops['HR_NAME'].map(hr_neighbors)

#%%
# Merge with USDA crops
meta_crop_data = pd.merge(
    usda_data, combined_crops, 
    how='outer', on=['County', 'HR_NAME', 'Crop_OpenAg', 'Neighboring Counties', 'Neighboring HR'])

meta_crop_data.to_csv('../../Datasets/econ_crop_data/processed_usda_crops_20.csv')

