# -*- coding: utf-8 -*-
"""
Created on Sat Nov 23 23:36:23 2024

@author: armen
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

usda_crops = pd.read_csv(r"C:/Users/armen/Desktop/COEQWAL/Datasets/Outputs/usda_crops_18_22.csv")
counties_hr = pd.read_csv('C:/Users/armen/Desktop/COEQWAL/Datasets/counties_HR.csv')
usda_crops = pd.merge(usda_crops, counties_hr[['NAME', 'HR_NAME']], left_on='County', right_on='NAME', how='left')

usda_crops = usda_crops.loc[usda_crops.Year == 2020]
usda_crops['Harvested Acres'] = pd.to_numeric(usda_crops['Harvested Acres'],errors='coerce')

tomatoes = usda_crops[usda_crops["Crop Name"].str.contains("tomatoes", case=False, na=False)]
tomatoes = tomatoes.dropna()
tomatoes = tomatoes[~tomatoes['Crop Name'].str.contains("Tomatoes Unspecified", case=False, na=False)]
#%%
df = tomatoes.copy()
# Calculate total harvested acres by county
county_totals = tomatoes.groupby('County')['Harvested Acres'].sum().reset_index()
county_totals = county_totals.rename(columns={'Harvested Acres': 'Total Acres'})

# Merge total acres back to the original DataFrame
df = pd.merge(df, county_totals, on='County')

# Calculate the percentage of processing and fresh market for each county
df['Percentage'] = df['Harvested Acres'] / df['Total Acres']

# Calculate weighted price and weighted yield for each row
df['Weighted Price'] = df['Price P/U'] * df['Percentage']
df['Weighted Yield'] = df['Yield'] * df['Percentage']

# Aggregate by county for weighted values
county_aggregates = df.groupby('County').agg(
    Percentage_Processing=('Percentage', lambda x: x[df['Crop Name'].str.contains("Processing")].sum()),
    Percentage_Fresh=('Percentage', lambda x: x[df['Crop Name'].str.contains("Fresh Market")].sum()),
    Weighted_Price=('Weighted Price', 'sum'),
    Weighted_Yield=('Weighted Yield', 'sum')
).reset_index()


#%%
grapes = usda_crops[usda_crops["Crop Name"].str.contains("grapes", case=False, na=False)]
grapes = grapes.dropna()
grapes = grapes[~grapes['Crop Name'].str.contains("Grapes Raisin", case=False, na=False)]

df = grapes.copy()
# Calculate total harvested acres by county
county_totals = df.groupby('County')['Harvested Acres'].sum().reset_index()
county_totals = county_totals.rename(columns={'Harvested Acres': 'Total Acres'})

# Merge total acres back to the original DataFrame
df = pd.merge(df, county_totals, on='County')

# Calculate the percentage of processing and fresh market for each county
df['Percentage'] = df['Harvested Acres'] / df['Total Acres']

# Calculate weighted price and weighted yield for each row
df['Weighted Price'] = df['Price P/U'] * df['Percentage']
df['Weighted Yield'] = df['Yield'] * df['Percentage']

# Aggregate by county for weighted values
county_aggregates = df.groupby('County').agg(
    Percentage_Table=('Percentage', lambda x: x[df['Crop Name'].str.contains("Table")].sum()),
    Percentage_Wine=('Percentage', lambda x: x[df['Crop Name'].str.contains("Wine")].sum()),
    Weighted_Price=('Weighted Price', 'sum'),
    Weighted_Yield=('Weighted Yield', 'sum')
).reset_index()

