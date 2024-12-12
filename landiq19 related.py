# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 12:02:44 2024

@author: armen
"""
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import fiona
import numpy as np
landiq = gpd.read_file(r"C:\Users\armen\Documents\ArcGIS\Projects\Landiq18\Landiq18.gdb", layer='LandIQ_18_SR_DU')
landiqcolumns = landiq.columns
crop_id = pd.read_excel(r"C:\Users\armen\Desktop\OpenAg\Datasets\bridge_landiq_openag_crops_all_years_01102024.xlsx",sheet_name='2018_updated')
ppic_mapping_dict = crop_id.set_index('CROPTYP2')['Crop_OpenAg'].to_dict()
landiq['Crop_OpenAg'] = landiq.CROPTYP2.map(ppic_mapping_dict)

du_agg = landiq.groupby(['DU_ID', 'Crop_OpenAg'], as_index=False).agg({
    'ACRES': 'sum',
    })

landiq = landiq[['ACRES','DU_ID','Subregion','COUNTY','Crop_OpenAg']]
landiq = landiq.dropna(subset= 'DU_ID').reset_index()
#%%
ag_regions_csv = pd.read_csv(r"C:\Users\armen\Desktop\OpenAg\Datasets\PPIC_database_221211_CV.csv")
landiq_w_econ = landiq.merge(ag_regions_csv[['region', 'crop','price','yld','xwaterunit']], left_on=['Subregion', 'Crop_OpenAg'], right_on=['region', 'crop'], how='left')

landiq_w_econ[['ACRES', 'xwaterunit', 'price','yld']] = landiq_w_econ[['ACRES', 'xwaterunit', 'price','yld']].apply(pd.to_numeric, errors='coerce')

du_crop_agg = landiq_w_econ.groupby(['DU_ID', 'Crop_OpenAg'], as_index=False).agg({
    'ACRES': 'sum',
    'xwaterunit': lambda x: (x * landiq.loc[x.index, 'ACRES']).sum() / landiq.loc[x.index, 'ACRES'].sum(),
    'price': lambda x: (x * landiq.loc[x.index, 'ACRES']).sum() / landiq.loc[x.index, 'ACRES'].sum(),
    'yld': lambda x: (x * landiq.loc[x.index, 'ACRES']).sum() / landiq.loc[x.index, 'ACRES'].sum()
})