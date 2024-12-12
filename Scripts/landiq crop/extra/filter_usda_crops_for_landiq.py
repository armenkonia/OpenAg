# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 21:18:22 2024

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
acres_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Harvested Acres').add_prefix('Acres_').reset_index()

usda_crops = pd.merge(price_df, yield_df, on=['County', 'Crop Name'], how='outer')

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
    'Field Crops Seed Misc.': 'Seed Field Crops Misc' #there's one more
})

# Group by 'Crop Name' and 'County', then aggregate using max() to combine the rows
usda_crops = usda_crops.groupby(['Crop Name', 'County'], as_index=False).first()

usda_crops_used_updated = usda_crops['Crop Name'].unique()
usda_crops_used_updated = np.append(usda_crops_used_updated, np.array(['No Classification Available', 'Not applicable', 'Unknown Classification']))

#%%
# Create a boolean mask to check if any value in the DataFrame is in usda_crops_left
mask = usda_landiq_bridge.isin(usda_crops_used_updated)
mask.iloc[:, :2] = True
usda_landiq_bridge_updated = usda_landiq_bridge.where(mask)

#%%
def squeeze_nan(x):
    original_columns = x.index.tolist()

    squeezed = x.dropna()
    squeezed.index = [original_columns[n] for n in range(squeezed.count())]

    return squeezed.reindex(original_columns, fill_value=np.nan)
usda_landiq_bridge_updated = usda_landiq_bridge_updated.apply(squeeze_nan, axis=1)
usda_landiq_bridge_updated = usda_landiq_bridge_updated.dropna(axis=1, how='all')

#%%
# Use ExcelWriter to append a new sheet
with pd.ExcelWriter(r"C:\Users\armen\Desktop\COEQWAL\bridging between datasets (work in progress).xlsx", engine='openpyxl', mode='a') as writer:
    usda_landiq_bridge_updated.to_excel(writer, sheet_name='new bridge bw USDA and landiq', index=False)

#%%
#this is to check which landiq crops
main_usda_crops = usda_crops.loc[usda_crops['Crop Name'].isin(usda_landiq_bridge_updated.iloc[:,2])]
usda_crops.to_csv('usda_crops_filtered.csv')
