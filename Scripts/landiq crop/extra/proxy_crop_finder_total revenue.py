# -*- coding: utf-8 -*-
"""
Created on Sat Nov  2 18:03:02 2024

@author: armen
"""
import pandas as pd
import matplotlib.pyplot as plt
import os
import pickle 

usda_crops = pd.read_csv(r"C:/Users/armen/Desktop/COEQWAL/Datasets/Outputs/updated_usda_crops_18_22.csv")
usda_openag_bridge = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\bridging between datasets (work in progress).xlsx",sheet_name='final upd bridge USDA & OpenAG', header=0, nrows=25, usecols="A:X")

# melt usda_openag_bridge dataset
value_vars = [col for col in usda_openag_bridge.columns if col != 'Crop_OpenAg'] # Identify all usda columns
usda_openag_bridge_melted = pd.melt(usda_openag_bridge, id_vars=['Crop_OpenAg'], value_vars=value_vars, value_name='USDA_Crop')
usda_openag_bridge_melted = usda_openag_bridge_melted.dropna(subset=['USDA_Crop']).reset_index(drop=True)
usda_openag_bridge_melted = usda_openag_bridge_melted.drop(columns=['variable'])

# check for crops in usda_openag_bridge that are missing in usda crops
not_found_in_usda = usda_openag_bridge_melted[~usda_openag_bridge_melted['USDA_Crop'].isin(set(usda_crops['Crop Name']))].reset_index(drop=True)

# work with 2020 and sacramento only
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
    agg_crops['Price Area ($.acre)'] = agg_crops['Price ($)'] * agg_crops['Area (acreage)']
    agg_crops['Percent Area (%)'] = (agg_crops['Area (acreage)'] / agg_crops.groupby('Crop_OpenAg')['Area (acreage)'].transform('sum')).round(2) * 100

    # Calculate the sum of crop prices multiplied by its acres
    weighted_avg_revenue = agg_crops.groupby('Crop_OpenAg')[['Price Area ($.acre)', 'Area (acreage)']].sum()
    weighted_avg_revenue['Price ($)'] = weighted_avg_revenue['Price Area ($.acre)'] / weighted_avg_revenue['Area (acreage)']
    weighted_avg_revenue = weighted_avg_revenue.reset_index()
    weighted_avg_revenue['Crop Name'] = 'WA_' + weighted_avg_revenue['Crop_OpenAg']

    # Merge weighted average of marginal revenue with proxy crops df
    agg_crops = pd.concat([agg_crops, weighted_avg_revenue], axis=0)
    agg_crops.fillna(0, inplace=True)
    agg_crops['Crop_OpenAg'] = agg_crops['Crop_OpenAg'].astype(str)

    # Return the relevant columns
    agg_crops = agg_crops[['Crop Name', 'Crop_OpenAg', 'Price ($/unit)', 'Production (unit)', 'Area (acreage)',
                           'Yield (unit/acreage)', 'Price Yield ($/acre)', 'Price ($)', 'Price Area ($.acre)', 'Percent Area (%)']]
    
    return agg_crops

agg_crops = calculate_agg_crops(usda_crops_20_sac, usda_openag_bridge_melted)

#%%
# For each crop category, calculate the absolute percent difference of price between the weighted average crop and the commodity crops. 
# The proxy crop is identified as the one with the smallest difference, which will be stored in a DataFrame
price_yield_column = 'Price ($)'
def find_proxy_crops(agg_crops, price_yield_column):
    rows = []
    for crop in agg_crops['Crop_OpenAg'].unique():
        crop_df = agg_crops[agg_crops['Crop_OpenAg'] == crop]
        wa_crop_value = crop_df[crop_df['Crop Name'] == f'WA_{crop}'][price_yield_column]
        
        # Check if the weighted average crop value exists
        if not wa_crop_value.empty:
            wa_crop_value = wa_crop_value.values[0]
            crop_df = crop_df[crop_df['Crop Name'] != f'WA_{crop}']  # Exclude the weighted average crop
            crop_df[f'Diff {price_yield_column}'] = abs(crop_df[price_yield_column] - wa_crop_value)
            crop_df[f'Percent Diff {price_yield_column} (%)'] = abs(crop_df[f'Diff {price_yield_column}']) / wa_crop_value * 100
            crop_df = crop_df.sort_values(by=f'Percent Diff {price_yield_column} (%)')  # Sort by percent difference
            
            # Find the crop with the smallest price difference
            min_diff_crop = crop_df[['Crop Name', f'Percent Diff {price_yield_column} (%)']].loc[crop_df[f'Percent Diff {price_yield_column} (%)'].idxmin()]
            rows.append({
                'Crop_OpenAg': crop,
                'Crop Name': min_diff_crop['Crop Name'],
                f'Percent Diff {price_yield_column} (%)': min_diff_crop[f'Percent Diff {price_yield_column} (%)']
            })
    
    lowest_diff_df = pd.DataFrame(rows)
    lowest_diff_df['Crop_OpenAg'] = 'WA_' + lowest_diff_df['Crop_OpenAg']
    
    # Extract the list of crops and their proxies
    crop_list = lowest_diff_df[['Crop_OpenAg', 'Crop Name']].values.flatten().tolist()
    
    return crop_list, lowest_diff_df

crop_list,lowest_diff_df = find_proxy_crops(agg_crops,price_yield_column)
#%%
def plot_crop_data(agg_crops, crop_list, region_name='Sacramento River'):
    unique_crops = agg_crops['Crop_OpenAg'].unique()
    for crop in unique_crops:
        crop_data = agg_crops[agg_crops['Crop_OpenAg'] == crop]

        # Assign colors based on crop name presence in crop_list
        colors = ['orange' if name in crop_list else 'lightblue' for name in crop_data['Crop Name']] 
        
        # Create subplots
        fig, axs = plt.subplots(1, 2, figsize=(15, 5))  # 2 subplots
        axs[0].bar(crop_data['Crop Name'], crop_data['Price ($)'], color=colors)
        axs[0].set_title(f'{crop} {region_name} Price ($) in 2020')
        axs[0].set_ylabel('Total Revenue ($)')
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
        save_path = f'Datasets/Outputs/commodity_crops/total revenue/{region_name}_{crop}_plots.png'
        os.makedirs(os.path.dirname(save_path), exist_ok=True)  # Create directories if they don't exist
        plt.tight_layout()
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()

plot_crop_data(agg_crops, crop_list, region_name='Sacramento River')


#%%
hr_crop_analysis_results_dict  = {}

for hr_name in usda_crops_20['HR_NAME'].unique():
    # Filter the data for the specific HR_NAME
    usda_crops_selected = usda_crops_20.loc[usda_crops_20.HR_NAME == hr_name]
    # Calculate the aggregated crops data for the HR
    agg_crops = calculate_agg_crops(usda_crops_selected, usda_openag_bridge_melted)
    # Find the proxy crops for the HR
    crop_list,lowest_diff_df = find_proxy_crops(agg_crops,price_yield_column)
    # Plot the crop data and save the plots
    plot_crop_data(agg_crops, crop_list, region_name=hr_name)
    
    # Store the results for the current HR_NAME
    hr_crop_analysis_results_dict [hr_name] = {
        'agg_crops': agg_crops,
        'lowest_diff_df': lowest_diff_df
    }

# with open(r"C:\Users\armen\Desktop\COEQWAL\Datasets\Outputs\hr_crop_analysis_results.pkl", 'wb') as f:
#     pickle.dump(hr_crop_analysis_results_dict, f) 