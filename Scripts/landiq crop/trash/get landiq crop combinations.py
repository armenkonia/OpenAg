# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 16:07:53 2024

@author: armen
"""
import geopandas as gpd
import pandas as pd
counties_hr = pd.read_csv('../../Datasets/econ_crop_data/counties_hr_neighbors.csv')
gdb_path = r"C:\Users\armen\Documents\ArcGIS\Projects\COEQWAL\COEQWAL.gdb"
landiq20 = gpd.read_file(gdb_path, layer='landiq20_CVID_GW_DU_SR')

crop_id = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\Datasets\econ_crop_data\bridge openag.xlsx",sheet_name='landiq20 & openag')
openag_mapping_dict = crop_id.set_index('CROPTYP2')['Crop_OpenAg'].to_dict()
landiq20['Crop_OpenAg'] = landiq20.CROPTYP2.map(openag_mapping_dict)

landiq_openag_crops = landiq20.groupby(['Crop_OpenAg', 'COUNTY'])['ACRES'].sum().reset_index()
landiq_openag_crops = landiq_openag_crops[~landiq_openag_crops['Crop_OpenAg'].isin(['na', "Idle", "Young Perennial","Pasture"])].dropna(subset=['Crop_OpenAg'])
landiq_openag_crops['COUNTY'] = landiq_openag_crops['COUNTY'].str.title()
landiq_openag_crops = landiq_openag_crops.rename(columns={'COUNTY': 'County'})
landiq_openag_crops = landiq_openag_crops.merge(counties_hr[['NAME', 'HR_NAME', 'Neighboring Counties', 'Neighboring HR']], how='left', left_on='County',right_on='NAME')
landiq_openag_crops= landiq_openag_crops.drop('NAME', axis=1)

landiq_openag_crops.to_csv('../../Datasets/econ_crop_data/landiq_openag_crops_county_area.csv')

# No duplicate rows found based on 'Crop_OpenAg' and 'COUNTY'
duplicates = landiq_openag_crops[landiq_openag_crops.duplicated(subset=['Crop_OpenAg', 'County'], keep=False)]
