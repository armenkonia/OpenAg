# -*- coding: utf-8 -*-
"""
Created on Sun Dec  1 20:35:18 2024

@author: armen
"""

import pandas as pd
import geopandas as gpd

meta_crop_data=pd.read_csv('../../Datasets/econ_crop_data/final_crop_economic_data.csv')
landiq20 = gpd.read_file(r"C:\Users\armen\Documents\ArcGIS\Projects\COEQWAL\COEQWAL.gdb", layer='landiq20_CVID_GW_DU_SR')


crop_id = pd.read_excel("../../Datasets/econ_crop_data/bridge openag.xlsx",sheet_name='landiq20 & openag')
openag_mapping_dict = crop_id.set_index('CROPTYP2')['Crop_OpenAg'].to_dict()
landiq20['Crop_OpenAg'] = landiq20.CROPTYP2.map(openag_mapping_dict)
#%%
landiq20_w_econ = landiq20.merge(meta_crop_data, left_on=['COUNTY','Crop_OpenAg'],right_on=['County','Crop_OpenAg'],how='left')

landiq20_w_econ_filtered = landiq20_w_econ[['COUNTY','Crop_OpenAg','ACRES', 'GSA_Name', 'DU_ID',
    'final_price_2020', 'final_yield_2020', 'final_Fraction_1', 'final_Fraction_2', 
                                   'final_price_1', 'final_yield_1', 'final_price_2', 'final_yield_2']]
landiq20_head = landiq20_w_econ.head()
#%%
landiq20_w_econ_grouped = landiq20_w_econ_filtered.groupby(['DU_ID', 'Crop_OpenAg']).apply(
    lambda group: pd.Series({
        'Weighted_Price': (group['final_price_2020'] * group['ACRES']).sum() / group['ACRES'].sum(),
        'Weighted_Yield': (group['final_yield_2020'] * group['ACRES']).sum() / group['ACRES'].sum(),
        'Total_Acres': group['ACRES'].sum(),  # Optional: Include total acres if needed
        'Weighted_Fraction_1': (group['final_Fraction_1'] * group['ACRES']).sum() / group['ACRES'].sum(),
        'Weighted_final_price_1': (group['final_price_1'] * group['ACRES']).sum() / group['ACRES'].sum(),
        'Weighted_final_price_2': (group['final_price_2'] * group['ACRES']).sum() / group['ACRES'].sum(),
        'Weighted_final_yield_1': (group['final_yield_1'] * group['ACRES']).sum() / group['ACRES'].sum(),
        'Weighted_final_yield_2': (group['final_yield_2'] * group['ACRES']).sum() / group['ACRES'].sum(),
    })
).reset_index()
#%%
landiq20_w_econ_grouped_grapes = landiq20_w_econ_grouped.loc[landiq20_w_econ_grouped.Crop_OpenAg == 'Grapes']

# Define a function to split the rows based on crop type
def split_crop_rows(row):
    crop_map = {
        'Grapes': ('Grapes Wine', 'Grapes Table'),
        'Tomatoes': ('Tomatoes Fresh', 'Tomatoes Processing')
    }

    # Get the crop-specific subcategories
    subcategories = crop_map.get(row['Crop_OpenAg'], None)
    if not subcategories:
        # If no matching crop in the map, return the original row
        return [{'DU_ID': row['DU_ID'], 'Crop_OpenAg': row['Crop_OpenAg'], 'Acres': row['Total_Acres'],
                 'final_price': row['Weighted_Price'], 'Yield': row['Weighted_Yield']}]

    # Calculate subcategory-specific values
    sub1_acres = row['Total_Acres'] * row['Weighted_Fraction_1']
    sub2_acres = row['Total_Acres'] - sub1_acres

    sub1_yield = row['Weighted_Yield'] * row['Weighted_Fraction_1']
    sub2_yield = row['Weighted_Yield'] * (1 - row['Weighted_Fraction_1'])

    # Create new rows for the subcategories
    sub1_row = {
        'DU_ID': row['DU_ID'],
        'Crop_OpenAg': subcategories[0],
        'Total_Acres': sub1_acres,
        'Weighted_Price': row['Weighted_final_price_1'],
        'Weighted_Yield': row['Weighted_final_yield_1']
    }
    sub2_row = {
        'DU_ID': row['DU_ID'],
        'Crop_OpenAg': subcategories[1],
        'Total_Acres': sub2_acres,
        'Weighted_Price': row['Weighted_final_price_2'],
        'Weighted_Yield': row['Weighted_final_yield_2']
    }

    return [sub1_row, sub2_row]

# Filter rows for crops that need splitting
crops_to_split = ['Grapes', 'Tomatoes']
rows_to_split = landiq20_w_econ_grouped.loc[landiq20_w_econ_grouped['Crop_OpenAg'].isin(crops_to_split)]

# Apply the split function to each row
split_rows = rows_to_split.apply(split_crop_rows, axis=1)

# Flatten the resulting list of lists and create a new DataFrame
split_data = pd.DataFrame([row for rows in split_rows for row in rows])

# Filter rows for crops that do not need splitting
non_split_data = landiq20_w_econ_grouped.loc[~landiq20_w_econ_grouped['Crop_OpenAg'].isin(crops_to_split)]

# Combine the split and non-split data
final_data = pd.concat([non_split_data, split_data], ignore_index=True)

final_data = final_data[['DU_ID', 'Crop_OpenAg', 'Weighted_Price', 'Weighted_Yield','Total_Acres']]

