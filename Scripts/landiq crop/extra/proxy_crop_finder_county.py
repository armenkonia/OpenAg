# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 21:51:35 2024

@author: armen
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import pickle
from proxy_crop_finder_functions_only import calculate_agg_crops,find_proxy_crops,plot_crop_data

usda_crops = pd.read_csv(r"C:/Users/armen/Desktop/COEQWAL/Datasets/Outputs/updated_usda_crops_18_22.csv")
usda_openag_bridge = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\bridging between datasets (work in progress).xlsx",sheet_name='final upd bridge USDA & OpenAG', header=0, nrows=25, usecols="A:X")

# melt usda_openag_bridge dataset
value_vars = [col for col in usda_openag_bridge.columns if col != 'Crop_OpenAg'] # Identify all usda columns
usda_openag_bridge_melted = pd.melt(usda_openag_bridge, id_vars=['Crop_OpenAg'], value_vars=value_vars, value_name='USDA_Crop')
usda_openag_bridge_melted = usda_openag_bridge_melted.dropna(subset=['USDA_Crop']).reset_index(drop=True)
usda_openag_bridge_melted = usda_openag_bridge_melted.drop(columns=['variable'])

# work with 2020 
usda_crops_20 = usda_crops[['Crop Name', 'County', 'HR_NAME', 'price_2020','Production_2020','Acres_2020', 'yield_2020']]
usda_crops_20.columns = ['Crop Name', 'County', 'HR_NAME', 'Price ($/unit)','Production (unit)', 'Area (acreage)', 'Yield (unit/acreage)']
usda_crops_20 = usda_crops_20.dropna(subset=['Area (acreage)','Price ($/unit)']) # drop nan rows because we cant do weighted average if either of this two are missing

usda_counties = usda_crops_20['County'].unique() # the number of counties drops from 58 to 48. this is because many counties dont have crops. or
#%%
# usda_crops_20_sac = usda_crops_20.loc[usda_crops_20.HR_NAME == 'Sacramento River']
usda_crops_20_butte = usda_crops_20.loc[usda_crops_20.County == 'butte']
## calculate acreage-weighted marginal revenue for each crop category
agg_crops = calculate_agg_crops(usda_crops_20_butte, usda_openag_bridge_melted)
crop_list,lowest_diff_df = find_proxy_crops(agg_crops)

#%%
county_crop_analysis_results_dict  = {}

for county_name in usda_crops_20['County'].unique():
    # Filter the data for the specific HR_NAME
    usda_crops_selected = usda_crops_20.loc[usda_crops_20.County == county_name]
    # Calculate the aggregated crops data for the HR
    agg_crops = calculate_agg_crops(usda_crops_selected, usda_openag_bridge_melted)
    # Find the proxy crops for the HR
    crop_list,lowest_diff_df = find_proxy_crops(agg_crops)
    # Plot the crop data and save the plots    
    # Store the results for the current HR_NAME
    county_crop_analysis_results_dict [county_name] = {
        'agg_crops': agg_crops,
        'lowest_diff_df': lowest_diff_df
    }
# with open(r"C:\Users\armen\Desktop\COEQWAL\Datasets\Outputs\county_crop_analysis_results.pkl", 'wb') as f:
#     pickle.dump(county_crop_analysis_results_dict, f) 
#%%%
# unique_crops = agg_crops['Crop_OpenAg'].unique()
# for crop in unique_crops:
#     crop_data = agg_crops[agg_crops['Crop_OpenAg'] == crop]

#     # Assign colors based on crop name presence in crop_list
#     colors = ['orange' if name in crop_list else 'lightblue' for name in crop_data['Crop Name']] 
    
#     # Create subplots
#     fig, axs = plt.subplots(1, 2, figsize=(15, 5))  # 2 subplots
#     axs[0].bar(crop_data['Crop Name'], crop_data['Price Yield ($/acre)'], color=colors)
#     axs[0].set_title(f'{crop} {region_name} Price Yield ($/acre) in 2020')
#     axs[0].set_ylabel('Price Yield ($/acre)')
#     axs[0].tick_params(axis='x', rotation=90)
#     axs[0].grid(axis='y', linestyle='--', alpha=0.7)
    
#     # Exclude last row for the second plot
#     crop_data = crop_data.iloc[:-1, :]
#     axs[1].bar(crop_data['Crop Name'], crop_data['Percent Area (%)'], color=colors)
#     axs[1].set_title(f'{crop} {region_name} Percent Area in 2020')
#     axs[1].set_ylabel('Percent Area (%)')
#     axs[1].tick_params(axis='x', rotation=90)
#     axs[1].grid(axis='y', linestyle='--', alpha=0.7)
#     axs[1].set_ylim(0, 100)