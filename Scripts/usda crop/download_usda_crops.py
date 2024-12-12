# -*- coding: utf-8 -*-
"""
Created on Thu May  9 11:11:39 2024

@author: armen
"""
import pandas as pd
import matplotlib.pyplot as plt
import pickle

# Initialize an empty dictionary to store the dataframes
data_by_year = {}

# Loop over the years from 1981 to 2022
for year in range(1981, 2023):
    urls_to_try = [
        f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/County_Ag_Commissioner_Report_{year}_data_by_commodity.csv",
        f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/CAC_{year}_data_by_commodity_20240417.csv",
        f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/{year}cropyear.csv",
        f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/1990s/{year}08cactb00.csv",
        f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/1980s/{year}08cactb00.csv",
        f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/{year}08cactb00.csv",
        f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/{year}10cactb00.csv",
        f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/{year}cactbsErrata.csv",
        f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/{year}12cactb00.csv",
        f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/{year}08cropyear.csv",
        f"https://www.nass.usda.gov/Statistics_by_State/California/Publications/AgComm/{year}/main_data_table.csv"
    ]
    data_found = False
    for url in urls_to_try:
        try:
            df = pd.read_csv(url)
            data_by_year[year] = df
            # print(f"Successfully read data for {year} from: {url}")
            print(f"Successfully read data for {year}")

            data_found = True
            break  # Stop trying URLs if one works
        except Exception as e:
            continue  # Try next URL if current one fails
    
    if not data_found:
        print(f"No data found for {year}")

with open("crop_yield_data.pkl", "wb") as pickle_file:
    pickle.dump(data_by_year, pickle_file)
#%%
data_by_year_filtered = {year: data_by_year[year] for year in range(1981, 2021)}
# df_merged = pd.concat(data_by_year[])

#%%
#concat all dataframes for all years into a single metadf
for year, df in data_by_year_filtered.items():
        df.columns = data_by_year_filtered[1981].columns
df_merged = pd.concat(data_by_year_filtered)
df_merged.columns = df_merged.columns.str.strip()
#%%
df = data_by_year[2022].copy()
df = df.drop(['Current Item Name','Current Item Code','Row Type Id','Commodities In Group', 'Footnote'],axis=1)
df = df.rename(columns={'Legacy Item Name': 'Crop Name', 'Legacy Commodity Code': 'Commodity Code', 'Price Per Unit': 'Price P/U'})
df = df[['Year', 'Commodity Code', 'Crop Name', 'County Code', 'County','Harvested Acres', 'Yield', 'Production', 'Price P/U', 'Unit', 'Value']]

df_merged = pd.concat([df_merged,df])

#%%
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
meta_df = df_merged.copy()
meta_df['Value'] = pd.to_numeric(meta_df['Value'],errors='coerce')
meta_df['Yield'] = pd.to_numeric(meta_df['Yield'],errors='coerce')
meta_df['Year'] = pd.to_numeric(meta_df['Year'],errors='coerce')
meta_df['Year'] = pd.to_datetime(meta_df['Year'], format='%Y',errors='coerce')
for column in ['County', 'Crop Name']:
        meta_df[column] = meta_df[column].str.strip()
# counties = pd.DataFrame(data_by_year_filtered[1981][' County'].unique())
meta_df = meta_df[~meta_df['County'].isin(['State Total', '', 'State Totals', 'Sum of Others'])]
meta_df['County'] = meta_df['County'].replace('San Luis Obisp', 'San Luis Obispo')
counties = pd.DataFrame(meta_df['County'].unique())
crop_types = pd.DataFrame(meta_df['Crop Name'].unique())

meta_df = meta_df.apply(lambda col: col.map(lambda x: x.capitalize() if isinstance(x, str) else x))
meta_df['Crop Name'] = meta_df['Crop Name'].str.replace(',', '')
#%%
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
counties = pd.DataFrame(meta_df['County'].unique())

#%%
grouped_sum = meta_df.groupby(['Year', 'Crop Name', 'County']).sum()
grouped_sum = grouped_sum.reset_index()
almonds_df = grouped_sum[grouped_sum['Crop Name'] == 'Almonds all']

# Loop over unique counties
for county in almonds_df['County'].unique():
    county_data = almonds_df[almonds_df['County'] == county]
    plt.plot(county_data['Year'], county_data['Value'], label=county)

plt.xlabel('Year')
plt.ylabel('Yield')
plt.title('Yield Over Time for Different Counties')
plt.legend()
plt.show() 

#%%
grouped_mean = meta_df.groupby(['Year', 'Crop Name', 'County'])[['Yield', 'Value']].mean()
grouped_mean = grouped_mean.reset_index()
# grouped_mean = grouped_mean[['Year','Crop Name','Yield','Value']]
almonds_df = grouped_mean[grouped_mean['Crop Name'] == 'Almonds all']

plt.plot(almonds_df['Year'], almonds_df['Yield'])  # Replace 'YourOtherColumn' with the actual column you want to plot
#%%
# Loop over unique counties
for county in almonds_df['County'].unique():
    county_data = almonds_df[almonds_df['County'] == county]
    plt.plot(county_data['Year'], county_data['Yield'], label=county)

plt.xlabel('Year')
plt.ylabel('Yield')
plt.title('Yield Over Time for Different Counties')
plt.legend()
plt.show()

#%%