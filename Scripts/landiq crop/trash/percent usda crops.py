# -*- coding: utf-8 -*-
"""
Created on Thu Oct 31 10:33:50 2024

@author: armen
"""
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

usda_crops = pd.read_csv(r"C:/Users/armen/Desktop/COEQWAL/Datasets/Outputs/usda_crops_18_22.csv")
usda_crops = usda_crops[['Year', 'Crop Name','County', 'Price P/U', 'Yield','Harvested Acres','Unit']]

price_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Price P/U').add_prefix('price_').reset_index()
yield_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Yield').add_prefix('yield_').reset_index()
usda_crops['Harvested Acres'] = pd.to_numeric(usda_crops['Harvested Acres'], errors='coerce')
acres_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Harvested Acres').add_prefix('acres_').reset_index()
usda_crops['Harvested Acres'] = pd.to_numeric(usda_crops['Harvested Acres'], errors='coerce')
acres_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Harvested Acres').add_prefix('Acres_').reset_index()

usda_crops = pd.merge(price_df, yield_df, on=['County', 'Crop Name'], how='outer')
usda_crops = pd.merge(usda_crops, acres_df, on=['County', 'Crop Name'], how='outer')

usda_landiq_bridge = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\bridging between datasets (work in progress).xlsx",sheet_name='bridge bw USDA and landiq', header=1, nrows=51, usecols="G:T")
usda_landiq_bridge['USDA'] = usda_landiq_bridge['USDA'].replace("-", 'No Classification Available')
usda_landiq_bridge['USDA'] = usda_landiq_bridge['USDA'].replace("na", 'Not applicable')
usda_landiq_bridge['USDA'] = usda_landiq_bridge['USDA'].replace(np.nan, 'Unknown Classification')

landiq_to_usda_dict = usda_landiq_bridge.set_index('CROPTYP2')['USDA'].to_dict()

usda_crops_used = pd.unique(usda_landiq_bridge.iloc[:,2:].values.ravel('K'))
usda_crops = usda_crops[usda_crops['Crop Name'].isin(usda_crops_used)]
#%%
usda_crops['Crop Name'] = usda_crops['Crop Name'].replace({
    'Plums Dried': 'Plums Dried (Prunes)',
    'Rice Seed': 'Seed Rice',
    'Sunflower Seed Planting': 'Seed Sunflower Planting',
    'Pears Asian': 'Pears Unspecified',
    'Pears Bartlett': 'Pears Unspecified',
    'Field Crops Seed Misc.': 'Seed Field Crops Misc'
})

# Group by 'Crop Name' and 'County', then aggregate using max() to combine the rows
usda_crops = usda_crops.groupby(['Crop Name', 'County'], as_index=False).first()
