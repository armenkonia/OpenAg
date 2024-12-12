# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 18:01:43 2024

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
        proxy_crops_hr_dic[hr_name]=result_dict_list['proxy crop']

all_proxy_crops_hr_dfs = []
for hr_name, proxy_crops_hr_df in proxy_crops_hr_dic.items():
    proxy_crops_hr_df['HR_NAME'] = hr_name
    all_proxy_crops_hr_dfs.append(proxy_crops_hr_df)
merged_proxy_crops_hr_df = pd.concat(all_proxy_crops_hr_dfs, ignore_index=True)
merged_proxy_crops_hr_df['Crop_OpenAg'] = merged_proxy_crops_hr_df['Crop_OpenAg'].str.replace('^WA_', '', regex=True)

usda_crops = pd.read_csv(r"C:/Users/armen/Desktop/COEQWAL/Datasets/Outputs/updated_usda_crops_18_22.csv")
usda_crops_20 = usda_crops[['Crop Name', 'County', 'HR_NAME', 'Neighboring Counties', 'price_2020','Production_2020','Acres_2020', 'yield_2020']]
usda_crops_20['County'] = usda_crops_20['County'].str.title()
usda_crops_20['economic_data_availability'] = np.where(usda_crops_20['price_2020'].isna(), 'N', 'Y')


openag_crops = usda_crops_20.merge(merged_proxy_crops_hr_df, how='outer', on=['Crop Name', 'HR_NAME'])
openag_crops = openag_crops.dropna(subset=['Crop_OpenAg'])

nan_price_rows = openag_crops[openag_crops['price_2020'].isna()]

import ast

openag_crops['Neighboring Counties'] = openag_crops['Neighboring Counties'].apply(ast.literal_eval)
openag_crops = openag_crops[['Crop Name', 'Crop_OpenAg', 'County', 'HR_NAME', 'Neighboring Counties', 'price_2020',
                               'Production_2020', 'Acres_2020', 'yield_2020',
                               'economic_data_availability']]
#%%

openag_crops_exploded = openag_crops.explode('Neighboring Counties')
openag_crops_merged = pd.merge(openag_crops_exploded, openag_crops[['Crop_OpenAg', 'County', 'price_2020']], 
                                left_on=['Neighboring Counties','Crop_OpenAg'], right_on=['County','Crop_OpenAg'], 
                                suffixes=('', '_neighbor'),how='left')

# grouped_openag_crops_merged = list(openag_crops_merged.groupby(by=['Crop Name', 'County']))

avg_neighboring_prices = openag_crops_merged.groupby(['Crop_OpenAg', 'County'])['price_2020_neighbor'].mean()
avg_neighboring_prices_dict = avg_neighboring_prices.to_dict()

avg_hr_prices = openag_crops.groupby(['Crop_OpenAg', 'HR_NAME'])['price_2020'].mean()
avg_hr_prices_dict = avg_hr_prices.to_dict()


openag_crops['neighbor_avg_price'] = openag_crops.apply(
    lambda row: avg_neighboring_prices_dict.get((row['Crop_OpenAg'], row['County'])), axis=1)

openag_crops['hr_avg_price'] = openag_crops.apply(
    lambda row: avg_hr_prices_dict.get((row['Crop_OpenAg'], row['HR_NAME'])), axis=1)

openag_crops['price_2020'] = openag_crops['price_2020'].fillna(openag_crops['neighbor_avg_price'])
openag_crops['price_2020'] = openag_crops['price_2020'].fillna(openag_crops['hr_avg_price'])


#%%

