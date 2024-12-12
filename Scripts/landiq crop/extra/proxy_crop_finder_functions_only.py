# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 21:59:06 2024

@author: armen
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import pickle 


## calculate acreage-weighted marginal revenue for each crop category

def calculate_agg_crops(usda_crops_20_sac, usda_openag_bridge_melted):
    # Aggregate variables for each commodity crop by hydrologic region
    agg_crops = usda_crops_20_sac.groupby('Crop Name').sum(numeric_only=True).reset_index()
    agg_crops = agg_crops.merge(usda_openag_bridge_melted, left_on='Crop Name', right_on='USDA_Crop', how='left')

    # Drop the 'USDA_Crop' column
    agg_crops = agg_crops.drop('USDA_Crop', axis=1)

    # Calculate revenue per year by multiplying each crop price per unit by its yield, then by area
    agg_crops['Price Yield ($/acre)'] = agg_crops['Price ($/unit)'] * agg_crops['Yield (unit/acreage)']
    agg_crops['Price ($)'] = agg_crops['Price Yield ($/acre)'] * agg_crops['Area (acreage)']
    agg_crops['Percent Area (%)'] = (agg_crops['Area (acreage)'] / agg_crops.groupby('Crop_OpenAg')['Area (acreage)'].transform('sum')).round(2) * 100

    # Calculate the sum of crop prices multiplied by its acres
    weighted_avg_revenue = agg_crops.groupby('Crop_OpenAg')[['Price ($)', 'Area (acreage)']].sum()
    weighted_avg_revenue['Price Yield ($/acre)'] = weighted_avg_revenue['Price ($)'] / weighted_avg_revenue['Area (acreage)']
    weighted_avg_revenue = weighted_avg_revenue.reset_index()
    weighted_avg_revenue['Crop Name'] = 'WA_' + weighted_avg_revenue['Crop_OpenAg']

    # Merge weighted average of marginal revenue with proxy crops df
    agg_crops = pd.concat([agg_crops, weighted_avg_revenue], axis=0)
    agg_crops.fillna(0, inplace=True)
    agg_crops['Crop_OpenAg'] = agg_crops['Crop_OpenAg'].astype(str)

    # Return the relevant columns
    agg_crops = agg_crops[['Crop Name', 'Crop_OpenAg', 'Price ($/unit)', 'Production (unit)', 'Area (acreage)',
                           'Yield (unit/acreage)', 'Price Yield ($/acre)', 'Price ($)', 'Percent Area (%)']]
    
    return agg_crops

# For each crop category, calculate the absolute percent difference of price between the weighted average crop and the commodity crops. 
# The proxy crop is identified as the one with the smallest difference, which will be stored in a DataFrame

def find_proxy_crops(agg_crops):
    rows = []
    for crop in agg_crops['Crop_OpenAg'].unique():
        crop_df = agg_crops[agg_crops['Crop_OpenAg'] == crop]
        wa_crop_value = crop_df[crop_df['Crop Name'] == f'WA_{crop}']['Price Yield ($/acre)']
        
        # Check if the weighted average crop value exists
        if not wa_crop_value.empty:
            wa_crop_value = wa_crop_value.values[0]
            crop_df = crop_df[crop_df['Crop Name'] != f'WA_{crop}']  # Exclude the weighted average crop
            crop_df['Diff Price Yield ($/acre)'] = abs(crop_df['Price Yield ($/acre)'] - wa_crop_value)
            crop_df['Percent Diff Price Yield (%)'] = abs(crop_df['Diff Price Yield ($/acre)']) / wa_crop_value * 100
            crop_df = crop_df.sort_values(by='Percent Diff Price Yield (%)')  # Sort by percent difference
            
            # Find the crop with the smallest price difference
            min_diff_crop = crop_df[['Crop Name', 'Percent Diff Price Yield (%)']].loc[crop_df['Percent Diff Price Yield (%)'].idxmin()]
            rows.append({
                'Crop_OpenAg': crop,
                'Crop Name': min_diff_crop['Crop Name'],
                'Percent Diff Price Yield (%)': min_diff_crop['Percent Diff Price Yield (%)']
            })
    
    lowest_diff_df = pd.DataFrame(rows)
    lowest_diff_df['Crop_OpenAg'] = 'WA_' + lowest_diff_df['Crop_OpenAg']
    
    # Extract the list of crops and their proxies
    crop_list = lowest_diff_df[['Crop_OpenAg', 'Crop Name']].values.flatten().tolist()
    
    return crop_list,lowest_diff_df

def plot_crop_data(agg_crops, crop_list, region_name='Sacramento River'):
    unique_crops = agg_crops['Crop_OpenAg'].unique()
    for crop in unique_crops:
        crop_data = agg_crops[agg_crops['Crop_OpenAg'] == crop]

        # Assign colors based on crop name presence in crop_list
        colors = ['orange' if name in crop_list else 'lightblue' for name in crop_data['Crop Name']] 
        
        # Create subplots
        fig, axs = plt.subplots(1, 2, figsize=(15, 5))  # 2 subplots
        axs[0].bar(crop_data['Crop Name'], crop_data['Price Yield ($/acre)'], color=colors)
        axs[0].set_title(f'{crop} {region_name} Price Yield ($/acre) in 2020')
        axs[0].set_ylabel('Price Yield ($/acre)')
        axs[0].tick_params(axis='x', rotation=90)
        axs[0].grid(axis='y', linestyle='--', alpha=0.7)
        
        # Exclude last row for the second plot
        crop_data = crop_data.iloc[:-1, :]
        axs[1].bar(crop_data['Crop Name'], crop_data['Percent Area (%)'], color=colors)
        axs[1].set_title(f'{crop} {region_name} Percent Area in 2020')
        axs[1].set_ylabel('Percent Area (%)')
        axs[1].tick_params(axis='x', rotation=90)
        axs[1].grid(axis='y', linestyle='--', alpha=0.7)
        axs[1].set_ylim(0, 100)

        # Ensure the directory exists
        save_path = f'Datasets/Outputs/commodity_crops/{region_name}_{crop}_plots.png'
        os.makedirs(os.path.dirname(save_path), exist_ok=True)  # Create directories if they don't exist
        plt.tight_layout()
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()
