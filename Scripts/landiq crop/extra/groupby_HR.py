# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 22:09:20 2024

@author: armen
"""

import pandas as pd
import geopandas as gpd
crop_data = pd.read_csv('../../Datasets/econ_crop_data/final_crop_economic_data.csv',index_col=0)


# Group by HR_NAME and Crop_OpenAg and calculate weighted averages
result = crop_data.groupby(['HR_NAME', 'Crop_OpenAg']).apply(
    lambda group: pd.Series({
        'Weighted_Price': (group['final_price'] * group['ACRES']).sum() / group['ACRES'].sum(),
        'Weighted_Yield': (group['final_yield'] * group['ACRES']).sum() / group['ACRES'].sum(),
        'Total_Acres': group['ACRES'].sum()  # Optional: Include total acres if needed
    })
).reset_index()

# Rename columns for clarity (optional)
result = result.rename(columns={
    'Weighted_Price': 'final_price',
    'Weighted_Yield': 'final_yield'
})

#%%
gdb_path = r"C:\Users\armen\Documents\ArcGIS\Projects\COEQWAL\COEQWAL.gdb"
landiq20 = gpd.read_file(gdb_path, layer='landiq20_CVID_GW_DU_SR')

crop_id = pd.read_excel(r"C:\Users\armen\Desktop\OpenAg\Datasets\econ_crop_data\bridge openag.xlsx",sheet_name='landiq20 & openag')
openag_mapping_dict = crop_id.set_index('CROPTYP2')['Crop_OpenAg'].to_dict()
landiq20['Crop_OpenAg'] = landiq20.CROPTYP2.map(openag_mapping_dict)
landiq20 = landiq20.merge(crop_data[['COUNTY', 'Crop_OpenAg','final_price','final_yield']], left_on=['COUNTY', 'Crop_OpenAg'], right_on=['COUNTY', 'Crop_OpenAg'], how='left')

landiq20_head = landiq20.head()

# Group by HYDRO_RGN and Crop_OpenAg and calculate weighted averages
result = landiq20.groupby(['HYDRO_RGN', 'Crop_OpenAg']).apply(
    lambda group: pd.Series({
        'Weighted_Price': (group['final_price'] * group['ACRES']).sum() / group['ACRES'].sum(),
        'Weighted_Yield': (group['final_yield'] * group['ACRES']).sum() / group['ACRES'].sum(),
        'Total_Acres': group['ACRES'].sum()
    })
).reset_index()

result = result[(result['Crop_OpenAg'] != 'na') & (result['Crop_OpenAg'] != 'Idle')]
