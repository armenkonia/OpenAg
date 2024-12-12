# -*- coding: utf-8 -*-
"""
Created on Sat Nov 23 21:55:29 2024

@author: armen
"""

import pandas as pd
import geopandas as gpd
import fiona
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap

crop_econ_data = pd.read_csv(r"C:\Users\armen\Desktop\COEQWAL\Datasets\Outputs\crop_economic_data.csv")

gdb_path = r"C:\Users\armen\Documents\ArcGIS\Projects\COEQWAL\COEQWAL.gdb"
layers = fiona.listlayers(gdb_path)
landiq20 = gpd.read_file(gdb_path, layer='landiq20_CVID_GW_DU_SR')

crop_id = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\Datasets\bridge_landiq_openag_crops_all_years_01102024.xlsx",sheet_name='2020', usecols=[0, 1, 2])
openag_mapping_dict = crop_id.set_index('CROPTYP2')['Crop_OpenAg'].to_dict()
landiq20['Crop_OpenAg'] = landiq20.CROPTYP2.map(openag_mapping_dict)

landiq20 = landiq20.merge(crop_econ_data[['County', 'Crop_OpenAg','final_price','final_yield']], left_on=['COUNTY', 'Crop_OpenAg'], right_on=['County', 'Crop_OpenAg'], how='left')

landiq20['Crop_OpenAg'] = landiq20.CROPTYP2.map(openag_mapping_dict)

landiq20_selected = landiq20.loc[landiq20.Crop_OpenAg != 'na']
landiq20_selected = landiq20_selected.loc[landiq20_selected.Crop_OpenAg != 'idle']

landiq20_selected = landiq20_selected.loc[landiq20_selected.HYDRO_RGN == 'San Joaquin River']
landiq20_selected = landiq20_selected.loc[landiq20_selected.final_price < 7500]

#%%
landiq20_selected = landiq20_selected.loc[landiq20_selected.Crop_OpenAg == 'Almonds']


fig, ax = plt.subplots(1, 1, figsize=(12, 10))

landiq20_selected.plot(column='final_price', 
                       cmap='viridis', 
                       legend=True, 
                       ax=ax)
plt.tight_layout()
plt.show()