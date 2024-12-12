# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 21:18:22 2024

@author: armen
"""
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

usda_crops = pd.read_csv(r"C:/Users/armen/Desktop/COEQWAL/Datasets/usda_crops_18_22.csv")
price_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Price P/U').add_prefix('price_').reset_index()
yield_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Yield').add_prefix('yield_').reset_index()
merged_df = pd.merge(price_df, yield_df, on=['County', 'Crop Name'], how='outer')

usda_crop_id = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\crossover\id.xlsx",sheet_name='bridge bw USDA and landiq', header=1, nrows=51, usecols="G:T")
usda_crop_id['USDA'] = usda_crop_id['USDA'].replace("-", 'No Classification Available')
usda_crop_id['USDA'] = usda_crop_id['USDA'].replace("na", 'Not applicable')
usda_crop_id['USDA'] = usda_crop_id['USDA'].replace(np.nan, 'Unknown Classification')

crops_mapping_dict = usda_crop_id.set_index('CROPTYP2')['USDA'].to_dict()

crops_needed = pd.unique(usda_crop_id.iloc[:,2:].values.ravel('K'))
merged_df = merged_df[merged_df['Crop Name'].isin(crops_needed)]
#%%
merged_df['Crop Name'] = merged_df['Crop Name'].replace({
    'Plums Dried': 'Plums Dried (Prunes)',
    'Rice Seed': 'Seed Rice',
    'Sunflower Seed Planting': 'Seed Sunflower Planting',
    'Pears Asian': 'Pears Unspecified',
    'Pears Bartlett': 'Pears Unspecified',
    'Field Crops Seed Misc.': 'Seed Field Crops Misc'
})

# Group by 'Crop Name' and 'County', then aggregate using max() to combine the rows
combined_df = merged_df.groupby(['Crop Name', 'County'], as_index=False).first()

usda_crops_left = merged_df['Crop Name'].unique()
#%%
# Create a boolean mask to check if any value in the DataFrame is in usda_crops_left
mask = usda_crop_id.isin(usda_crops_left)
mask.iloc[:, :2] = True

filtered_usda_crop_id = usda_crop_id.where(mask)
