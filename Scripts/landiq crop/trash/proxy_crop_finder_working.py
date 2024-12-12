# -*- coding: utf-8 -*-
"""
Created on Fri Nov  8 08:52:18 2024

@author: armen
"""
import pandas as pd
import matplotlib.pyplot as plt
import os

usda_crops = pd.read_csv(r"C:/Users/armen/Desktop/COEQWAL/Datasets/Outputs/updated_usda_crops_18_22.csv")
usda_openag_bridge = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\bridging between datasets (work in progress).xlsx",sheet_name='final upd bridge USDA & OpenAG', header=0, nrows=25, usecols="A:X")

# melt usda_openag_bridge dataset
value_vars = [col for col in usda_openag_bridge.columns if col != 'Crop_OpenAg'] # Identify all usda columns
usda_openag_bridge_melted = pd.melt(usda_openag_bridge, id_vars=['Crop_OpenAg'], value_vars=value_vars, value_name='USDA_Crop')
usda_openag_bridge_melted = usda_openag_bridge_melted.dropna(subset=['USDA_Crop']).reset_index(drop=True)
usda_openag_bridge_melted = usda_openag_bridge_melted.drop(columns=['variable'])

# check for crops in usda_openag_bridge that are missing in usda crops
not_found_in_usda = usda_openag_bridge_melted[~usda_openag_bridge_melted['USDA_Crop'].isin(set(usda_crops['Crop Name']))].reset_index(drop=True)

# work with 2018 and sacramento only
usda_crops_20 = usda_crops[['Crop Name', 'County', 'HR_NAME', 'price_2020','Production_2020','Acres_2020', 'yield_2020']]
usda_crops_20.columns = ['Crop Name', 'County', 'HR_NAME', 'Price ($/unit)','Production (unit)', 'Area (acreage)', 'Yield (unit/acreage)']
usda_crops_20 = usda_crops_20.dropna(subset=['Area (acreage)','Price ($/unit)']) # drop nan rows because we cant do weighted average if either of this two are missing
usda_crops_20_sac = usda_crops_20.loc[usda_crops_20.HR_NAME == 'Sacramento River']

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

agg_crops = calculate_agg_crops(usda_crops_20_sac, usda_openag_bridge_melted)

