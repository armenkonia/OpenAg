# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 16:22:53 2024

@author: armen
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

usda_crops = pd.read_csv('../../Datasets/econ_crop_data/usda_crops_18_22.csv')
counties_hr = pd.read_csv('../../Datasets/econ_crop_data/counties_hr_neighbors.csv')

## transform the USDA crops dataset into a more interpretable format
usda_crops['County'] = usda_crops['County'].str.strip().str.lower()
counties_hr['NAME'] = counties_hr['NAME'].str.strip().str.lower()
usda_crops = usda_crops.merge(counties_hr[['NAME']],left_on='County',right_on='NAME', how='left').drop('NAME',axis=1)

usda_openag_bridge = pd.read_excel('../../Datasets/econ_crop_data/bridge openag.xlsx',sheet_name='usda & openag', header=0, nrows=25)

# keep price, yield, and area for each crop in every county for the years 2018 to 2022
usda_crops = usda_crops[['Year', 'Crop Name','County', 'Price P/U','Production','Yield','Harvested Acres','Unit']]
usda_crops['Harvested Acres'] = pd.to_numeric(usda_crops['Harvested Acres'], errors='coerce')
usda_crops['Production'] = pd.to_numeric(usda_crops['Production'], errors='coerce')
# create a pivot table for price, yield, acres, and production. And merge dfs with crops and counties on the x-axis
price_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Price P/U').add_prefix('price_').reset_index()
yield_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Yield').add_prefix('yield_').reset_index()
acres_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Harvested Acres').add_prefix('Acres_').reset_index()
production_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Production').add_prefix('Production_').reset_index()

usda_crops['Unit'] = usda_crops['Unit'].str.strip()  # Removes leading and trailing whitespace
unit_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Unit',aggfunc='first').add_prefix('Unit_').reset_index()
unit_df = unit_df[['Crop Name', 'County', 'Unit_2018']]


# usda_crops['Unit'] = usda_crops['Unit'].str.strip()  # Removes leading and trailing whitespace
# inconsistent_units = usda_crops.groupby(['Crop Name', 'County', 'HR_NAME'])['Unit'].nunique()
# unit_groups = usda_crops.groupby(['Crop Name', 'County', 'HR_NAME'])['Unit'].nunique()
# inconsistent_groups = unit_groups[unit_groups > 1].index
# # Filter the original DataFrame to show rows with these inconsistent units
# inconsistent_rows = usda_crops[usda_crops.set_index(['Crop Name', 'County', 'HR_NAME']).index.isin(inconsistent_groups)]
# unit_df = inconsistent_rows.pivot_table(index=['Crop Name', 'County', 'HR_NAME'], columns='Year', values='Unit',aggfunc='first').add_prefix('Unit_').reset_index()
# unit_df = unit_df[['Crop Name', 'County', 'HR_NAME', 'Unit_2018']]

usda_crops = pd.merge(price_df, yield_df, on=['County', 'Crop Name'], how='outer')
usda_crops = pd.merge(usda_crops, acres_df, on=['County', 'Crop Name'], how='outer')
usda_crops = pd.merge(usda_crops, production_df, on=['County', 'Crop Name'], how='outer')
usda_crops = pd.merge(usda_crops, unit_df, on=['County', 'Crop Name'], how='left')


## update the bridge by eliminating duplicate USDA crop entries
# keep usda crops that are found in bridge
usda_crops_used = pd.unique(usda_openag_bridge.iloc[:,1:].values.ravel('K'))
usda_crops = usda_crops[usda_crops['Crop Name'].isin(usda_crops_used)]

# create a dictionary to identify potentially duplicate crops and determine the appropriate method for combining them
potential_duplicates = {
    'Plums Dried': ['Plums Dried (Prunes)'],
    'Seed Field Crops Misc': ['Field Crops Seed Misc'],
    'Field Crops Seed Misc.': ['Field Crops Seed Misc'],
    'Citrus By-Products Misc.': ['Citrus By-Products Misc'],
    'Seed Sunflower Planting': ['Sunflower Seed Planting'],
    'Seed Rice': ['Rice Seed'],
    'Seed Potato': ['Potatoes Seed'],
    'Pears Bartlett': ['Pears Unspecified', 'Pears Asian']
}
duplicate_crops_dict = {}
for crop, duplicates in potential_duplicates.items():
    # Combine the crop and its duplicates for filtering
    filtered_df = usda_crops[usda_crops['Crop Name'].isin([crop] + duplicates)]
    key = f"{crop} & {' / '.join(duplicates)}"
    duplicate_crops_dict[key] = filtered_df

# remove duplicates
usda_crops['Crop Name'] = usda_crops['Crop Name'].replace({
    'Plums Dried': 'Plums Dried (Prunes)',
    'Seed Field Crops Misc': 'Field Crops Seed Misc',
    'Field Crops Seed Misc.': 'Field Crops Seed Misc',
    'Citrus By-Products Misc.': 'Citrus By-Products Misc',
    'Seed Sunflower Planting': 'Sunflower Seed Planting',
    'Seed Rice': 'Rice Seed',
    'Seed Potato': 'Potatoes Seed',
})
# Group by 'Crop Name' and 'County', then aggregate using max() to combine the duplicate crops 
usda_crops = usda_crops.groupby(['County', 'Crop Name'], as_index=False).first()

# Update the bridge since we have removed duplicated crops
usda_crops_used = usda_crops['Crop Name'].unique()
mask = usda_openag_bridge.isin(usda_crops_used)
mask.iloc[:, 0] = True
usda_openag_bridge_updated = usda_openag_bridge.where(mask)

# The function moves all non-empty values to the start of a column, pushing the empty spots out.
def squeeze_nan(x):
    original_columns = x.index.tolist()
    squeezed = x.dropna()
    squeezed.index = [original_columns[n] for n in range(squeezed.count())]
    return squeezed.reindex(original_columns, fill_value=np.nan)

usda_openag_bridge_updated = usda_openag_bridge_updated.apply(squeeze_nan, axis=1)
usda_openag_bridge_updated = usda_openag_bridge_updated.dropna(axis=1, how='all')

## update usda crops dataset to include geometric information
usda_crops = usda_crops.merge(counties_hr[['NAME', 'HR_NAME','Neighboring Counties', 'Neighboring HR']],left_on='County',right_on='NAME', how='left').drop('NAME',axis=1)
usda_crops = usda_crops[['County', 'Crop Name', 'HR_NAME', 'Neighboring Counties', 'Neighboring HR',
                            'price_2018', 'price_2019', 'price_2020','price_2021', 'price_2022', 
                            'yield_2018', 'yield_2019', 'yield_2020',
                            'yield_2021', 'yield_2022', 
                            'Acres_2018', 'Acres_2019', 'Acres_2020',
                            'Acres_2021', 'Acres_2022', 
                            'Production_2018', 'Production_2019',
                            'Production_2020', 'Production_2021', 'Production_2022', 
                            'Unit_2018'
                            ]]
usda_crops.to_csv('../../Datasets/econ_crop_data/processed_usda_crops_18_22.csv')
with pd.ExcelWriter('../../Datasets/econ_crop_data/bridge openag.xlsx', engine='openpyxl', mode='a') as writer:
    usda_openag_bridge_updated.to_excel(writer, sheet_name='updated usda & openag', index=False)
