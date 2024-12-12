# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 09:12:31 2024

@author: armen
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import fiona
import numpy as np
gdb_path = r"C:\Users\armen\Documents\ArcGIS\Projects\COEQWAL\COEQWAL.gdb"
layers = fiona.listlayers(gdb_path)
landiq20_CVID_GW_DU_SR = gpd.read_file(gdb_path, layer='landiq20_CVID_GW_DU_SR')
landiq20_CVID_GW_DU_SR = landiq20_CVID_GW_DU_SR[~landiq20_CVID_GW_DU_SR['CROPTYP2'].isin(['X', 'U','I2','P1','P3','P4','P5','P6','P7','T16','T27','YP'])] #remove all parcels that are not crops

ag_regions_csv = pd.read_csv(r"C:\Users\armen\Desktop\OpenAg\Datasets\PPIC_database_221211_CV.csv")
ag_regions_csv_crops = ag_regions_csv.crop.unique()
#%%
landiq_crop_description = pd.read_csv(r"C:\Users\armen\Desktop\OpenAg\Datasets\landiq_crop_description.csv")
crop_id = pd.read_excel(r"C:\Users\armen\Desktop\OpenAg\Datasets\bridge_landiq_openag_crops_all_years_01102024.xlsx",sheet_name='2020_updated')

#get openag and landiq crop name for each croptyp2 in parcel
landiq_mapping_dict = landiq_crop_description.set_index('CROPTYP2')['Description'].to_dict()
ppic_mapping_dict = crop_id.set_index('CROPTYP2')['Crop_OpenAg'].to_dict()
landiq20_CVID_GW_DU_SR['landiq crop type'] = landiq20_CVID_GW_DU_SR.CROPTYP2.map(landiq_mapping_dict)
landiq20_CVID_GW_DU_SR['openag crop type'] = landiq20_CVID_GW_DU_SR.CROPTYP2.map(ppic_mapping_dict)

#merge openag crop info to landiq crops based on subregion 
landiq20_CVID_GW_DU_SR = landiq20_CVID_GW_DU_SR.merge(ag_regions_csv[['region', 'crop','price','yld','xwaterunit']], left_on=['Subregion', 'openag crop type'], right_on=['region', 'crop'], how='left')
landiq20_CVID_GW_DU_SR_head = landiq20_CVID_GW_DU_SR.head()
# landiq20_CVID_GW_DU_SR.to_file(gdb_path, layer='landiq20_CVID_GW_DU_SR', driver="GPKG")

#check if crop classifications are correct
landiq_crops = landiq20_CVID_GW_DU_SR.crop.unique()
landiq_crops = landiq20_CVID_GW_DU_SR['landiq crop type'].unique()
openag_bridge_crops = landiq20_CVID_GW_DU_SR['openag crop type'].unique()
ag_regions_csv_crops = ag_regions_csv.crop.unique()
all_in_crop_id = np.isin(openag_bridge_crops, ag_regions_csv_crops)
not_openag_values = openag_bridge_crops[~all_in_crop_id] #returns those that are not found in openag but are found in bridge

#status of each parcel (whether it has openag data)
landiq20_CVID_GW_DU_SR['crop data status'] = 'Available'
landiq20_CVID_GW_DU_SR.loc[landiq20_CVID_GW_DU_SR['region'].isna(), 'crop data status'] = 'Crop price not available in this region'
landiq20_CVID_GW_DU_SR.loc[landiq20_CVID_GW_DU_SR['openag crop type'].isna(), 'crop data status'] = 'Crop not classified'


landiq20_SR = landiq20_CVID_GW_DU_SR[landiq20_CVID_GW_DU_SR['Subregion'].notna()] #remove all rows that dont have subregion
landiq20_madera = landiq20_CVID_GW_DU_SR.loc[landiq20_CVID_GW_DU_SR.COUNTY == 'Madera']

landiq20_SR_noprice = landiq20_SR.loc[landiq20_CVID_GW_DU_SR['crop data status'] == 'Crop price not available in this region']

subregion_agg = landiq20_CVID_GW_DU_SR.groupby(['Subregion','crop','HYDRO_RGN','price','yld','xwaterunit'], as_index=False).agg({
                   'ACRES': 'sum'})

#%%
fig, ax = plt.subplots(figsize=(10, 8))
# landiq20_madera.plot(column='crop data status', ax=ax, legend=True, cmap='viridis')
landiq20_SR.plot(column='crop data status', ax=ax, legend=True, cmap='viridis')

#%%
du_waterunit_sum = landiq20_CVID_GW_DU_SR.groupby('DU_ID', as_index=False).agg({
    'xwaterunit': 'sum',
    'ACRES': 'sum'})

landiq20_CVID_GW_DU_SR['total_wateruse'] = landiq20_CVID_GW_DU_SR['xwaterunit']*landiq20_CVID_GW_DU_SR['ACRES']

du_waterunit_sum = landiq20_CVID_GW_DU_SR.groupby('DU_ID', as_index=False).agg({
    'total_wateruse': 'sum',
    'ACRES': 'sum'})
du_waterunit_sum['total_wateruse_TAF'] = du_waterunit_sum['total_wateruse'] * 0.001
du_waterunit_sum.to_csv('DU_wateruse.csv')
