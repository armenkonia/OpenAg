# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 23:07:54 2024

@author: armen
"""

import pickle 
import pandas as pd
import matplotlib.pyplot as plt
import os
import fiona
import geopandas as gpd
import numpy as np

#get price and yield from each county
with open(r"C:\Users\armen\Desktop\COEQWAL\Datasets\Outputs\hr_crop_analysis_results.pkl", 'rb') as f:
    hr_crop_analysis_results_dict = pickle.load(f)

agg_crops_dic = {}
proxy_crops_hr_dic = {}
for hr_name, result_dict_list in hr_crop_analysis_results_dict.items():
        agg_crops_dic[hr_name]=result_dict_list['agg_crops']
        proxy_crops_hr_dic[hr_name]=result_dict_list['lowest_diff_df']

all_proxy_crops_hr_dfs = []
for hr_name, proxy_crops_hr_df in proxy_crops_hr_dic.items():
    proxy_crops_hr_df['HR_NAME'] = hr_name
    all_proxy_crops_hr_dfs.append(proxy_crops_hr_df)
merged_proxy_crops_hr_df = pd.concat(all_proxy_crops_hr_dfs, ignore_index=True)
merged_proxy_crops_hr_df['Crop_OpenAg'] = merged_proxy_crops_hr_df['Crop_OpenAg'].str.replace('^WA_', '', regex=True)

usda_crops = pd.read_csv(r"C:/Users/armen/Desktop/COEQWAL/Datasets/Outputs/updated_usda_crops_18_22_filtered.csv")
usda_crops = usda_crops.drop('Crop_OpenAg', axis=1)
openag_crops = usda_crops.merge(merged_proxy_crops_hr_df, how='outer', on=['Crop Name', 'HR_NAME'])


#%%
# #figure out what crops do we have in each county in landiq
# gdb_path = r"C:\Users\armen\Documents\ArcGIS\Projects\COEQWAL\COEQWAL.gdb"
# landiq20_CVID_GW_DU_SR = gpd.read_file(gdb_path, layer='landiq20_CVID_GW_DU_SR')

# crop_id = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\Datasets\bridge_landiq_openag_crops_all_years_01102024.xlsx",sheet_name='2020')
# openag_mapping_dict = crop_id.set_index('CROPTYP2')['Crop_OpenAg'].to_dict()
# landiq20_CVID_GW_DU_SR['openag crop type'] = landiq20_CVID_GW_DU_SR.CROPTYP2.map(openag_mapping_dict)

# landiq_crop_county_combinations = landiq20_CVID_GW_DU_SR.groupby(['openag crop type', 'COUNTY', 'HYDRO_RGN'])['ACRES'].sum().reset_index()
# landiq_crop_county_combinations = landiq_crop_county_combinations[~landiq_crop_county_combinations['openag crop type'].isin(['na', "Idle", "Young Perennial","Pasture"])].dropna(subset=['openag crop type'])
# landiq_crop_county_combinations['COUNTY'] = landiq_crop_county_combinations['COUNTY'].str.title()
# landiq_crop_county_combinations.to_csv(r"C:\Users\armen\Desktop\COEQWAL\Datasets\Outputs\landiq_county_crop_areas.csv")
landiq_crop_county_areas = pd.read_csv(r"C:\Users\armen\Desktop\COEQWAL\Datasets\Outputs\landiq_county_crop_areas.csv")

#%%

#figure out what econ crop is missing in landiq county
merged_df = landiq_crop_county_areas.merge(openag_crops, left_on=['openag crop type','COUNTY'], right_on=['Crop_OpenAg','County'], how='left')
merged_df = merged_df.sort_values(by=['COUNTY', 'ACRES'], ascending=[True, False])
merged_df['data availability'] = np.where(merged_df['Crop Name'].isna(), 'not available', 'available')
merged_df_grouped = merged_df.groupby('data availability')['ACRES'].sum()
total_acres = merged_df_grouped.sum()
percent_area_series = (merged_df_grouped / total_acres) * 100
percent_area_series = percent_area_series.round(2)

merged_df_available = merged_df.loc[merged_df['data availability'] == 'available']
