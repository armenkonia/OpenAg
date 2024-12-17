# -*- coding: utf-8 -*-
"""
Created on Sat Nov 23 21:20:39 2024

@author: armen
"""

import geopandas as gpd
import matplotlib.pyplot as plt

landiq_only = gpd.read_file(r"C:/Users/armen/Desktop/COEQWAL/Datasets/GIS data/i15_crop_mapping_2020/i15_Crop_Mapping_2020.shp")

counties_gdf = gpd.read_file(r"C:\Users\armen\Desktop\COEQWAL\Datasets\GIS data\ca_counties\CA_Counties.shp")

counties_gdf = counties_gdf.to_crs(3310)
landiq_only = landiq_only.to_crs(3310)
#%%
# Assuming 'landiq_only' and 'counties_gdf' are GeoDataFrames
fig, ax = plt.subplots(1, 1, figsize=(12, 10))

# Plot counties_gdf (county boundaries) as the base layer
counties_gdf.boundary.plot(ax=ax, color="black", linewidth=1, label="County Boundaries")

# Plot landiq_only with colors based on 'COUNTY'
landiq_only.plot(column='COUNTY', ax=ax, cmap='tab20')

plt.tight_layout()
plt.savefig('validating landiq county boundaries.png', dpi=2400, bbox_inches='tight', format='png')  # 'pdf' or 'svg' for vector graphics
plt.show()