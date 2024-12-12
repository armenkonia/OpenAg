# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 15:07:58 2024

@author: armen
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

landiq20 = gpd.read_file(r"Datasets/i15_crop_mapping_2020/i15_Crop_Mapping_2020.shp")
landiq20 = landiq20[~landiq20['CROPTYP2'].isin(['X', 'U'])]
landiq20 = landiq20[['CROPTYP2','REGION','ACRES', 'COUNTY','geometry']]

counties = gpd.read_file(r"C:/Users/armen/Desktop/COEQWAL/Datasets/ca_counties/CA_Counties.shp")

landiq20 = landiq20.to_crs(epsg=3310)
counties = counties.to_crs(epsg=3310)

landiq20_with_counties = gpd.sjoin(landiq20, counties, how="left", predicate="intersects")

landiq20_merced = landiq20_with_counties.loc[landiq20_with_counties.NAME == 'Merced']

usda_crops = pd.read_csv(r"C:/Users/armen/Desktop/COEQWAL/Datasets/usda_crops_18_22.csv")
price_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Price P/U').add_prefix('price_').reset_index()
yield_df = usda_crops.pivot_table(index=['Crop Name', 'County'], columns='Year', values='Yield').add_prefix('yield_').reset_index()
merged_df = pd.merge(price_df, yield_df, on=['County', 'Crop Name'], how='outer')

#%%
usda_crop_id = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\crossover\id.xlsx",sheet_name='bridge bw USDA and landiq', header=1, usecols="G:T")
usda_crop_id['USDA'] = usda_crop_id['USDA'].replace("-", 'No Classification Available')
usda_crop_id['USDA'] = usda_crop_id['USDA'].replace("na", 'Not applicable')
usda_crop_id['USDA'] = usda_crop_id['USDA'].replace(np.nan, 'Unknown Classification')

crops_mapping_dict = usda_crop_id.set_index('CROPTYP2')['USDA'].to_dict()
landiq20_merced['usda_crop_type'] = landiq20_merced.CROPTYP2.map(crops_mapping_dict)
landiq20_merced_crops = landiq20_merced.usda_crop_type.unique()

crops_needed = pd.unique(usda_crop_id.iloc[:,2:].values.ravel('K'))
filtered_df = merged_df[merged_df['Crop Name'].isin(crops_needed)]

#%%
landiq20_merced_usda = landiq20_merced.merge(price_df, left_on=['NAME', 'usda_crop_type'], right_on=['County', 'Crop Name'], how='left')

# landiq20_merced_usda = landiq20_merced_usda.usda_crop_type.unique()
landiq20_merced_crops = landiq20_merced.usda_crop_type.unique()
landiq20_crops = landiq20.CROPTYP2.unique()

#%%
# Plot the map
fig, ax = plt.subplots(figsize=(10, 10))

# Plot the geometries with Price P/U as the color scale
landiq20_merced_usda.plot(column='Price P/U', ax=ax, legend=True,
                          cmap='viridis',  # You can choose any colormap
                          missing_kwds={
                              "color": "lightgrey",
                              "label": "Missing values",
                          })

# Add a title
plt.title('LandIQ20 Merced USDA Data with Price P/U', fontsize=15)

# Show the plot
plt.show()
#%%
from matplotlib.lines import Line2D  # Import for manual legend creation

# Create a custom color mapping
color_map = {
    'No Classification Available': 'red',
    'Not applicable': 'orange',
    'Unknown Classification': 'yellow'
}

# Create a default color for other classifications
default_color = 'lightblue'

# Plotting
fig, ax = plt.subplots(figsize=(10, 10))

# Plot each classification separately
for classification, color in color_map.items():
    subset = landiq20_merced_usda[landiq20_merced_usda['usda_crop_type'] == classification]
    if not subset.empty:
        subset.plot(ax=ax, color=color)

# Plot other classifications
other_subset = landiq20_merced_usda[~landiq20_merced_usda['usda_crop_type'].isin(color_map.keys())]
if not other_subset.empty:
    other_subset.plot(ax=ax, color=default_color)

# Manually create the legend
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='No Classification Available', markerfacecolor='red', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Not applicable', markerfacecolor='orange', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Unknown Classification', markerfacecolor='yellow', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='Classifications Available', markerfacecolor=default_color, markersize=10)
]

# Add the legend to the plot
ax.legend(handles=legend_elements, loc='upper right')

# Add a title
plt.title('LandIQ20 Merced USDA Crop Type Map', fontsize=15)

# Show the plot
plt.show()