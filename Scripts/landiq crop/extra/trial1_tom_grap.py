# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 20:20:18 2024

@author: armen
"""

import pandas as pd

usda_crops = pd.read_csv('../../Datasets/econ_crop_data/processed_usda_crops_18_22.csv', index_col=0)
usda_crops = usda_crops[['Crop Name','County','HR_NAME', 'price_2020','Acres_2020','yield_2020']]
usda_crops['County'] = usda_crops['County'].str.title()

crop_name = 'tomatoes'
def process_crop(crop_name, usda_crops):
    # Filter the crop and remove unwanted rows
    crop_data = usda_crops[usda_crops["Crop Name"].str.contains(crop_name, case=False, na=False)]
    crop_data = crop_data.dropna()
    crop_data = crop_data[~crop_data['Crop Name'].str.contains(f"{crop_name} Unspecified", case=False, na=False)]
    crop_data = crop_data[~crop_data['Crop Name'].str.contains(f"{crop_name} Raisin", case=False, na=False)]
    crop_data['Crop_OpenAg'] = crop_name.capitalize()
    
    # Calculate total harvested acres by county
    county_totals = crop_data.groupby('County')['Acres_2020'].sum().reset_index()
    county_totals = county_totals.rename(columns={'Acres_2020': 'Total Acres'})
    crop_data = pd.merge(crop_data, county_totals, on='County')
    
    # Calculate the percentage of each crop and weighted price/yield
    crop_data['Percentage'] = crop_data['Acres_2020'] / crop_data['Total Acres']
    crop_data['Weighted Price'] = crop_data['price_2020'] * crop_data['Percentage']
    crop_data['Weighted Yield'] = crop_data['yield_2020'] * crop_data['Percentage']
    
    if crop_name == 'tomatoes':
        county_aggregates = crop_data.groupby(['County','HR_NAME']).agg(
                Percentage_Processing=('Percentage', lambda x: x[crop_data['Crop Name'].str.contains("Processing")].sum()),
                Percentage_Fresh=('Percentage', lambda x: x[crop_data['Crop Name'].str.contains("Fresh Market")].sum()),
                Acres = ('Total Acres', 'sum'),
                Weighted_Price=('Weighted Price', 'sum'),
                Weighted_Yield=('Weighted Yield', 'sum'),).reset_index()
    elif crop_name == 'grapes':
        county_aggregates = crop_data.groupby(['County','HR_NAME']).agg(
                Percentage_Wine=('Percentage', lambda x: x[crop_data['Crop Name'].str.contains("Wine")].sum()),
                Percentage_Table=('Percentage', lambda x: x[crop_data['Crop Name'].str.contains("Table")].sum()),
                Acres = ('Total Acres', 'sum'),
                Weighted_Price=('Weighted Price', 'sum'),
                Weighted_Yield=('Weighted Yield', 'sum')).reset_index()
        
    county_aggregates = county_aggregates.rename(columns={'Weighted_Price': 'price_2020', 'Weighted_Yield': 'yield_2020'})
    county_aggregates['Crop_OpenAg'] = crop_name.capitalize()
    # county_aggregates['County'] = county_aggregates['County'].str.title()

    return county_aggregates

tomatoes_aggregates = process_crop("tomatoes", usda_crops)
grapes_aggregates = process_crop("grapes", usda_crops)

tomatoes_aggregates = tomatoes_aggregates.set_index(['County', 'HR_NAME', 'Crop_OpenAg'])
grapes_aggregates = grapes_aggregates.set_index(['County', 'HR_NAME', 'Crop_OpenAg'])

# Concatenate the DataFrames on axis=1
merged_aggregates = pd.concat([tomatoes_aggregates, grapes_aggregates], axis=1)
merged_aggregates = (merged_aggregates.T.groupby(level=0).sum(min_count=1).T).reset_index()
#%%
# Process Tomatoes Data
# =====================
# Split the DataFrame into Fresh Market and Processing categories
fresh_df = (usda_crops[usda_crops["Crop Name"] == "Tomatoes Fresh Market"])
processing_df = (usda_crops[usda_crops["Crop Name"] == "Tomatoes Processing"])

# Rename columns to specify fresh and processing categories
fresh_df = fresh_df.rename(columns={
        "price_2020": "price_fresh",
        "Acres_2020": "acres_fresh",
        "yield_2020": "yield_fresh"})

processing_df = processing_df.rename(columns={
        "price_2020": "price_processing",
        "Acres_2020": "acres_processing",
        "yield_2020": "yield_processing"})

fresh_df = fresh_df.drop('Crop Name',axis=1)
processing_df = processing_df.drop('Crop Name',axis=1)
# Merge the two DataFrames based on County
result_tomatoes = pd.merge(fresh_df, processing_df, how="outer", on=['County','HR_NAME'])
result_tomatoes['Crop_OpenAg'] = 'Tomatoes'

# Process Grapes Data
# ====================
# Separate data by grape type (Table, Wine, Raisin)
table_df = (usda_crops[usda_crops["Crop Name"] == "Grapes Table"])
wine_df = (usda_crops[usda_crops["Crop Name"] == "Grapes Wine"])
raisin_df = (usda_crops[usda_crops["Crop Name"] == "Grapes Raisin"])

# Rename columns for each grape type for clarity
table_df = table_df.rename(
    columns={
        "price_2020": "price_table",
        "Acres_2020": "acres_table",
        "yield_2020": "yield_table"})

wine_df = wine_df.rename(columns={
        "price_2020": "price_wine",
        "Acres_2020": "acres_wine",
        "yield_2020": "yield_wine"})

# raisin_df = raisin_df.rename(columns={
#         "price_2020": "price_raisin",
#         "Acres_2020": "acres_raisin",
#         "yield_2020": "yield_raisin"})

table_df = table_df.drop('Crop Name',axis=1)
wine_df = wine_df.drop('Crop Name',axis=1)
# Merge the three grape DataFrames based on County
result_grapes = pd.merge(table_df, wine_df, how="outer", on=['County','HR_NAME'])
result_grapes['Crop_OpenAg'] = 'Grapes'
#%%
results_aggregates = pd.merge(result_grapes, result_tomatoes, how="outer", on=['County','HR_NAME','Crop_OpenAg'])
results_aggregates = results_aggregates.set_index(['County','HR_NAME','Crop_OpenAg']).dropna(how='all').reset_index()
merged_aggregates_1 = pd.merge(merged_aggregates, results_aggregates, how="outer", on=['County','HR_NAME','Crop_OpenAg'])

    