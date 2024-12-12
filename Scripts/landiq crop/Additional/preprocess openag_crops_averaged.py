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
## get 5-yr average (2018 to 2022) of price yield acres and production
usda_crops_av = pd.melt(usda_data, id_vars=['County', 'Crop Name', 'HR_NAME', 'Neighboring Counties','Neighboring HR', 'Unit_2018'],
                    value_vars=
                    ['price_2018', 'price_2019', 'price_2020','price_2021', 'price_2022', 
                     'yield_2018', 'yield_2019', 'yield_2020','yield_2021', 'yield_2022', 
                     'Acres_2018', 'Acres_2019', 'Acres_2020','Acres_2021', 'Acres_2022', 
                     'Production_2018', 'Production_2019','Production_2020', 'Production_2021', 'Production_2022'],
                    var_name='year_type', value_name='value')
# Extract year and type (price or yield) from the 'year_type' column
usda_crops_av['year'] = usda_crops_av['year_type'].str.extract(r'(\d{4})')  # Extract year (e.g., 2018, 2019)
usda_crops_av['type'] = usda_crops_av['year_type'].str.extract(r'(price|yield|Acres|Production)')  # Extract price or yield
#transform back to original format
usda_crops_av = usda_crops_av.pivot_table(index=["County", "Crop Name", "HR_NAME", "Neighboring Counties", "Neighboring HR"], columns="type", values="value", aggfunc="mean").reset_index()

usda_crops_av = usda_crops_av[['Crop Name', 'County', 'HR_NAME', "Neighboring Counties", "Neighboring HR", 'price', 'Production', 'Acres','yield']]
usda_crops_av.columns = ['Crop Name', 'County', 'HR_NAME', "Neighboring Counties", "Neighboring HR", 'price_2020', 'Production_2020', 'Acres_2020', 'yield_2020']
usda_crops_av = usda_crops_av.dropna(subset=['Acres_2020','price_2020']) # drop nan rows because we cant do weighted average if either of this two are missing
usda_data = usda_crops_av
#%%
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

