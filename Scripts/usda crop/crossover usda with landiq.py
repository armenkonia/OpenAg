# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 21:43:16 2024

@author: armen
"""

import pandas as pd
import matplotlib.pyplot as plt
import pickle
import geopandas as gpd
import matplotlib.pyplot as plt

with open("USDA_ag.pkl", "rb") as pickle_file:
    data_by_year = pickle.load(pickle_file)

#%%
#1981 to 2020 the format of the table is the same, thus we first concat 1981 to 2020 period    
data_by_year_filtered = {year: data_by_year[year] for year in range(1981, 2021)}

#concat all dataframes for all years into a single metadf
for year, df in data_by_year_filtered.items():
        df.columns = data_by_year_filtered[1981].columns
df_merged = pd.concat(data_by_year_filtered)
df_merged.columns = df_merged.columns.str.strip()
df_merged.reset_index(drop=True, inplace=True)

# 2021 and 2022 new columns have been added and thus we modify it to match the previous format
def process_year_data(df):
    df = df.drop(['Current Item Name', 'Current Item Code', 'Row Type Id', 'Commodities In Group', 'Footnote'], axis=1)
    df = df.rename(columns={'Legacy Item Name': 'Crop Name', 'Legacy Commodity Code': 'Commodity Code', 'Price Per Unit': 'Price P/U'})
    df = df[['Year', 'Commodity Code', 'Crop Name', 'County Code', 'County', 'Harvested Acres', 'Yield', 'Production', 'Price P/U', 'Unit', 'Value']]
    return df

df_2021 = data_by_year[2021].copy()
df_2021 = process_year_data(df_2021)
df_2022 = data_by_year[2022].copy()
df_2022 = process_year_data(df_2022)

df_merged = pd.concat([df_merged, df_2021, df_2022])
df_merged.reset_index(drop=True, inplace=True)
#%%
# make columns numeric
meta_df = df_merged.copy()
meta_df['Value'] = pd.to_numeric(meta_df['Value'],errors='coerce')
meta_df['Yield'] = pd.to_numeric(meta_df['Yield'],errors='coerce')
# meta_df['Year'] = pd.to_numeric(meta_df['Year'],errors='coerce')
meta_df['Price P/U'] = pd.to_numeric(meta_df['Price P/U'], errors='coerce')
meta_df = meta_df[meta_df['Year'].str.strip().astype(bool)]
meta_df['Year'] = meta_df['Year'].astype('int64')
# meta_df['Year'] = pd.to_datetime(meta_df['Year'], format='%Y',errors='coerce')

# remove whitespace (spaces, tabs, newlines, etc.) from both the beginning and end of each string
for column in ['County', 'Crop Name']:
        meta_df[column] = meta_df[column].str.strip()
        
# fix misspeled counties and crop names
meta_df = meta_df[~meta_df['County'].isin(['State Total', '', 'State Totals', 'Sum of Others'])]
meta_df['County'] = meta_df['County'].replace('San Luis Obisp', 'San Luis Obispo')

meta_df = meta_df.apply(lambda col: col.map(lambda x: x.title() if isinstance(x, str) else x))
meta_df['Crop Name'] = meta_df['Crop Name'].str.replace(',', '')

# check  number of counties should be 58        
counties = pd.DataFrame(meta_df['County'].unique())
crop_names = pd.DataFrame(meta_df['Crop Name'].unique())

# filter based on county 
sacramento_valley_counties = [
    "Butte", "Colusa", "Glenn", "Placer", 
    "Sacramento", "Shasta", "Sutter", 
    "Tehama", "Yolo", "Yuba"]
san_joaquin_valley_counties = [
    "Fresno", "Kern", "Kings", "Madera", 
    "Merced", "San Joaquin", "Stanislaus", 
    "Tulare"]
central_ca_counties = sacramento_valley_counties + san_joaquin_valley_counties
meta_df = meta_df[meta_df['County'].isin(central_ca_counties)]

#%%
# meta_df = meta_df[['Year', 'Crop Name','County','Harvested Acres', 'Yield', 'Production', 'Price P/U', 'Unit', 'Value']]
meta_df = meta_df[['Year', 'Crop Name','County', 'Price P/U', 'Yield']]
meta_df = meta_df[meta_df.Year >= 2018]
meta_df_crops = meta_df['Crop Name'].unique()
meta_df.to_csv('usda_crops_18_22.csv')
#%%

crop_id = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\crossover\bridge_landiq_openag_crops_all_years_01102024.xlsx",sheet_name='2020_updated')
ppic_mapping_dict = crop_id.set_index('CROPTYP2')['Crop_OpenAg'].to_dict()

