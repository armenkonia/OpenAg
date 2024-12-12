# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 17:44:49 2024

@author: armen
"""
import pickle 
import pandas as pd
import matplotlib.pyplot as plt
import os
import geopandas as gpd
import numpy as np
import ast

# extract proxy crop within each HR
with open('../../Datasets/econ_crop_data/hr_crop_analysis_results.pkl', 'rb') as f:
    hr_crop_analysis_results_dict = pickle.load(f)

meta_crops_info_by_hr = {}
all_proxy_crops_hr_dfs = []
for hr_name, result in hr_crop_analysis_results_dict.items():
    meta_crops_info_by_hr[hr_name] = result['agg_crops']
    # Extract proxy crop DataFrame, add hydrologic region name, and append to list
    proxy_crops_hr_df = result['proxy crop']
    proxy_crops_hr_df['HR_NAME'] = hr_name
    all_proxy_crops_hr_dfs.append(proxy_crops_hr_df)

proxy_crops_hr_df = pd.concat(all_proxy_crops_hr_dfs, ignore_index=True)
proxy_crops_hr_df['Crop_OpenAg'] = proxy_crops_hr_df['Crop_OpenAg'].str.replace('^WA_', '', regex=True)


# only keep 2020 econ data of proxy crops in each county in landiq
usda_crops = pd.read_csv('../../Datasets/econ_crop_data/processed_usda_crops_18_22.csv', index_col=0)
landiq_openag_crops = pd.read_csv('../../Datasets/econ_crop_data/landiq_openag_crops_county_area.csv', index_col=0)

usda_crops = usda_crops[['Crop Name', 'County', 'HR_NAME', 'Neighboring Counties', 'Neighboring HR', 'price_2020','Production_2020','Acres_2020', 'yield_2020']]
usda_crops['County'] = usda_crops['County'].str.title()
usda_crops = usda_crops.merge(proxy_crops_hr_df, how='outer', on=['Crop Name', 'HR_NAME'])
# usda_crops = usda_crops.dropna(subset=['Crop_OpenAg'])
usda_crops['economic_data_availability'] = np.where(usda_crops['price_2020'].isna(), 'N', 'Y')

usda_crops = landiq_openag_crops.merge(usda_crops[['Crop Name', 'Crop_OpenAg', 'County', 'price_2020', 'yield_2020']], 
                                       on=['Crop_OpenAg', 'County'], how='left')
usda_crops = usda_crops.rename(columns={'Crop Name': 'usda crop'})

# convert str into a python list
usda_crops['Neighboring Counties'] = usda_crops['Neighboring Counties'].apply(ast.literal_eval)
usda_crops_updated = usda_crops.copy()

def process_crop(crop_name, usda_crops):
    # Filter the crop and remove unwanted rows
    crop_data = usda_crops[usda_crops["Crop Name"].str.contains(crop_name, case=False, na=False)]
    crop_data = crop_data.dropna()
    crop_data = crop_data[~crop_data['Crop Name'].str.contains(f"{crop_name} Unspecified", case=False, na=False)]

    # Calculate total harvested acres by county
    county_totals = crop_data.groupby('County')['Acres_2020'].sum().reset_index()
    county_totals = county_totals.rename(columns={'Acres_2020': 'Total Acres'})
    crop_data = pd.merge(crop_data, county_totals, on='County')

    # Calculate the percentage of each crop and weighted price/yield
    crop_data['Percentage'] = crop_data['Acres_2020'] / crop_data['Total Acres']
    crop_data['Weighted Price'] = crop_data['price_2020'] * crop_data['Percentage']
    crop_data['Weighted Yield'] = crop_data['yield_2020'] * crop_data['Percentage']

    # Aggregate by county for weighted values
    county_aggregates = crop_data.groupby('County').agg(
        Percentage_Processing=('Percentage', lambda x: x[crop_data['Crop Name'].str.contains("Processing")].sum()),
        Percentage_Fresh=('Percentage', lambda x: x[crop_data['Crop Name'].str.contains("Fresh Market")].sum()),
        Weighted_Price=('Weighted Price', 'sum'),
        Weighted_Yield=('Weighted Yield', 'sum')
    ).reset_index()

    # Rename columns and add crop type
    county_aggregates = county_aggregates.rename(columns={'Weighted_Price': 'price_2020', 'Weighted_Yield': 'yield_2020'})
    county_aggregates['Crop_OpenAg'] = crop_name.capitalize()

    return county_aggregates

usda_crops = pd.read_csv('../../Datasets/econ_crop_data/processed_usda_crops_18_22.csv')
usda_crops['County'] = usda_crops['County'].str.title()

# Process tomatoes and grapes
tomatoes_aggregates = process_crop("tomatoes", usda_crops)
grapes_aggregates = process_crop("grapes", usda_crops)

# Merge with the main dataset
usda_crops_updated = usda_crops_updated.merge(tomatoes_aggregates[["County", "Crop_OpenAg", "price_2020", "yield_2020"]],
                                              on=["County", "Crop_OpenAg"], how="left", suffixes=("", "_new"))

usda_crops_updated.loc[usda_crops_updated["Crop_OpenAg"] == "Tomatoes", "price_2020"] = usda_crops_updated["price_2020_new"]
usda_crops_updated.loc[usda_crops_updated["Crop_OpenAg"] == "Tomatoes", "yield_2020"] = usda_crops_updated["yield_2020_new"]
usda_crops_updated.drop(["price_2020_new", "yield_2020_new"], axis=1, inplace=True)

usda_crops_updated = usda_crops_updated.merge(grapes_aggregates[["County", "Crop_OpenAg", "price_2020", "yield_2020"]],
                                              on=["County", "Crop_OpenAg"], how="left", suffixes=("", "_new"))
usda_crops_updated.loc[usda_crops_updated["Crop_OpenAg"] == "Grapes", "price_2020"] = usda_crops_updated["price_2020_new"]
usda_crops_updated.loc[usda_crops_updated["Crop_OpenAg"] == "Grapes", "yield_2020"] = usda_crops_updated["yield_2020_new"]
usda_crops_updated.drop(["price_2020_new", "yield_2020_new"], axis=1, inplace=True)


usda_crops_updated.to_csv(r"C:\Users\armen\Desktop\COEQWAL\Scripts\landiq crop\proxy crop finder\crops_county.csv")
