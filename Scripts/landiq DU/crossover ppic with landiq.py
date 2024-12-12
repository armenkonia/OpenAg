# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 09:12:31 2024

@author: armen
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import fiona

gdb_path = r"C:\Users\armen\Documents\ArcGIS\Projects\COEQWAL\COEQWAL.gdb"
layers = fiona.listlayers(gdb_path)
print(layers)

landiq20_CVID_GW_DU_SR = gpd.read_file(gdb_path, layer='landiq20_CVID_GW_DU_SR')
# #remove all parcels that are not crops
# landiq20_CVID_GW_DU = landiq20_CVID_GW_DU[~landiq20_CVID_GW_DU['CROPTYP2'].isin(['X', 'U'])]
# #remove all crops that dont have irrigation district
# landiq20_CVID_GW_DU = landiq20_CVID_GW_DU.dropna(subset=['Agency_Nam'])

ag_regions_csv = pd.read_csv(r"C:\Users\armen\Desktop\COEQWAL\Datasets\PPIC_database_221211_CV.csv")
ag_regions_csv_crops = ag_regions_csv.crop.unique()

landiq_crop_description = pd.read_csv('landiq_crop_description.csv')
landiq_mapping_dict = landiq_crop_description.set_index('CROPTYP2')['Description'].to_dict()

crop_id = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\crossover\bridge_landiq_openag_crops_all_years_01102024.xlsx",sheet_name='2020_updated')
ppic_mapping_dict = crop_id.set_index('CROPTYP2')['Crop_OpenAg'].to_dict()


landiq20_CVID_GW_DU_SR['landiq crop type'] = landiq20_CVID_GW_DU_SR.CROPTYP2.map(landiq_mapping_dict)
landiq20_CVID_GW_DU_SR['ppic crop type'] = landiq20_CVID_GW_DU_SR.CROPTYP2.map(ppic_mapping_dict)

landiq20_CVID_GW_DU_SR = landiq20_CVID_GW_DU_SR.merge(ag_regions_csv[['region', 'crop','price','xwaterunit']], left_on=['Subregion', 'ppic crop type'], right_on=['region', 'crop'], how='left')
# landiq20_CVID_GW_DU_SR.to_file(gdb_path, layer='landiq20_CVID_GW_DU_SR', driver="GPKG")
landiq20_CVID_GW_DU_SR_head = landiq20_CVID_GW_DU_SR.head()
#%%
landiq20_SR = landiq20_CVID_GW_DU_SR[landiq20_CVID_GW_DU_SR['Subregion'].notna()]
landiq20_SR.columns
landiq20_SR_crops = landiq20_CVID_GW_DU_SR.crop.unique()
landiq20_SR_crops = landiq20_CVID_GW_DU_SR['landiq crop type'].unique()
landiq20_SR_crops = landiq20_CVID_GW_DU_SR['ppic crop type'].unique()


landiq20_SR['crop data status'] = 'Available'
landiq20_SR.loc[landiq20_SR['region'].isna(), 'crop data status'] = 'crop price not available in this region'
landiq20_SR.loc[landiq20_SR['ppic crop type'].isna(), 'crop data status'] = 'crop not classified'


# filtered_landiq = landiq20_CVID_GW_DU_SR.loc[landiq20_CVID_GW_DU_SR['landiq crop type'] == 'Eucalyptus']
# landiq20_SR.to_file(gdb_path, layer='landiq20_SR', driver="GPKG")
