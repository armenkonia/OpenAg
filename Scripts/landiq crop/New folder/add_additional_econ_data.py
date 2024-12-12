# -*- coding: utf-8 -*-
"""
Created on Sat Nov 23 12:08:22 2024

@author: armen
"""

import pandas as pd
import geopandas as gpd
import fiona
import numpy as np
crop_econ_data = pd.read_csv('../../Datasets/econ_crop_data/final_crop_economic_data.csv',index_col=0)

gdb_path = r"C:\Users\armen\Documents\ArcGIS\Projects\COEQWAL\COEQWAL.gdb"
layers = fiona.listlayers(gdb_path)
landiq20 = gpd.read_file(gdb_path, layer='landiq20_CVID_GW_DU_SR')
# landiq20 = landiq20[~landiq20_CVID_GW_DU_SR['CROPTYP2'].isin(['X', 'U','I2','P1','P3','P4','P5','P6','P7','T16','T27','YP'])] #remove all parcels that are not crops
# landiq20 = landiq20[~landiq20_CVID_GW_DU_SR['CROPTYP2'].isin(['X', 'U',])] #remove all parcels that are not crops

crop_id = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\Datasets\bridge_landiq_openag_crops_all_years_01102024.xlsx",sheet_name='2020', usecols=[0, 1, 2])

#get openag and landiq crop name for each parcel
openag_mapping_dict = crop_id.set_index('CROPTYP2')['Crop_OpenAg'].to_dict()
landiq20['Crop_OpenAg'] = landiq20.CROPTYP2.map(openag_mapping_dict)

crops_bridge = crop_id.Crop_OpenAg.unique()
crops_econ = crop_econ_data.Crop_OpenAg.unique()
# bridge_not_in_econ = set(crops_bridge) - set(crops_econ)
# econ_not_in_bridge = set(crops_econ) - set(crops_bridge)

counties_landiq = landiq20.COUNTY.unique()
counties_econ = crop_econ_data.County.unique()
bridge_not_in_econ = set(counties_landiq) - set(counties_econ)
econ_not_in_bridge = set(counties_econ) - set(counties_landiq)

#%%
#merge openag crop info to landiq crops based on subregion 
landiq20 = landiq20.merge(crop_econ_data[['County', 'Crop_OpenAg','final_price','final_yield']], left_on=['COUNTY', 'Crop_OpenAg'], right_on=['County', 'Crop_OpenAg'], how='left')

landiq20_filtered = landiq20.loc[landiq20.COUNTY != '****']
landiq20_filtered = landiq20_filtered.loc[landiq20.Crop_OpenAg != 'na']
landiq20_filtered = landiq20_filtered.loc[landiq20.Crop_OpenAg != 'idle']

nan_final_price_rows = landiq20_filtered[landiq20_filtered['final_price'].isna()]
crops_landiq = nan_final_price_rows.CROPTYP2.unique()

nan_crop_OpenAg_rows = landiq20_filtered[landiq20_filtered['Crop_OpenAg'].isna()]

# landiq_SR = landiq_SR[~landiq_SR['CROPTYP2'].isin(['X', 'U','I2','P1','P3','P4','P5','P6','P7','T16','T27'])]
#%%
# Group by COUNTY instead of Subregion
county_agg = landiq20.groupby(['COUNTY', 'Crop_OpenAg', 'final_price', 'final_yield'], as_index=False, dropna=False).agg({
    'ACRES': 'sum'})

# Categorize crops as Perennial or Non-Perennial
county_agg['Crop_Type'] = np.where(
    county_agg['Crop_OpenAg'].isin(['Almonds', 'Grapes', 'Orchards', 'Pistachios', 'Subtropical', 'Walnuts']),
    'Perennial',
    'Non-Perennial')

county_agg_perennial = county_agg[county_agg['Crop_Type'] == 'Perennial']
county_total_area = county_agg_perennial.groupby('COUNTY')['ACRES'].sum()
county_agg_perennial = pd.merge(county_agg_perennial, county_total_area, how='left', on='COUNTY')
county_agg_perennial = county_agg_perennial.rename(columns={'ACRES_x': 'ACRES', 'ACRES_y': 'Total_Acres'})
county_agg_perennial['percent_area'] = county_agg_perennial['ACRES'] / county_agg_perennial['Total_Acres']
county_agg_perennial['weighted_price'] = county_agg_perennial['final_price'] * county_agg_perennial['percent_area']
county_agg_perennial['weighted_yld'] = county_agg_perennial['final_yield'] * county_agg_perennial['percent_area']
county_agg_yp = county_agg_perennial.groupby('COUNTY')[['weighted_price', 'weighted_yld']].sum().reset_index()
county_agg_yp['Crop_OpenAg'] = 'Young Perennial'

# Rename weighted columns for final merge
county_agg_yp = county_agg_yp.rename(columns={
    'weighted_price': 'final_price',
    'weighted_yld': 'final_yield'})

# Merge aggregated values back to the original DataFrame
county_agg_final = pd.merge(county_agg, county_agg_yp, how='left', on=['COUNTY', 'Crop_OpenAg'], suffixes=('', '_new'))

# Replace NaN values in the original columns with values from the new columns
for col in ['final_price', 'final_yield']:
    county_agg_final[col] = county_agg_final[col].combine_first(county_agg_final[f'{col}_new'])

# Drop the temporary columns
county_agg_final.drop(columns=[f'{col}_new' for col in ['final_price', 'final_yield']], inplace=True)

#%%
# Define the new row attributes
pasture_price = 215
pasture_yield = 3.5
pasture_crop_type = "Non-Perennial"
pasture_crop_openag = "Pasture"

# Get the unique counties from the DataFrame
unique_counties = county_agg_final['COUNTY'].unique()

# Create a DataFrame for the new rows
pasture_rows = pd.DataFrame({
    'COUNTY': unique_counties,
    'Crop_OpenAg': pasture_crop_openag,
    'final_price': pasture_price,
    'final_yield': pasture_yield,
    'ACRES': 0,  # Set as 0 initially, adjust as needed
    'Crop_Type': pasture_crop_type
})

# Append the new rows to the existing DataFrame
county_agg_final = pd.concat([county_agg_final, pasture_rows], ignore_index=True)


county_agg_final.loc[county_agg_final['Crop_OpenAg'] == 'Pasture', ['final_price', 'final_yield']] = [215, 3.5]
county_agg_final = county_agg_final.dropna()
county_agg_final = county_agg_final.drop('Crop_Type',axis=1)
county_agg_final.to_csv('../../Datasets/econ_crop_data/final_crop_economic_data.csv')
