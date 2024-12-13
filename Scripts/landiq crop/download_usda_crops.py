# -*- coding: utf-8 -*-
"""
Created on Thu May  9 11:11:39 2024

@author: armen
"""
import pandas as pd
import matplotlib.pyplot as plt
import pickle

# data_by_year = {}

# for year in range(1981, 2023):
#     urls_to_try = [
#         f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/County_Ag_Commissioner_Report_{year}_data_by_commodity.csv",
#         f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/CAC_{year}_data_by_commodity_20240417.csv",
#         f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/{year}cropyear.csv",
#         f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/1990s/{year}08cactb00.csv",
#         f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/1980s/{year}08cactb00.csv",
#         f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/{year}08cactb00.csv",
#         f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/{year}10cactb00.csv",
#         f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/{year}cactbsErrata.csv",
#         f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/{year}12cactb00.csv",
#         f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/{year}08cropyear.csv",
#         f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/main_data_table.csv"
#     ]
#     data_found = False
#     for url in urls_to_try:
#         try:
#             df = pd.read_csv(url)
#             data_by_year[year] = df
#             print(f"Successfully read data for {year}")

#             data_found = True
#             break  # stop trying URLs if one works
#         except Exception as e:
#             continue  # try next URL if current one fails
    
#     if not data_found:
#         print(f"No data found for {year}")
# # dump dic into pickle
# with open("crop_yield_data.pkl", "wb") as pickle_file:
#     pickle.dump(data_by_year, pickle_file)

with open('../../Datasets/meta_usda_crop_data.pkl', "rb") as pickle_file:
    data_by_year = pickle.load(pickle_file)

## 1981 to 2020 the format of the table is the same, thus we first concat 1981 to 2020 period    
data_by_year_filtered = {year: data_by_year[year] for year in range(1981, 2021)}

#concat all dataframes for all years into a single meta_df
for year, df in data_by_year_filtered.items():
        df.columns = data_by_year_filtered[1981].columns
meta_df = pd.concat(data_by_year_filtered)
meta_df.columns = meta_df.columns.str.strip()
meta_df.reset_index(drop=True, inplace=True)

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

meta_df = pd.concat([meta_df, df_2021, df_2022])
meta_df.reset_index(drop=True, inplace=True)

## preprocessing data (ie: make sure columns are numeric, fix misspeled county names)
# make columns numeric
meta_df['Value'] = pd.to_numeric(meta_df['Value'],errors='coerce')
meta_df['Yield'] = pd.to_numeric(meta_df['Yield'],errors='coerce')
meta_df['Production'] = pd.to_numeric(meta_df['Production'],errors='coerce')
meta_df['Price P/U'] = pd.to_numeric(meta_df['Price P/U'], errors='coerce')
meta_df = meta_df[meta_df['Year'].str.strip().astype(bool)]
meta_df['Year'] = meta_df['Year'].astype('int64')

# remove whitespace (spaces, tabs, newlines, etc.) from both the beginning and end of each string
for column in ['County', 'Crop Name']:
        meta_df[column] = meta_df[column].str.strip()
        
# fix misspeled counties
meta_df = meta_df[~meta_df['County'].isin(['State Total', '', 'State Totals', 'Sum of Others'])]
meta_df['County'] = meta_df['County'].replace('San Luis Obisp', 'San Luis Obispo')
# convert all string values in each column to title case - capitalizes first letter and lower case the rest (ie: 'new york' is converted to 'New York')
meta_df = meta_df.apply(lambda col: col.map(lambda x: x.title() if isinstance(x, str) else x))
meta_df['Crop Name'] = meta_df['Crop Name'].str.replace(',', '')
       
counties = pd.DataFrame(meta_df['County'].unique()) # number of counties should be 58 

# crop_names = pd.DataFrame(meta_df['Crop Name'].unique())

meta_df = meta_df[meta_df.Year >= 2018]
meta_df.to_csv('../../Datasets/Output/usda_crops_18_22.csv')

