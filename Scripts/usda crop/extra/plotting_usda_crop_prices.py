# -*- coding: utf-8 -*-
"""
Created on Tue May 28 11:00:47 2024

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
# meta_df = meta_df[meta_df.Year >= 2007]

meta_df['HR'] = meta_df['County'].apply(lambda county: 'Sacramento Region' if county in sacramento_valley_counties else 'San Joaquin Region')
meta_df = meta_df.sort_values(by=['Year', 'Crop Name', 'County', 'HR'])
#%%
annual_avg_county = meta_df.groupby(['Year', 'County'])[['Price P/U', 'Yield']].mean().reset_index()
annual_avg = meta_df.groupby(['Year'])[['Price P/U', 'Yield']].mean().reset_index()
annual_avg = annual_avg.set_index('Year')
annual_avg[['Price P/U']].plot()
pivot_price = meta_df.pivot_table(values='Price P/U', index='County', columns='Year', aggfunc='mean')
pivot_yield = meta_df.pivot_table(values='Yield', index='County', columns='Year', aggfunc='mean')

#%%
# Assuming pivot_price has years as columns, calculate percentage change between two specific years (e.g., 2023 and 2022)
price_change = (pivot_price[2022] - pivot_price[2018]) / pivot_price[2018] * 100
price_change = price_change.reset_index()
price_change.columns = ['County', 'Price Increase']

counties_gdf = gpd.read_file(r"C:\Users\armen\Desktop\COEQWAL\ca_counties\CA_Counties.shp")
# Ensure 'County' names in your data match the shapefile 'County' names (e.g., standardize case, remove spaces)
counties_gdf['NAME'] = counties_gdf['NAME'].str.strip().str.title()
counties_gdf = counties_gdf.rename(columns={'NAME': 'County'}) 
counties_gdf = counties_gdf[['County', 'Shape_Leng', 'Shape_Area','geometry']]
merged_gdf = counties_gdf.merge(price_change, on='County', how='left')
# merged_gdf = price_change.merge(counties_gdf, on='County', how='left')
# merged_gdf = gpd.GeoDataFrame(merged_gdf)

#%%
fig, ax = plt.subplots(1, 1, figsize=(10, 10))
merged_gdf.plot(column='Price Increase', cmap='OrRd', linewidth=0.8, ax=ax, edgecolor='0.8', legend=True)
for idx, row in merged_gdf.iterrows():
    centroid = row['geometry'].centroid
    ax.text(centroid.x, centroid.y, row['County'], fontsize=8, ha='center', color='black')
ax.set_title('Price Increase by County', fontsize=15)
counties_gdf.boundary.plot(ax=ax, linewidth=1, color='black')

plt.show()

#%%
df_yearly_change = pivot_price.diff(axis=1)
df_wrt_2018 = pivot_price.sub(pivot_price[2018], axis=0)

#%%
# Plot settings
fig, axs = plt.subplots(3, 1, figsize=(10, 8))

# Plot year-to-year price change
pivot_price.T.plot(ax=axs[0], marker='o', legend=False)
axs[0].set_title('Year-to-Year Price')
axs[0].set_ylabel('Price')
# axs[0].legend(title="County", loc='upper right')
axs[0].grid(True)

# Plot year-to-year price change
df_yearly_change.T.plot(ax=axs[1], marker='o', legend=False)
axs[1].set_title('Year-to-Year Price Change')
axs[1].set_ylabel('Price Change')
# axs[1].legend(title="County", loc='upper right')
axs[1].grid(True)

# Plot price change with respect to 2018
df_wrt_2018.T.plot(ax=axs[2], marker='o', legend=False)
axs[2].set_title('Price Change with Respect to 2018')
axs[2].set_ylabel('Price Change from 2007')
# axs[2].legend(title="County", loc='upper right')
axs[2].grid(True)

lines, labels = axs[0].get_legend_handles_labels()
fig.legend(lines, labels, title="County", bbox_to_anchor=(1, 0.5), loc='center right')

plt.tight_layout()
plt.subplots_adjust(right=0.8)  
plt.show()