# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 18:42:48 2024

@author: armen
"""

import pandas as pd
import geopandas as gpd
import numpy as np

# Load datasets
economic_data = pd.read_csv('../../Datasets/econ_crop_data/final_crop_economic_data.csv',index_col=0)
meta_landiq20 = gpd.read_file(r"C:\Users\armen\Documents\ArcGIS\Projects\COEQWAL\COEQWAL.gdb", layer='landiq20_CVID_GW_DU_SR')
crop_mapping = pd.read_excel("../../Datasets/econ_crop_data/bridge openag.xlsx", sheet_name='landiq20 & openag')
landiq20_columns = meta_landiq20.columns
# 'GSA_ID','DU_ID','Subregion','COUNTY','HYDRO_RGN'
#%%
landiq20 = meta_landiq20.copy()
# Selected column for grouping
grouping_column = 'DU_ID'
# Create crop mapping dictionary
openag_mapping_dict = crop_mapping.set_index('CROPTYP2')['Crop_OpenAg'].to_dict()
landiq20['Crop_OpenAg'] = landiq20['CROPTYP2'].map(openag_mapping_dict)

# Merge land use data with economic data
landiq20 = landiq20.merge(economic_data, left_on=['COUNTY', 'Crop_OpenAg'], right_on=['County', 'Crop_OpenAg'], how='left')
landiq20 = landiq20[['COUNTY', 'Crop_OpenAg', 'ACRES', 'GSA_Name', grouping_column , 
                             'price_2020', 'yield_2020', 'fraction_1', 'fraction_2', 
                             'price_1', 'yield_1', 'price_2', 'yield_2']]
# Group and calculate weighted values
def calculate_weighted_values(group):
    acres_sum = group['ACRES'].sum()
    return pd.Series({
        'Weighted_Price': (group['price_2020'] * group['ACRES']).sum() / acres_sum,
        'Weighted_Yield': (group['yield_2020'] * group['ACRES']).sum() / acres_sum,
        'Total_Acres': acres_sum,
        'Weighted_Fraction_1': (group['fraction_1'] * group['ACRES']).sum() / acres_sum,
        'Weighted_price_1': (group['price_1'] * group['ACRES']).sum() / acres_sum,
        'Weighted_price_2': (group['price_2'] * group['ACRES']).sum() / acres_sum,
        'Weighted_yield_1': (group['yield_1'] * group['ACRES']).sum() / acres_sum,
        'Weighted_yield_2': (group['yield_2'] * group['ACRES']).sum() / acres_sum
    })
landiq20_grouped = landiq20.groupby([grouping_column , 'Crop_OpenAg']).apply(calculate_weighted_values).reset_index()
landiq20_grouped = landiq20_grouped[
    (landiq20_grouped[grouping_column].str.strip() != '') &  # Remove rows where 'DU_ID' is empty
    (landiq20_grouped['Crop_OpenAg'] != 'Idle') &   # Remove rows where 'Crop_OpenAg' is 'Idle'
    (landiq20_grouped['Crop_OpenAg'] != 'na')              # Remove rows where 'DU_ID' is Na
]


# Split rows for tomatoes and grapes
def split_crop_rows(row):
    crop_map = {
        'Grapes': ('Grapes Wine', 'Grapes Table'),
        'Tomatoes': ('Tomatoes Fresh', 'Tomatoes Processing')}
    subcategories = crop_map.get(row['Crop_OpenAg'], None)
    if not subcategories:
        return [{
            grouping_column: row[grouping_column],
            'Crop_OpenAg': row['Crop_OpenAg'],
            'Total_Acres': row['Total_Acres'],
            'Weighted_Price': row['Weighted_Price'],
            'Weighted_Yield': row['Weighted_Yield']}]
    sub1_acres = row['Total_Acres'] * row['Weighted_Fraction_1']
    sub2_acres = row['Total_Acres'] - sub1_acres
    sub1_row = {
        grouping_column: row[grouping_column],
        'Crop_OpenAg': subcategories[0],
        'Total_Acres': sub1_acres,
        'Weighted_Price': row['Weighted_price_1'],
        'Weighted_Yield': row['Weighted_yield_1']}
    sub2_row = {
        grouping_column: row[grouping_column],
        'Crop_OpenAg': subcategories[1],
        'Total_Acres': sub2_acres,
        'Weighted_Price': row['Weighted_price_2'],
        'Weighted_Yield': row['Weighted_yield_2']}
    return [sub1_row, sub2_row]

# Split crops for 'Grapes' and 'Tomatoes'
split_crops = ['Grapes', 'Tomatoes']
split_rows_data = landiq20_grouped[landiq20_grouped['Crop_OpenAg'].isin(split_crops)]

split_rows = split_rows_data.apply(split_crop_rows, axis=1)
split_data = pd.DataFrame([row for rows in split_rows for row in rows])

# Non-split data
non_split_data = landiq20_grouped[~landiq20_grouped['Crop_OpenAg'].isin(split_crops)]

final_data = pd.concat([non_split_data, split_data], ignore_index=True)

# Adjust column names and assign final prices and yields for 'Pasture'
final_data = final_data[[grouping_column, 'Crop_OpenAg', 'Weighted_Price', 'Weighted_Yield', 'Total_Acres']]
final_data.columns = [grouping_column, 'Crop_OpenAg', 'final_price', 'final_yield', 'Total_Acres']
final_data.loc[final_data['Crop_OpenAg'] == 'Pasture', ['final_price', 'final_yield']] = [215, 3.5]

# Categorize crops as Perennial or Non-Perennial
final_data['Crop_Type'] = np.where(
    final_data['Crop_OpenAg'].isin(['Almonds', 'Grapes Wine', 'Grapes Table', 'Orchards', 'Pistachios', 'Subtropical', 'Walnuts', 'Young Perennial']),
    'Perennial',
    'Non-Perennial')

# Split the data into perennial and non-perennial
perennial_data = final_data[final_data['Crop_Type'] == 'Perennial']
non_perennial_data = final_data[final_data['Crop_Type'] == 'Non-Perennial']

# Calculate young perennial area and merge it
young_perennial_area = perennial_data[perennial_data['Crop_OpenAg'] == 'Young Perennial'][[grouping_column, 'Total_Acres']]
non_young_perennial = perennial_data[perennial_data['Crop_OpenAg'] != 'Young Perennial']
non_young_perennial['Crop_Percentage'] = non_young_perennial.groupby(grouping_column)['Total_Acres'].transform(lambda x: (x / x.sum()) * 100)
perennial_data = pd.merge(perennial_data, non_young_perennial[[grouping_column, 'Crop_OpenAg', 'Crop_Percentage']], on=[grouping_column, 'Crop_OpenAg'])
perennial_data = pd.merge(perennial_data, young_perennial_area, on=grouping_column, how='left')

# Fill NaN values for young perennial area and calculate area adjustments
perennial_data['Total_Acres_y'] = perennial_data['Total_Acres_y'].fillna(0)
perennial_data['Area_Adjustment'] = (perennial_data['Crop_Percentage'] / 100) * perennial_data['Total_Acres_y']

# Adjust acres and finalize the dataset
perennial_data['Adjusted_Acres'] = perennial_data['Total_Acres_x'] + perennial_data['Area_Adjustment']
perennial_data = perennial_data[[grouping_column, 'Crop_OpenAg', 'final_price', 'final_yield', 'Adjusted_Acres', 'Crop_Type']]
perennial_data.columns = [grouping_column, 'Crop_OpenAg', 'final_price', 'final_yield', 'Total_Acres', 'Crop_Type']

# Combine perennial and non-perennial data
final_aggregated_data = pd.concat([perennial_data, non_perennial_data])
final_aggregated_data = final_aggregated_data[[grouping_column, 'Crop_OpenAg', 'final_price', 'final_yield', 'Total_Acres']]
final_aggregated_data.columns = [grouping_column, 'Crop', 'Price ($/unit)', 'Yield (unit/acre)', 'Area (acre)']
final_aggregated_data.to_csv('../../Datasets/econ_crop_data/final_final_crop_economic_data.csv')
