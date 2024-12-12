# -*- coding: utf-8 -*-
"""
Created on Sat Nov  2 18:03:02 2024

@author: armen
"""
import pandas as pd
import matplotlib.pyplot as plt

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

usda_crops_20_sac = usda_crops_20.loc[usda_crops_20.HR_NAME == 'Sacramento River']
usda_crops_20_sac = usda_crops_20_sac.dropna(subset=['Area (acreage)','Price ($/unit)']) # drop nan rows because we cant do weighted average if either of this two are missing

## calculate acreage-weighted marginal revenue for each crop category

# Aggregate variables for each commodity crops by hydrolgic region 
agg_crops = usda_crops_20_sac.groupby('Crop Name').sum(numeric_only=True).reset_index()
agg_crops = agg_crops.merge(usda_openag_bridge_melted, left_on='Crop Name', right_on='USDA_Crop', how='left')

agg_crops = agg_crops.drop('USDA_Crop', axis=1)

# calculate revenue per year by multiplying each crop price per unit by its yield. Then multiply revenue by area
agg_crops['Price Yield ($/acre)'] = agg_crops['Price ($/unit)'] * agg_crops['Yield (unit/acreage)']
agg_crops['Price ($)'] = agg_crops['Price Yield ($/acre)'] * agg_crops['Area (acreage)']
agg_crops['Percent Area (%)'] = (agg_crops['Area (acreage)'] / agg_crops.groupby('Crop_OpenAg')['Area (acreage)'].transform('sum')).round(2)*100

# calculate the sum of crop prices multiplied by its acres
weighted_avg_revenue = agg_crops.groupby('Crop_OpenAg')[['Price ($)','Area (acreage)']].sum()
weighted_avg_revenue['Price Yield ($/acre)'] = weighted_avg_revenue['Price ($)']/weighted_avg_revenue['Area (acreage)']
weighted_avg_revenue = weighted_avg_revenue.reset_index()
weighted_avg_revenue['Crop Name'] = 'WA_' + weighted_avg_revenue['Crop_OpenAg']

# merge weighted average of marginal revenue with proxy crops df
agg_crops = pd.concat([agg_crops,weighted_avg_revenue],axis=0)
agg_crops.fillna(0, inplace=True)
agg_crops['Crop_OpenAg'] = agg_crops['Crop_OpenAg'].astype(str)

agg_crops = agg_crops[['Crop Name', 'Crop_OpenAg', 'Price ($/unit)', 'Production (unit)', 'Area (acreage)',
                       'Yield (unit/acreage)', 'Price Yield ($/acre)','Price ($)', 'Percent Area (%)']]


# For each crop category, calculate the absolute percent difference of price between the weighted average crop and the commodity crops. 
# The proxy crop is identified as the one with the smallest difference, which will be stored in a DataFrame

rows = []
for crop in agg_crops['Crop_OpenAg'].unique():
    crop_df = agg_crops[agg_crops['Crop_OpenAg'] == crop]
    wa_crop_value = crop_df[crop_df['Crop Name'] == f'WA_{crop}']['Price Yield ($/acre)']
    if not wa_crop_value.empty:
        wa_crop_value = wa_crop_value.values[0]
        crop_df = crop_df[crop_df['Crop Name'] != f'WA_{crop}']
        crop_df['Diff Price Yield ($/acre)'] = abs(crop_df['Price Yield ($/acre)'] - wa_crop_value)
        crop_df['Percent Diff Price Yield (%)'] = abs(crop_df['Diff Price Yield ($/acre)']) / wa_crop_value * 100
        crop_df = crop_df.sort_values(by='Percent Diff Price Yield (%)')
        min_diff_crop = crop_df[['Crop Name', 'Percent Diff Price Yield (%)']].loc[crop_df['Percent Diff Price Yield (%)'].idxmin()]
        rows.append({
            'Crop_OpenAg': crop,
            'Crop Name': min_diff_crop['Crop Name'],
            'Percent Diff Price Yield (%)': min_diff_crop['Percent Diff Price Yield (%)']
            })

