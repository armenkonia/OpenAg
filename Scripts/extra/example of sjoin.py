# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 11:11:58 2024

@author: armen
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import matplotlib.patches as mpatches

# Define the polygons for gdf1
polygon1_gdf1 = Polygon([(1, 1), (5, 1), (5, 5), (1, 5)])

# Define the polygons for gdf2
polygon1_gdf2 = Polygon([(3, 3), (7, 3), (7, 7), (3, 7)])
polygon2_gdf2 = Polygon([(4, 0), (8, 0), (8, 4), (4, 4)])

# Create GeoDataFrames
gdf1 = gpd.GeoDataFrame({'geometry': [polygon1_gdf1]}, crs="EPSG:4326")
gdf2 = gpd.GeoDataFrame({'geometry': [polygon1_gdf2, polygon2_gdf2]}, crs="EPSG:4326")

# Perform spatial join
result = gpd.sjoin(gdf1, gdf2, how="left", predicate="intersects")

# Plotting to visualize
fig, ax = plt.subplots(figsize=(8, 8))
gdf1.plot(ax=ax, color='blue', edgecolor='black', alpha=0.5)
gdf2.plot(ax=ax, color='green', edgecolor='black', alpha=0.5)
result.plot(ax=ax, color='red', edgecolor='black', alpha=0.5)

# Create custom legend handles
gdf1_patch = mpatches.Patch(color='blue', label='gdf1')
gdf2_patch = mpatches.Patch(color='green', label='gdf2')
result_patch = mpatches.Patch(color='red', label='Result of sjoin')

# Add the legend
plt.legend(handles=[gdf1_patch, gdf2_patch, result_patch], loc='upper left', bbox_to_anchor=(1, 1))
plt.show()

#%%
import geopandas as gpd
import matplotlib.pyplot as plt

# Define the polygons for gdf1
polygon1_gdf1 = Polygon([(1, 1), (5, 1), (5, 5), (1, 5)])

# Define the polygons for gdf2
polygon1_gdf2 = Polygon([(3, 3), (7, 3), (7, 7), (3, 7)])
polygon2_gdf2 = Polygon([(4, 0), (8, 0), (8, 4), (4, 4)])

# Create GeoDataFrames
gdf1 = gpd.GeoDataFrame({'geometry': [polygon1_gdf1]}, crs="EPSG:4326")
gdf2 = gpd.GeoDataFrame({'geometry': [polygon1_gdf2, polygon2_gdf2]}, crs="EPSG:4326")

# Perform intersection to cut polygons from gdf1
intersections = gdf1.overlay(gdf2, how='identity')

# Plot the results
fig, ax = plt.subplots(figsize=(8, 8))
gdf1.plot(ax=ax, color='lightblue', edgecolor='black', alpha=0.5, label='gdf1 Polygons')
gdf2.plot(ax=ax, color='orange', edgecolor='black', alpha=0.5, label='gdf2 Polygons')
intersections.plot(ax=ax, color='green', edgecolor='black', alpha=0.7, label='Intersections')

# Add legend and titles
plt.legend()
plt.title('Intersection of gdf1 and gdf2')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show()

