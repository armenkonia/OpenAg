# -*- coding: utf-8 -*-
"""
Created on Fri Nov  1 19:04:36 2024

@author: armen
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import os

counties_gdf = gpd.read_file('../Datasets/GIS data/ca_counties/CA_Counties.shp')
hr_gdf = gpd.read_file('../Datasets/GIS data/i03_Hydrologic_Regions/i03_Hydrologic_Regions.shp')
counties_gdf = counties_gdf.to_crs(epsg=3310)
hr_gdf = hr_gdf.to_crs(epsg=3310)

## Mapping each county to its corresponding hydrologic region
# returns dictionary that stores intersection results for each county
county_intersections = {}
for county_name in counties_gdf['NAME']:
    county_geometry = counties_gdf[counties_gdf['NAME'] == county_name]   
    county_hr_intersection = county_geometry.overlay(hr_gdf, how="identity", keep_geom_type=False)
    county_hr_intersection['area_sq_meters'] = county_hr_intersection.geometry.area
    county_intersections[county_name] = county_hr_intersection

# Returns df with the largest HR by area percentage for each county
county_largest_hr_summary = []
for county_name, county_hr_intersections in county_intersections.items():
    # Calculate the total area of the current county
    total_county_area = counties_gdf[counties_gdf['NAME'] == county_name].geometry.area.values[0]
    # Calculate the percent area for each HR within the county
    county_hr_intersections['hr_area_percentage'] = (county_hr_intersections['area_sq_meters'] / total_county_area) * 100
    # Identify the HR with the largest area percentage in the county (Remove the areas not part of any hydrologic region)
    county_hr_intersections_wo_nan = county_hr_intersections.dropna(subset=['HR_NAME'])
    largest_hr_in_county = county_hr_intersections_wo_nan.loc[county_hr_intersections_wo_nan['hr_area_percentage'].idxmax()]
    county_largest_hr_summary.append({
        'County': county_name,
        'HR_NAME': largest_hr_in_county['HR_NAME'],
        'HR Area Percentage': largest_hr_in_county['hr_area_percentage']})
county_largest_hr_df = pd.DataFrame(county_largest_hr_summary)

## add HR info to counties_gdf
counties_gdf = counties_gdf.merge(county_largest_hr_df, left_on='NAME', right_on='County', how='left')

## Identifying the neighboring counties for each county
# Find neighboring counties by checking which geometries touch the current county's geometry
county_neighbors = {}
for idx, county in counties_gdf.iterrows():
    neighbors = counties_gdf[counties_gdf.geometry.touches(county.geometry)]
    county_neighbors[county['County']] = neighbors['County'].tolist()
# add neighboring counties info to counties_gdf
counties_gdf['Neighboring Counties'] = counties_gdf['County'].map(county_neighbors)

## Identifying the neighboring hydrologic regions for each HR
# Find neighboring HR by checking which geometries touch the current HR's geometry
hr_neighbors = {}
for idx, hr in hr_gdf.iterrows():
    neighbors = hr_gdf[hr_gdf.geometry.touches(hr.geometry)]
    hr_neighbors[hr['HR_NAME']] = neighbors['HR_NAME'].tolist()
# add neighboring HR info to hr_gdf
hr_gdf['Neighboring HR'] = hr_gdf['HR_NAME'].map(hr_neighbors)
# add neighboring HR info to counties_gdf
counties_gdf['Neighboring HR'] = counties_gdf['HR_NAME'].map(hr_neighbors)

counties_gdf.to_csv('../Datasets/Output/counties_hr_neighbors.csv')

## plot neighboring counties for each county 
output_folder ='../Datasets/Output/Data Validation/county_neighbor_plots'
os.makedirs(output_folder, exist_ok=True)  

for county in counties_gdf['County'].unique():
    neighbors = county_neighbors.get(county, [])
    county_geom = counties_gdf[counties_gdf['County'] == county]
    neighboring_counties = counties_gdf[counties_gdf['County'].isin(neighbors)]
    
    fig, ax = plt.subplots(figsize=(10, 10))
    hr_gdf.boundary.plot(ax=ax, color='black', linewidth=2, label='Hydrologic Regions')
    county_geom.plot(ax=ax, color='lightblue', edgecolor='black', label=county)
    neighboring_counties.plot(ax=ax, color='orange', edgecolor='black', label='Neighbors')
    
    ax.set_title(f"{county} County and Its Neighbors")
    plt.legend()
    
    plot_path = os.path.join(output_folder, f"{county}_neighbors.png")
    plt.savefig(plot_path, bbox_inches='tight')
    plt.close()


fig, ax = plt.subplots(figsize=(12, 10))
counties_gdf.plot(
    column='HR_NAME',  # Column to color by
    cmap='tab20',      # Colormap (adjust as needed)
    legend=True,       # Add legend
    ax=ax
)
hr_gdf.boundary.plot(ax=ax, color='black', linewidth=2, label='Hydrologic Regions')
ax.set_title("Counties by HR_NAME", fontsize=16)
plt.tight_layout()

# Show the plot
plt.show()