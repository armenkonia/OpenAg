# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 16:37:39 2024

@author: armen
"""

import pickle
import pandas as pd


# Load HR crop analysis results
with open('../../Datasets/econ_crop_data/hr_crop_analysis_results.pkl', 'rb') as file:
    hr_crop_analysis_results = pickle.load(file)

usda_data = pd.read_csv('../../Datasets/econ_crop_data/processed_usda_crops_18_22.csv', index_col=0)
## get 5-yr average (2018 to 2022) of price yield acres and production
usda_crops_av = pd.melt(usda_data, id_vars=['County', 'Crop Name', 'HR_NAME', 'Neighboring Counties','Neighboring HR', 'Unit_2018'],
                    value_vars=
                    ['price_2018', 'price_2019', 'price_2020','price_2021', 'price_2022', 
                     'yield_2018', 'yield_2019', 'yield_2020','yield_2021', 'yield_2022', 
                     'Acres_2018', 'Acres_2019', 'Acres_2020','Acres_2021', 'Acres_2022', 
                     'Production_2018', 'Production_2019','Production_2020', 'Production_2021', 'Production_2022'],
                    var_name='year_type', value_name='value')
# Extract year and type (price or yield) from the 'year_type' column
usda_crops_av['year'] = usda_crops_av['year_type'].str.extract(r'(\d{4})')  # Extract year (e.g., 2018, 2019)
usda_crops_av['type'] = usda_crops_av['year_type'].str.extract(r'(price|yield|Acres|Production)')  # Extract price or yield
#transform back to original format
usda_crops_av = usda_crops_av.pivot_table(index=["County", "Crop Name", "HR_NAME", "Neighboring Counties", "Neighboring HR"], columns="type", values="value", aggfunc="mean").reset_index()

usda_crops_av = usda_crops_av[['Crop Name', 'County', 'HR_NAME', "Neighboring Counties", "Neighboring HR", 'price', 'Production', 'Acres','yield']]
usda_crops_av.columns = ['Crop Name', 'County', 'HR_NAME', "Neighboring Counties", "Neighboring HR", 'price_2020', 'Production_2020', 'Acres_2020', 'yield_2020']
usda_crops_av = usda_crops_av.dropna(subset=['Acres_2020','price_2020']) # drop nan rows because we cant do weighted average if either of this two are missing
usda_data = usda_crops_av
#%%
crop_combinations = pd.read_csv('../../Datasets/econ_crop_data/ca_county_openag_crop_combinations.csv', index_col=0)

# Extract proxy crops for each HR and create a unified DataFrame
proxy_crop_info_by_hr = {}
proxy_crops_list = []
for hr_name, result in hr_crop_analysis_results.items():
    proxy_crop_info_by_hr[hr_name] = result['agg_crops']
    proxy_crops_df = result['proxy crop']
    proxy_crops_df['HR_NAME'] = hr_name
    proxy_crops_list.append(proxy_crops_df)
proxy_crops_df = pd.concat(proxy_crops_list, ignore_index=True)
proxy_crops_df['Crop_OpenAg'] = proxy_crops_df['Crop_OpenAg'].str.replace('^WA_', '', regex=True)

# Extract economic data for proxy crops
usda_data = usda_data[['Crop Name', 'County', 'HR_NAME', 'Neighboring Counties', 
                       'Neighboring HR', 'price_2020', 'Production_2020', 'Acres_2020', 'yield_2020']]
usda_data['County'] = usda_data['County'].str.title()
usda_data = usda_data.merge(proxy_crops_df, how='outer', on=['Crop Name', 'HR_NAME'])
usda_data = usda_data.merge(crop_combinations, on=['Crop_OpenAg', 'County'], how='right')
usda_data.rename(columns={
    'Crop Name': 'usda_crop',
    'HR_NAME_y': 'HR_NAME',
    'Neighboring Counties_y': 'Neighboring Counties',
    'Neighboring HR_y': 'Neighboring HR'
}, inplace=True)
usda_data = usda_data[['Crop_OpenAg', 'usda_crop', 'County', 'HR_NAME', 'Neighboring Counties', 'Neighboring HR', 'price_2020', 'Production_2020', 'Acres_2020', 'yield_2020']]


#%%
new_usda_data = usda_crops_av
new_usda_data = new_usda_data[['Crop Name', 'County', 'HR_NAME', 'Neighboring Counties', 
                       'Neighboring HR', 'price_2020', 'Production_2020', 'Acres_2020', 'yield_2020']]
new_usda_data['County'] = new_usda_data['County'].str.title()
new_usda_data = new_usda_data.rename(columns={"Crop Name": "Crop_OpenAg"})

grapes_combinations = crop_combinations[crop_combinations.Crop_OpenAg.str.contains("grapes", case=False, na=False)]
tomatoes_combinations = crop_combinations[crop_combinations.Crop_OpenAg.str.contains("tomato", case=False, na=False)]

usda_grapes = new_usda_data.merge(grapes_combinations, on=['Crop_OpenAg', 'County'], how='right')
usda_grapes.rename(columns={
    'HR_NAME_y': 'HR_NAME',
    'Neighboring Counties_y': 'Neighboring Counties',
    'Neighboring HR_y': 'Neighboring HR'
}, inplace=True)
usda_grapes['usda_crop'] = usda_grapes['Crop_OpenAg']
# usda_grapes['Crop_OpenAg'] = 'Grapes'
usda_grapes = usda_grapes[['Crop_OpenAg', 'usda_crop', 'County', 'HR_NAME', 'Neighboring Counties', 'Neighboring HR', 'price_2020', 'Production_2020', 'Acres_2020', 'yield_2020']]

usda_tomatoes = new_usda_data.merge(tomatoes_combinations, on=['Crop_OpenAg', 'County'], how='right')
usda_tomatoes.rename(columns={
    'HR_NAME_y': 'HR_NAME',
    'Neighboring Counties_y': 'Neighboring Counties',
    'Neighboring HR_y': 'Neighboring HR'
}, inplace=True)
usda_tomatoes['usda_crop'] = usda_tomatoes['Crop_OpenAg']
# usda_tomatoes['Crop_OpenAg'] = 'Tomatoes'
usda_tomatoes = usda_tomatoes[['Crop_OpenAg', 'usda_crop', 'County', 'HR_NAME', 'Neighboring Counties', 'Neighboring HR', 'price_2020', 'Production_2020', 'Acres_2020', 'yield_2020']]
usda_exc_crops = pd.concat([usda_tomatoes,usda_grapes])

#%%
usda_data = usda_data[~usda_data.Crop_OpenAg.str.contains("Grapes|Tomatoes", case=False, na=False)].reset_index(drop=True)
usda_data = pd.concat([usda_data,usda_exc_crops])
usda_data['Crop_Subtype'] = usda_data['Crop_OpenAg']
usda_data['Crop_OpenAg'] = usda_data['Crop_OpenAg'].str.replace(r'^Grapes.*', 'Grapes', regex=True, case=False)
usda_data['Crop_OpenAg'] = usda_data['Crop_OpenAg'].str.replace(r'^Tomatoes.*', 'Tomatoes', regex=True, case=False)

total_area = usda_data.groupby(['Crop_OpenAg','County'])['Acres_2020'].sum().reset_index()
usda_data = usda_data.merge(total_area, on=['Crop_OpenAg','County'], suffixes=('', '_total'), how='left')
usda_data['fraction'] = usda_data['Acres_2020']/usda_data['Acres_2020_total']

usda_data = usda_data[['Crop_OpenAg', 'Crop_Subtype', 'usda_crop', 'County', 'HR_NAME', 'Neighboring Counties','Neighboring HR', 'price_2020', 'Production_2020', 'Acres_2020','yield_2020','fraction']]
usda_data.to_csv('../../Datasets/econ_crop_data/processed_usda_crops_20.csv')
#%%

usda_data_grapes = usda_data.loc[usda_data.Crop_OpenAg == 'Grapes']
pivot_table = usda_data_grapes.pivot_table(index='County', columns='Crop_Subtype', values='fraction', aggfunc='first')
pivot_table = pivot_table.fillna(0)
unpivoted_df = pd.melt(pivot_table.reset_index(), id_vars='County', value_name='fraction')
usda_data_grapes = usda_data_grapes.merge(unpivoted_df[['County', 'Crop_Subtype', 'fraction']], 
                                          on=['County', 'Crop_Subtype'], how='left', suffixes=('', '_updated'))
usda_data_grapes['fraction'] = usda_data_grapes['fraction_updated']
usda_data_grapes = usda_data_grapes.drop(columns=['fraction_updated'])

usda_data_tomatoes = usda_data.loc[usda_data.Crop_OpenAg == 'Tomatoes']
pivot_table_tomatoes = usda_data_tomatoes.pivot_table(index='County', columns='Crop_Subtype', values='fraction', aggfunc='first')
pivot_table_tomatoes = pivot_table_tomatoes.fillna(0)
unpivoted_df_tomatoes = pd.melt(pivot_table_tomatoes.reset_index(), id_vars='County', value_name='fraction')
usda_data_tomatoes = usda_data_tomatoes.merge(unpivoted_df_tomatoes[['County', 'Crop_Subtype', 'fraction']], 
                                              on=['County', 'Crop_Subtype'], how='left', suffixes=('', '_updated'))
usda_data_tomatoes['fraction'] = usda_data_tomatoes['fraction_updated']
usda_data_tomatoes = usda_data_tomatoes.drop(columns=['fraction_updated'])

usda_data_non_grapes_tomatoes = usda_data.loc[~usda_data.Crop_OpenAg.isin(['Grapes', 'Tomatoes'])]
usda_data = pd.concat([usda_data_non_grapes_tomatoes, usda_data_grapes, usda_data_tomatoes])

usda_data.to_csv('../../Datasets/econ_crop_data/processed_usda_crops_20.csv')
