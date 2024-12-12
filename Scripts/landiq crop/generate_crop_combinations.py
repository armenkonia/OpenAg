# -*- coding: utf-8 -*-
"""
Created on Sat Nov 30 11:58:42 2024

@author: armen
"""
import geopandas as gpd
import pandas as pd
import itertools

counties_hr = pd.read_csv('../../Datasets/econ_crop_data/counties_hr_neighbors.csv')

crop_id = pd.read_excel("../../Datasets/econ_crop_data/bridge openag.xlsx",sheet_name='updated usda & openag')
crop_id = crop_id[~crop_id['Crop_OpenAg'].isin(['Idle', 'na', 'Young Perennial','Pasture'])]
openag_crops = crop_id.Crop_OpenAg
openag_crops = pd.concat([openag_crops, pd.Series(["Grapes Wine", "Grapes Table", "Grapes Raisin",
                                                    "Tomatoes Unspecified", "Tomatoes Processing", "Tomatoes Fresh Market"])], ignore_index=True)
openag_crops = openag_crops[~openag_crops.isin(["Grapes", "Tomatoes"])].reset_index(drop=True)

counties_ca = counties_hr.NAME.unique()
combinations = list(itertools.product(counties_ca, openag_crops))
combinations_df = pd.DataFrame(combinations, columns=['County', 'Crop_OpenAg'])

combinations_df = combinations_df.merge(counties_hr[['NAME', 'HR_NAME', 'Neighboring Counties', 'Neighboring HR']], how='left', left_on='County',right_on='NAME')

combinations_df.to_csv('../../Datasets/econ_crop_data/ca_county_openag_crop_combinations.csv')
