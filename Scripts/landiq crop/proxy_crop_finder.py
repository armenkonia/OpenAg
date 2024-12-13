# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:54:20 2024

@author: armen
"""
import pandas as pd
import matplotlib.pyplot as plt
import os
import pickle 
usda_crops_av = pd.read_csv('../../Datasets/Output/processed_usda_crops_18_22.csv',index_col=0)
#only keep relevant columns
# usda_crops_av = usda_crops_av[['County', 'Crop Name','HR_NAME','value','year','type']]
#transform back to original format
usda_crops_av = usda_crops_av.pivot_table(index=["County", "Crop Name", "HR_NAME"], columns="type", values="value", aggfunc="mean").reset_index()
usda_crops_av = usda_crops_av[['Crop Name', 'County', 'HR_NAME', 'price', 'Production', 'Acres','yield']]
usda_crops_av.columns = ['Crop Name', 'County', 'HR_NAME', 'Price ($/unit)', 'Production (unit)', 'Area (acreage)', 'Yield (unit/acreage)']
usda_crops_av = usda_crops_av.dropna(subset=['Area (acreage)','Price ($/unit)']) # drop nan rows because we cant do weighted average if either of this two are missing


usda_openag_bridge = pd.read_excel('../../Datasets/bridge openag.xlsx',sheet_name='updated usda & openag', header=0)
value_vars = [col for col in usda_openag_bridge.columns if col != 'Crop_OpenAg'] # Identify all usda columns
usda_openag_bridge_melted = pd.melt(usda_openag_bridge, id_vars=['Crop_OpenAg'], value_vars=value_vars, value_name='USDA_Crop')
usda_openag_bridge_melted = usda_openag_bridge_melted.dropna(subset=['USDA_Crop']).reset_index(drop=True)
usda_openag_bridge_melted = usda_openag_bridge_melted.drop(columns=['variable'])

# =============================================================================
# Calculate acreage-weighted average price yield for each crop category
# =============================================================================
def calculate_agg_crops(usda_crops_20_sac, usda_openag_bridge_melted):
    # Aggregate variables for each commodity crop by hydrologic region
    agg_crops = usda_crops_20_sac.groupby(["Crop Name", "HR_NAME"]).apply(
        lambda group: pd.Series({
            "Price ($/unit)": (group["Price ($/unit)"] * group
                               ["Area (acreage)"]).sum() / group["Area (acreage)"].sum(),
            "Yield (unit/acreage)": (group["Yield (unit/acreage)"] * group["Area (acreage)"]).sum() / group["Area (acreage)"].sum(),
            "Production (unit)": group["Production (unit)"].sum(),
            "Area (acreage)": group["Area (acreage)"].sum(),
        })
    ).reset_index()
    # agg_crops = usda_crops_20_sac.groupby('Crop Name').sum(numeric_only=True).reset_index()
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
# agg_crops = calculate_agg_crops(usda_crops_20_sac, usda_openag_bridge_melted)

def select_proxy_crop(crop, area_diff_threshold=10):
    """
    Selects a proxy crop for a given crop based on price yield and area coverage criteria.

    Parameters:
    - crop (str): The crop name to find a proxy for.
    - area_diff_threshold (int): Threshold for determining if the top crop by area should be chosen based on area difference.

    Returns:
    - dict: A dictionary with the proxy crop name as the key and the corresponding 'Crop_OpenAg' as the value.
    """
    # Filter for rows with the specified crop
    crop_df = agg_crops[agg_crops['Crop_OpenAg'] == crop].copy()

    # Retrieve the 'Price Yield' of the 'WA' crop for comparison
    wa_crop_name = f'WA_{crop}'
    wa_crop_value = crop_df.loc[crop_df['Crop Name'] == wa_crop_name, 'Price Yield ($/acre)'].values[0]

    # Exclude 'WA' crop from comparison and calculate price yield differences
    crop_df = crop_df[crop_df['Crop Name'] != wa_crop_name]
    crop_df['Diff Price Yield ($/acre)'] = abs(crop_df['Price Yield ($/acre)'] - wa_crop_value)
    crop_df['Percent Diff Price Yield (%)'] = (crop_df['Diff Price Yield ($/acre)'] / wa_crop_value) * 100

    # Sort crops by 'Percent Area (%)' in descending order and calculate the area difference from the largest area
    crop_df = crop_df.sort_values(by='Percent Area (%)', ascending=False)
    top_area = crop_df['Percent Area (%)'].iloc[0]
    crop_df['Diff Percent Area (%)'] = top_area - crop_df['Percent Area (%)']

    # Initialize dictionary for proxy crop
    proxy_crop = {}

    # Logic for selecting the proxy crop
    if len(crop_df) == 1:
        # Only one potential proxy crop is available
        proxy_crop = {crop_df.iloc[0]['Crop Name']: crop_df.iloc[0]['Crop_OpenAg']}
    
    elif len(crop_df) > 1:
        # If top crop has a significant area difference, select it as the proxy crop
        if crop_df.iloc[1]['Diff Percent Area (%)'] > area_diff_threshold:
            proxy_crop = {crop_df.iloc[0]['Crop Name']: crop_df.iloc[0]['Crop_OpenAg']}
        else:
            # Otherwise, select the crop with the smallest price yield difference as the proxy
            crop_df = crop_df[crop_df['Diff Percent Area (%)'] < area_diff_threshold]
            min_diff_row = crop_df.loc[crop_df['Percent Diff Price Yield (%)'].idxmin()]
            proxy_crop = {min_diff_row['Crop Name']: min_diff_row['Crop_OpenAg']}
    
    return proxy_crop
# crop = 'Orchards'
# crop = 'Almonds'
# proxy_crop = select_proxy_crop(crop=crop, area_diff_threshold=5)

def get_proxy_crops_for_all(agg_crops, area_diff_threshold=10):
    """
    Finds proxy crops for all crops in the 'agg_crops' DataFrame based on area difference and price yield criteria.

    Parameters:
    - agg_crops (DataFrame): DataFrame containing crop data with 'Crop_OpenAg' and 'Crop Name'.
    - area_diff_threshold (int): Threshold for selecting crops based on area difference.

    Returns:
    - tuple: A flattened list of proxy crops and a DataFrame with detailed crop selection information.
    """
    proxy_crop_rows = {}

    # Iterate through each unique crop in the 'Crop_OpenAg' column
    for crop in agg_crops['Crop_OpenAg'].unique():
        # Select proxy crop for the current crop
        proxy_crop = select_proxy_crop(crop=crop, area_diff_threshold=area_diff_threshold)
        proxy_crop_rows.update(proxy_crop)

    # Convert the dictionary of proxy crops to a DataFrame
    proxy_crops_df = pd.DataFrame.from_dict(proxy_crop_rows, orient='index', columns=['Crop_OpenAg']).reset_index()
    proxy_crops_df.columns = ['Crop Name', 'Crop_OpenAg']

    # Flatten the DataFrame to a list of ['Crop_OpenAg', 'Crop Name']
    proxy_crop_list = proxy_crops_df[['Crop_OpenAg', 'Crop Name']].values.flatten().tolist()

    return proxy_crop_list, proxy_crops_df
# crop_list, lowest_diff_df = get_proxy_crops_for_all(agg_crops)

def plot_crop_data(agg_crops, crop_list, region_name='Sacramento River'):
    """
    Plots price yield and percent area for each crop in the given region.
    
    Parameters:
    - agg_crops (DataFrame): DataFrame containing crop data.
    - crop_list (list): List of crop names to highlight in the plot.
    - region_name (str): Name of the region (default is 'Sacramento River').
    """
    # Get unique crops from the 'Crop_OpenAg' column
    unique_crops = agg_crops['Crop_OpenAg'].unique()

    # Iterate over each crop to generate plots
    for crop in unique_crops:
        # Filter data for the current crop
        crop_data = agg_crops[agg_crops['Crop_OpenAg'] == crop]

        # Assign colors based on whether the crop name is in crop_list
        colors = ['orange' if name in crop_list else 'lightblue' for name in crop_data['Crop Name']]

        # Create subplots: one for price yield and one for percent area
        fig, axs = plt.subplots(1, 2, figsize=(15, 5))  # 2 subplots in a row

        # Plot Price Yield on the first subplot
        axs[0].bar(crop_data['Crop Name'], crop_data['Price Yield ($/acre)'], color=colors)
        axs[0].set_title(f'{crop} {region_name} Price Yield ($/acre) in 2020')
        axs[0].set_ylabel('Price Yield ($/acre)')
        axs[0].tick_params(axis='x', rotation=90)
        axs[0].grid(axis='y', linestyle='--', alpha=0.7)

        # Exclude the last row for the second plot (Percent Area)
        crop_data = crop_data.iloc[:-1, :]  # Exclude the last row
        axs[1].bar(crop_data['Crop Name'], crop_data['Percent Area (%)'], color=colors)
        axs[1].set_title(f'{crop} {region_name} Percent Area in 2020')
        axs[1].set_ylabel('Percent Area (%)')
        axs[1].tick_params(axis='x', rotation=90)
        axs[1].grid(axis='y', linestyle='--', alpha=0.7)
        axs[1].set_ylim(0, 100)  # Set y-axis limit for percent area

        # Adjust layout to prevent overlap and save the plot
        save_path = f'../../Datasets/Output/Data Validation/commodity_crops/{region_name}_{crop}_plots.png'
        os.makedirs(os.path.dirname(save_path), exist_ok=True)  # Create directories if they don't exist
        plt.tight_layout()
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()  # Close the figure to avoid memory issues
# plot_crop_data(agg_crops, crop_list, region_name='Sacramento River')


hr_crop_analysis_results_dict  = {}
for hr_name in usda_crops_av['HR_NAME'].unique():
    # Filter the data for the specific HR_NAME
    usda_crops_selected = usda_crops_av.loc[usda_crops_av.HR_NAME == hr_name]
    # Calculate the aggregated crops data for the HR
    agg_crops = calculate_agg_crops(usda_crops_selected, usda_openag_bridge_melted)
    # Find the proxy crops for the HR
    crop_list,lowest_diff_df = get_proxy_crops_for_all(agg_crops)
    # Plot the crop data and save the plots
    plot_crop_data(agg_crops, crop_list, region_name=hr_name)
    # Store the results for the current HR_NAME
    hr_crop_analysis_results_dict [hr_name] = {'agg_crops': agg_crops,
                                               'proxy crop': lowest_diff_df}
    
with open('../../Datasets/Output/hr_crop_analysis_results.pkl', 'wb') as f:
    pickle.dump(hr_crop_analysis_results_dict, f) 

# Retrieve proxy crops for each HR
proxy_crop_info_by_hr = {}
proxy_crops_list = []
for hr_name, result in hr_crop_analysis_results_dict.items():
    proxy_crop_info_by_hr[hr_name] = result['agg_crops']
    proxy_crops_df = result['proxy crop']
    proxy_crops_df['HR_NAME'] = hr_name
    proxy_crops_list.append(proxy_crops_df)
proxy_crops_df = pd.concat(proxy_crops_list, ignore_index=True)
proxy_crops_df['Crop_OpenAg'] = proxy_crops_df['Crop_OpenAg'].str.replace('^WA_', '', regex=True)
proxy_crops_df.to_csv('../../Datasets/Output/proxy_crops_hr.csv')
