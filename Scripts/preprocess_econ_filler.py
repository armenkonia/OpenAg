# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 16:37:39 2024

@author: armen
"""

import pickle
import pandas as pd
import itertools

# crop_combinations = pd.read_csv('../../Datasets/Output/ca_county_openag_crop_combinations.csv', index_col=0)
proxy_crops_df = pd.read_csv('../Datasets/Output/proxy_crops_hr.csv')
counties_hr = pd.read_csv('../Datasets/Output/counties_hr_neighbors.csv')
crop_id = pd.read_excel("../Datasets/bridge openag.xlsx",sheet_name='updated usda & openag')
usda_crops_av = pd.read_csv('../Datasets/Output/processed_usda_crops_18_22.csv', index_col=0)

# =============================================================================
# Get all possible combination of crops in each county. thus, 21x58
# =============================================================================
crop_id = crop_id[~crop_id['Crop_OpenAg'].isin(['Idle', 'na', 'Young Perennial','Pasture'])]
openag_crops = crop_id.Crop_OpenAg
openag_crops = pd.concat([openag_crops, pd.Series(["Grapes Wine", "Grapes Table", "Grapes Raisin",
                                                    "Tomatoes Unspecified", "Tomatoes Processing", "Tomatoes Fresh Market"])], ignore_index=True)
openag_crops = openag_crops[~openag_crops.isin(["Grapes", "Tomatoes"])].reset_index(drop=True)
counties_ca = counties_hr.NAME.unique()
combinations = list(itertools.product(counties_ca, openag_crops))
crop_combinations = pd.DataFrame(combinations, columns=['County', 'Crop_OpenAg'])
crop_combinations = crop_combinations.merge(counties_hr[['NAME', 'HR_NAME', 'Neighboring Counties', 'Neighboring HR']], how='left', left_on='County',right_on='NAME')

# =============================================================================
# Extract economic data from usda for openag crops
# =============================================================================
econ_data = usda_crops_av.copy()
# Extract economic data for proxy crops
econ_data = econ_data[['Crop Name', 'County', 'HR_NAME', 'Neighboring Counties', 
                       'Neighboring HR', 'price_avg', 'production_avg', 'acres_avg', 'yield_avg']]
econ_data['County'] = econ_data['County'].str.title()
econ_data = econ_data.merge(proxy_crops_df, how='outer', on=['Crop Name', 'HR_NAME'])
econ_data = econ_data[['Crop Name', 'County', 'price_avg', 'production_avg', 'acres_avg', 'yield_avg', 'Crop_OpenAg']].rename(columns={'Crop Name': 'usda_crop'})
econ_data = econ_data.merge(crop_combinations, on=['Crop_OpenAg', 'County'], how='right')
econ_data = econ_data[['Crop_OpenAg', 'usda_crop', 'County', 'HR_NAME', 'Neighboring Counties', 'Neighboring HR', 'price_avg', 'production_avg', 'acres_avg', 'yield_avg']]


# =============================================================================
# Extract economic data for exceptional crops
# =============================================================================
excp_econ_data = usda_crops_av.copy()
excp_econ_data = excp_econ_data[['Crop Name', 'County', 'HR_NAME', 'Neighboring Counties', 
                       'Neighboring HR', 'price_avg', 'production_avg', 'acres_avg', 'yield_avg']]
excp_econ_data['County'] = excp_econ_data['County'].str.title()
excp_econ_data = excp_econ_data.rename(columns={"Crop Name": "Crop_OpenAg"})

grapes_combinations = crop_combinations[crop_combinations.Crop_OpenAg.str.contains("grapes", case=False, na=False)]
tomatoes_combinations = crop_combinations[crop_combinations.Crop_OpenAg.str.contains("tomato", case=False, na=False)]

usda_grapes = excp_econ_data[['Crop_OpenAg', 'County', 'price_avg', 'production_avg', 'acres_avg','yield_avg']].merge(grapes_combinations, on=['Crop_OpenAg', 'County'], how='right')
usda_grapes['usda_crop'] = usda_grapes['Crop_OpenAg']
usda_tomatoes = excp_econ_data[['Crop_OpenAg', 'County', 'price_avg', 'production_avg', 'acres_avg','yield_avg']].merge(tomatoes_combinations, on=['Crop_OpenAg', 'County'], how='right')
usda_tomatoes['usda_crop'] = usda_tomatoes['Crop_OpenAg']

usda_exc_crops = pd.concat([usda_tomatoes,usda_grapes])
usda_exc_crops = usda_exc_crops[['Crop_OpenAg', 'usda_crop', 'County', 'HR_NAME', 'Neighboring Counties', 'Neighboring HR', 'price_avg', 'production_avg', 'acres_avg', 'yield_avg']]

# =============================================================================
# Replace exceptional crops econ data in original dataset
# =============================================================================
econ_data = econ_data[~econ_data.Crop_OpenAg.str.contains("Grapes|Tomatoes", case=False, na=False)].reset_index(drop=True)
econ_data = pd.concat([econ_data,usda_exc_crops])
econ_data['Crop_Subtype'] = econ_data['Crop_OpenAg']
econ_data['Crop_OpenAg'] = econ_data['Crop_OpenAg'].str.replace(r'^Grapes.*', 'Grapes', regex=True, case=False)
econ_data['Crop_OpenAg'] = econ_data['Crop_OpenAg'].str.replace(r'^Tomatoes.*', 'Tomatoes', regex=True, case=False)
total_area = econ_data.groupby(['Crop_OpenAg','County'])['acres_avg'].sum().reset_index()
econ_data = econ_data.merge(total_area, on=['Crop_OpenAg','County'], suffixes=('', '_total'), how='left')
econ_data['fraction'] = econ_data['acres_avg']/econ_data['acres_avg_total']
econ_data = econ_data[['Crop_OpenAg', 'Crop_Subtype', 'usda_crop', 'County', 'HR_NAME', 'Neighboring Counties','Neighboring HR', 
                       'price_avg', 'production_avg', 'acres_avg', 'yield_avg', 'fraction']]

# =============================================================================
# Update fraction for exceptional crops, as different types of grapes and tomatoes are grown in each county
# =============================================================================
econ_grapes = econ_data.loc[econ_data.Crop_OpenAg == 'Grapes']
pivot_table = econ_grapes.pivot_table(index='County', columns='Crop_Subtype', values='fraction', aggfunc='first')
pivot_table = pivot_table.fillna(0)
unpivoted_df = pd.melt(pivot_table.reset_index(), id_vars='County', value_name='fraction')
econ_grapes = econ_grapes.merge(unpivoted_df[['County', 'Crop_Subtype', 'fraction']], on=['County', 'Crop_Subtype'], how='left', suffixes=('', '_updated'))
econ_grapes['fraction'] = econ_grapes['fraction_updated']
econ_grapes = econ_grapes.drop(columns=['fraction_updated'])

econ_tomatoes = econ_data.loc[econ_data.Crop_OpenAg == 'Tomatoes']
pivot_table_tomatoes = econ_tomatoes.pivot_table(index='County', columns='Crop_Subtype', values='fraction', aggfunc='first')
pivot_table_tomatoes = pivot_table_tomatoes.fillna(0)
unpivoted_df_tomatoes = pd.melt(pivot_table_tomatoes.reset_index(), id_vars='County', value_name='fraction')
econ_tomatoes = econ_tomatoes.merge(unpivoted_df_tomatoes[['County', 'Crop_Subtype', 'fraction']], on=['County', 'Crop_Subtype'], how='left', suffixes=('', '_updated'))
econ_tomatoes['fraction'] = econ_tomatoes['fraction_updated']
econ_tomatoes = econ_tomatoes.drop(columns=['fraction_updated'])

econ_data_non_grapes_tomatoes = econ_data.loc[~econ_data.Crop_OpenAg.isin(['Grapes', 'Tomatoes'])]
econ_data = pd.concat([econ_data_non_grapes_tomatoes, econ_grapes, econ_tomatoes])

econ_data.to_csv('../Datasets/Output/processed_usda_crops_20.csv')
