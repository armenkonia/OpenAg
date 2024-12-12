# -*- coding: utf-8 -*-
"""
Created on Sat Oct 12 15:39:30 2024

@author: armen
"""

import pyhecdss
import pandas as pd

fname=r"C:\Users\armen\Desktop\COEQWAL\Datasets\s0002_DCR2023_9.3.1_danube_adj-20241012T184038Z-001\s0002_DCR2023_9.3.1_danube_adj\Model_Files\9.3.1_danube_adj\9.3.1_danube_adj\DSS\output\DCR2023_DV_9.3.1_v2a_Danube_Adj_v1.8_new.dss"

with pyhecdss.DSSFile(fname) as d:
    catdf=d.read_catalog()
catdf.F.unique()

def build_dss_path(row):
    return f"/{row['A']}/{row['B']}/{row['C']}/{row['D']}/{row['E']}/{row['F']}/"
#%%
first_row = catdf.iloc[0]  
pathname = build_dss_path(first_row)
df, units2, ptype2 = d.read_rts(pathname)
result = catdf[catdf['B'].str.contains('AW_02_NA', na=False)]

#%%
df = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\calsim\cs3rpt2022_all_demand_units_v20241003.xlsx", sheet_name='all_demand_units', header=1)
df = df[df['Unit Type (Ag, MI, Refuge/Wetland)'] == 'AG']
demand_units = df[['Delivery_Variable']].iloc[0:,:]
demand_units = demand_units.drop_duplicates().dropna()
demand_units = demand_units['Delivery_Variable']
#%%
result_dict = {}
for demand_unit in demand_units:
    demand_unit = str(demand_unit)
    filtered_df = catdf[
        (catdf['B'].str.contains(demand_unit, na=False))
        #  & (catdf['C'] == 'DIVERSION')
    ]    
    result_dict[demand_unit] = filtered_df

#%%
time_series_dict = {}
for key, df_row in result_dict.items():
    if not df_row.empty:  # Check if the row is not empty
        df_row = df_row.iloc[0]
        pathname = build_dss_path(df_row)         
        df, units2, ptype2 = d.read_rts(pathname)
        time_series_dict[key]  = df
        # print(type(df))
combined_df = pd.concat(time_series_dict.values())
combined_df.columns = list(time_series_dict.keys())
    
combined_df = combined_df.reset_index()
combined_df = pd.melt(combined_df, id_vars=['index'], 
                  var_name='Demand Unit', 
                  value_name='Deliveries')
#add whether deliveries are gw or surface water
        #%%
first_key, first_value = next(iter(result_dict.items()))
pathname = build_dss_path(first_row)
df, units2, ptype2 = d.read_rts(pathname)