lowest_diff_df = pd.DataFrame(rows)
lowest_diff_df['Crop_OpenAg'] = 'WA_' + lowest_diff_df['Crop_OpenAg']
crop_list = lowest_diff_df[['Crop_OpenAg', 'Crop Name']].values.flatten().tolist()

#%%
unique_crops = agg_crops['Crop_OpenAg'].unique()
# unique_crops = unique_crops[0:7]

for crop in unique_crops:
    crop_data = agg_crops[agg_crops['Crop_OpenAg'] == crop]
    
    colors = ['orange' if name in crop_list else 'lightblue' for name in crop_data['Crop Name']] 
    fig, axs = plt.subplots(1, 2, figsize=(15, 5))  # 2 rows, 1 column
    axs[0].bar(crop_data['Crop Name'], crop_data['Price Yield ($/acre)'], color=colors)
    axs[0].set_title(f'{crop} Sacramento River Price Yield ($/acre) in 2020')
    axs[0].set_ylabel('Price Yield ($/acre)')
    axs[0].tick_params(axis='x', rotation=90)
    axs[0].grid(axis='y', linestyle='--', alpha=0.7) 
    crop_data = crop_data.iloc[:-1,:]
    axs[1].bar(crop_data['Crop Name'], crop_data['Percent Area (%)'], color=colors)
    axs[1].set_title(f'{crop} Sacramento River Percent Area in 2020')
    axs[1].set_ylabel('Percent Area (%)')
    axs[1].tick_params(axis='x', rotation=90)
    axs[1].grid(axis='y', linestyle='--', alpha=0.7)
    axs[1].set_ylim(0, 100)

    plt.tight_layout()
    plt.savefig(f'Datasets/Outputs/commodity crops/{crop}_plots.png', bbox_inches='tight')
    plt.close()

#%%

crop = 'Orchards'
crop_df = agg_crops[agg_crops['Crop_OpenAg'] == crop]
wa_crop_value = crop_df[crop_df['Crop Name'] == f'WA_{crop}']['Price Yield ($/acre)'].values[0]

crop_df = crop_df[crop_df['Crop Name'] != f'WA_{crop}']
crop_df['Diff Price Yield ($/acre)'] = abs(crop_df['Price Yield ($/acre)'] - wa_crop_value)
crop_df['Percent Diff Price Yield (%)'] = abs(crop_df['Diff Price Yield ($/acre)']) / wa_crop_value * 100

crop_df = crop_df.sort_values(by='Percent Diff Price Yield (%)')
min_diff_crop = crop_df[['Crop Name', 'Percent Diff Price Yield (%)']].loc[crop_df['Percent Diff Price Yield (%)'].idxmin()]

crop_data = agg_crops[agg_crops['Crop_OpenAg'] == crop]

colors = ['orange' if name in crop_list else 'lightblue' for name in crop_data['Crop Name']] 
fig, axs = plt.subplots(1, 2, figsize=(15, 5))  # 2 rows, 1 column
axs[0].bar(crop_data['Crop Name'], crop_data['Price Yield ($/acre)'], color=colors)
axs[0].set_title(f'{crop} Sacramento River Price Yield ($/acre) in 2020')
axs[0].set_ylabel('Price Yield ($/acre)')
axs[0].tick_params(axis='x', rotation=90)
axs[0].grid(axis='y', linestyle='--', alpha=0.7) 
crop_data = crop_data.iloc[:-1,:]
axs[1].bar(crop_data['Crop Name'], crop_data['Percent Area (%)'], color=colors)
axs[1].set_title(f'{crop} Sacramento River Percent Area in 2020')
axs[1].set_ylabel('Percent Area (%)')
axs[1].tick_params(axis='x', rotation=90)
axs[1].grid(axis='y', linestyle='--', alpha=0.7)
axs[1].set_ylim(0, 100)

plt.tight_layout()
plt.show()