def fill_missing_values_with_neighbor_and_hr_avg(df, column_name):
    """
    Fill missing values in the specified column (`price_2020` or `yield_2020`) 
    with the average value from neighboring counties, and if that is not available, 
    with the average HR-level value.
    
    Parameters:
    - df: DataFrame with crop data.
    - column_name: The column in the DataFrame to fill missing values for (e.g., 'price_2020' or 'yield_2020').
    
    Returns:
    - DataFrame with missing values in the specified column filled.
    """
    # Explode the 'Neighboring Counties' list into separate rows
    df_exploded = df.explode('Neighboring Counties')
    
    # Merge to get neighboring county values for the specified column
    df_merged = pd.merge(
        df_exploded,
        df[['Crop_OpenAg', 'County', column_name]],
        left_on=['Neighboring Counties', 'Crop_OpenAg'],
        right_on=['County', 'Crop_OpenAg'],
        suffixes=('', '_neighbor'),
        how='left'
    )
    
    # Calculate average neighboring values per crop and county
    avg_neighboring_values = df_merged.groupby(['Crop_OpenAg', 'County'])[f"{column_name}_neighbor"].mean()
    avg_neighboring_values_dict = avg_neighboring_values.to_dict()
    
    # Calculate average HR-level values per Crop Name and HR_NAME
    avg_hr_values = df.groupby(['Crop_OpenAg', 'HR_NAME'])[column_name].mean()
    avg_hr_values_dict = avg_hr_values.to_dict()
    
    # Add the average neighboring values and HR-level values to the original DataFrame
    df[f'neighbor_avg_{column_name}'] = df.apply(
        lambda row: avg_neighboring_values_dict.get((row['Crop_OpenAg'], row['County'])), axis=1)
    
    df[f'hr_avg_{column_name}'] = df.apply(
        lambda row: avg_hr_values_dict.get((row['Crop_OpenAg'], row['HR_NAME'])), axis=1)
    
    # Fill missing values in the specified column with neighbor and HR-level averages
    df[column_name] = df[column_name].fillna(df[f'neighbor_avg_{column_name}'])
    df[column_name] = df[column_name].fillna(df[f'hr_avg_{column_name}'])
    
    return df

# Usage example:
updated_openag_crops = fill_missing_values_with_neighbor_and_hr_avg(openag_crops, 'price_2020')
updated_openag_crops = fill_missing_values_with_neighbor_and_hr_avg(updated_openag_crops, 'yield_2020')
updated_openag_crops = updated_openag_crops.drop(['Production_2020', 'Acres_2020'], axis=1)
# updated_openag_crops.to_csv(r"C:\Users\armen\Desktop\COEQWAL\Datasets\Outputs\updated_usda_crops_18_22_filtered.csv")
#%%

landiq_crop_county_combinations = pd.read_csv(r"C:\Users\armen\Desktop\COEQWAL\Datasets\Outputs\landiq_county_crop_areas.csv")
counties_hr = pd.read_csv('C:/Users/armen/Desktop/COEQWAL/Datasets/counties_HR.csv')
landiq_crop_county_combinations = landiq_crop_county_combinations.merge(counties_hr[['NAME','Neighboring Counties']], how='left', left_on='COUNTY',right_on='NAME')
landiq_crop_county_combinations= landiq_crop_county_combinations.drop('NAME', axis=1)
updated_openag_crops = updated_openag_crops[['Crop Name', 'Crop_OpenAg', 'County','price_2020', 'yield_2020']]
final_df = landiq_crop_county_combinations.merge(updated_openag_crops, left_on=['openag crop type', 'COUNTY'], right_on=['Crop_OpenAg', 'County'], how='left' )
final_df= final_df.drop('Crop_OpenAg', axis=1)
final_df = final_df.rename(columns={'HYDRO_RGN': 'HR_NAME', 'openag crop type': 'Crop_OpenAg'})

#%%
updated_final_df = fill_missing_values_with_neighbor_and_hr_avg(final_df, 'price_2020')

#%%
counties_hr = pd.read_csv('C:/Users/armen/Desktop/COEQWAL/Datasets/counties_HR.csv')

counties = updated_openag_crops['County'].unique()
crops = updated_openag_crops['Crop Name'].unique()
all_combinations = pd.MultiIndex.from_product([counties, crops], names=['County', 'Crop Name']).to_frame(index=False)
all_combinations = pd.merge(all_combinations, counties_hr[['County', 'Neighboring Counties', 'HR_NAME']], on=['County'], how='left')
all_combinations = all_combinations.merge(openag_crops[['Crop Name', 'County','Crop_OpenAg','price_2020','yield_2020']],how='left')
updated_all_combinations = fill_missing_values_with_neighbor_and_hr_avg(all_combinations, 'price_2020')