#%%
def select_proxy_crop(crop, area_threshold=40, area_diff_threshold=5, price_yield_diff_threshold=10):
    """
    Select a proxy crop based on area percentage and price yield differences.

    Parameters:
    crop (str): The specific crop to find a proxy for.
    area_threshold (float): The minimum percentage of area for crops to be considered (default is 40%).
    area_diff_threshold (float): The minimum difference in area percentage to select the top crop (default is 5%).
    price_yield_diff_threshold (float): The threshold for the price yield difference to consider for selecting proxy crop (default is 10%).

    Returns:
    dict: Dictionary with 'Crop Name' as the key and 'Crop_OpenAg' as the value representing the proxy crop.
    """
    # Filter data for the specific crop
    crop_df = agg_crops[agg_crops['Crop_OpenAg'] == crop]
    
    # Get the Price Yield of the 'WA' crop for comparison
    wa_crop_value = crop_df[crop_df['Crop Name'] == f'WA_{crop}']['Price Yield ($/acre)'].values[0]
    
    # Remove 'WA' crop and calculate the price yield differences
    crop_df = crop_df[crop_df['Crop Name'] != f'WA_{crop}']
    crop_df['Diff Price Yield ($/acre)'] = abs(crop_df['Price Yield ($/acre)'] - wa_crop_value)
    crop_df['Percent Diff Price Yield (%)'] = (abs(crop_df['Diff Price Yield ($/acre)']) / wa_crop_value) * 100

    # Sort crops by 'Percent Area (%)' in descending order and calculate the difference in area
    crop_df = crop_df.sort_values(by='Percent Area (%)', ascending=False)
    crop_df['Diff Percent Area (%)'] = -crop_df['Percent Area (%)'].diff()

    # Filter crops with 'Percent Area (%)' greater than the area threshold
    crop_df_40 = crop_df[crop_df['Percent Area (%)'] > area_threshold]

    # Initialize proxy crop dictionary
    proxy_crop = {}

    if len(crop_df_40) == 1:
        # If only one crop meets the threshold, select it as the proxy crop
        usda_crop = crop_df_40.iloc[0]['Crop Name']
        open_ag_crop = crop_df_40.iloc[0]['Crop_OpenAg']
        proxy_crop[usda_crop] = open_ag_crop

    elif len(crop_df_40) > 1:
        # If more than one crop meets the threshold
        if crop_df_40.iloc[1]['Diff Percent Area (%)'] > area_diff_threshold:
            # If the difference in percent area between the top two crops is greater than the area_diff_threshold, choose the top crop
            usda_crop = crop_df_40.iloc[0]['Crop Name']
            open_ag_crop = crop_df_40.iloc[0]['Crop_OpenAg']
            proxy_crop[usda_crop] = open_ag_crop
        else:
            # If the difference is not significant, find the crop with the minimum difference in price yield
            min_diff_crop = crop_df_40.loc[crop_df_40['Percent Diff Price Yield (%)'].idxmin(),
                                           ['Crop Name', 'Crop_OpenAg', 'Percent Diff Price Yield (%)']]
            usda_crop = min_diff_crop['Crop Name']
            open_ag_crop = min_diff_crop['Crop_OpenAg']
            proxy_crop[usda_crop] = open_ag_crop

    else:
        # If no crops meet the threshold in crop_df_40
        if crop_df.iloc[1]['Diff Percent Area (%)'] > area_diff_threshold:
            # Select the top crop by area if it has a significant lead over the next crop
            usda_crop = crop_df.iloc[0]['Crop Name']
            open_ag_crop = crop_df.iloc[0]['Crop_OpenAg']
            proxy_crop[usda_crop] = open_ag_crop
        else:
            # Otherwise, find the crop with the minimum difference in price yield across all crops
            min_diff_crop = crop_df.loc[crop_df['Percent Diff Price Yield (%)'].idxmin(),
                                        ['Crop Name', 'Crop_OpenAg', 'Percent Diff Price Yield (%)']]
            usda_crop = min_diff_crop['Crop Name']
            open_ag_crop = min_diff_crop['Crop_OpenAg']
            proxy_crop[usda_crop] = open_ag_crop

    return proxy_crop
crop = 'Orchards'
proxy_crop = select_proxy_crop(crop=crop, area_threshold=40, area_diff_threshold=5, price_yield_diff_threshold=10)

#%%

# proxy_crop = select_proxy_crop(crop_df, crop='Almond', area_threshold=40, area_diff_threshold=5, price_yield_diff_threshold=10)
rows = {}
for crop in agg_crops['Crop_OpenAg'].unique():
    # crop_df = agg_crops[agg_crops['Crop_OpenAg'] == crop]
    
    proxy_crop = select_proxy_crop(crop=crop, area_threshold=40, area_diff_threshold=5, price_yield_diff_threshold=10)
    rows.update(proxy_crop)
lowest_diff_df = pd.DataFrame.from_dict(rows, orient='index', columns=['Crop_OpenAg']).reset_index()
lowest_diff_df.columns = ['Crop Name','Crop_OpenAg']
crop_list = lowest_diff_df[['Crop_OpenAg', 'Crop Name']].values.flatten().tolist()
#%%
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

        # Adjust layout and save the plot
        # Ensure the directory exists
        save_path = f'Datasets/Outputs/commodity_crops/new_proxies/{region_name}_{crop}_plots.png'
        os.makedirs(os.path.dirname(save_path), exist_ok=True)  # Create directories if they don't exist
        plt.tight_layout()
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()

plot_crop_data(agg_crops, crop_list, region_name='Sacramento River')