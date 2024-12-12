# -*- coding: utf-8 -*-
"""
Created on Sat Oct 26 18:51:54 2024

@author: armen
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import fiona
import numpy as np

gdb_path = r"C:\Users\armen\Documents\ArcGIS\Projects\Landiq18\Landiq18.gdb"
landiq_SR = gpd.read_file(gdb_path, layer='LandIQ_18_SR')

ag_regions_csv = pd.read_csv(r"C:\Users\armen\Desktop\COEQWAL\Datasets\PPIC_database_221211_CV.csv")
ag_regions_csv_crops = ag_regions_csv.crop.unique()

landiq_crop_description = pd.read_csv(r"C:\Users\armen\Desktop\COEQWAL\Datasets\landiq_crop_description.csv")
crop_id = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\Datasets\bridge_landiq_openag_crops_all_years_01102024.xlsx",sheet_name='2018_updated')

#get openag and landiq crop name for each parcel
landiq_mapping_dict = landiq_crop_description.set_index('CROPTYP2')['Description'].to_dict()
ppic_mapping_dict = crop_id.set_index('CROPTYP2')['Crop_OpenAg'].to_dict()
landiq_SR['landiq crop type'] = landiq_SR.CROPTYP2.map(landiq_mapping_dict)
landiq_SR['openag crop type'] = landiq_SR.CROPTYP2.map(ppic_mapping_dict)

#merge openag crop info to landiq crops based on subregion 
landiq_SR = landiq_SR.merge(ag_regions_csv[['region', 'crop','price','yld','xwaterunit']], left_on=['Subregion', 'openag crop type'], right_on=['region', 'crop'], how='left')

landiq_SR = landiq_SR[landiq_SR['Subregion'].notna()] #remove all rows that dont have subregion

landiq_SR = landiq_SR[~landiq_SR['CROPTYP2'].isin(['X', 'U','I2','P1','P3','P4','P5','P6','P7','T16','T27'])]
#%%
subregion_agg = landiq_SR.groupby(['Subregion','openag crop type','price','yld','xwaterunit'], as_index=False, dropna=False).agg({
                    'ACRES': 'sum'})
subregion_agg['Crop_Type'] = np.where(subregion_agg['openag crop type'].isin(['Almonds', 'Grapes','Orchards','Pistachios','Subtropical','Walnuts']), 'Perennial', 'Non-Perennial')
subregion_agg_perennial = subregion_agg[subregion_agg['Crop_Type'] == 'Perennial']
#%%
subregion_total_area = subregion_agg_perennial.groupby('Subregion')['ACRES'].sum()
subregion_agg_perennial = pd.merge(subregion_agg_perennial, subregion_total_area, how='left', on='Subregion')
subregion_agg_perennial = subregion_agg_perennial.rename(columns={'ACRES_x': 'ACRES','ACRES_y': 'Total_Acres'})
subregion_agg_perennial['percent_area'] = subregion_agg_perennial['ACRES'] / subregion_agg_perennial['Total_Acres']
subregion_agg_perennial['weighted_price'] = subregion_agg_perennial['price'] * subregion_agg_perennial['percent_area']
subregion_agg_perennial['weighted_yld'] = subregion_agg_perennial['yld'] * subregion_agg_perennial['percent_area']
subregion_agg_perennial['weighted_xwaterunit'] = subregion_agg_perennial['xwaterunit'] * subregion_agg_perennial['percent_area']

subregion_agg_yp = subregion_agg_perennial.groupby('Subregion')[['weighted_price','weighted_yld','weighted_xwaterunit']].sum().reset_index()

subregion_agg_yp['openag crop type'] = 'Young Perennial'
subregion_agg_yp = subregion_agg_yp.rename(columns={'weighted_price': 'price','weighted_yld': 'yld','weighted_xwaterunit': 'xwaterunit'})


subregion_agg_final = pd.merge(subregion_agg,subregion_agg_yp,how='left',on=['Subregion', 'openag crop type'],suffixes=('', '_new'))
for col in ['price', 'yld', 'xwaterunit']:
    subregion_agg_final[col] = subregion_agg_final[col].combine_first(subregion_agg_final[f'{col}_new'])
subregion_agg_final.drop(columns=[f'{col}_new' for col in ['price', 'yld', 'xwaterunit']], inplace=True)
