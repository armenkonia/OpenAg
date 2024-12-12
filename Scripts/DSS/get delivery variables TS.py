# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 21:29:17 2024

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
#%%
del_vars = df[['Delivery_Variable']].iloc[0:,:]
del_vars_duplicates = del_vars[del_vars.duplicated(keep=False)]
# demand_units = df[['Demand Unit']].iloc[0:,:]
del_vars = del_vars.drop_duplicates()
del_vars = del_vars.drop_duplicates().dropna()

# del_vars = del_vars['Delivery_Variable']
del_vars_split = del_vars['Delivery_Variable'].str.split(';', expand=True)
del_vars_split = del_vars['Delivery_Variable'].str.split(r'[;|+]', expand=True)
del_vars_separated = del_vars_split.stack().str.strip().reset_index(drop=True)

#%%
result_dict = {}
for del_var in del_vars:
    del_var = str(del_var)
    filtered_df = catdf[
        (catdf['B'] == del_var)  # Exact match with del_var
        # (catdf['B'].str.contains(del_var, na=False))
        # & (catdf['C'] == 'DIVERSION')
    ]    
    result_dict[del_var] = filtered_df
    
#%%
del_vars = df[['Demand Unit','Delivery_Variable']].iloc[0:,:]
del_vars[['Delivery_Variable_1', 'Delivery_Variable_2']] = del_vars['Delivery_Variable'].str.split(r'[;|+]', expand=True)
del_vars['Delivery_Variable_1'] = del_vars['Delivery_Variable_1'].str.strip()
del_vars['Delivery_Variable_2'] = del_vars['Delivery_Variable_2'].str.strip()

#%%
stacked_df = del_vars.melt(id_vars=['Demand Unit'], value_vars=['Delivery_Variable_1', 'Delivery_Variable_2'],
                     var_name='Delivery_Variable_Type', value_name='Delivery_Variable_new').dropna()
merged_df = pd.merge(stacked_df, del_vars[['Demand Unit', 'Delivery_Variable']], on='Demand Unit', how='left')
#%%
result_dict = {}
for del_var in del_vars:
    del_var = str(del_var)
    filtered_df = catdf[
        (catdf['B'] == del_var)  # Exact match with del_var
        # (catdf['B'].str.contains(del_var, na=False))
        # & (catdf['C'] == 'DIVERSION')
    ]    
    result_dict[del_var] = filtered_df
    
#%%
time_series_dict = {}
for key, df_row in result_dict.items():
    if not df_row.empty:  # Check if the row is not empty
        df_row = df_row.iloc[0]
        pathname = build_dss_path(df_row)         
        df, units2, ptype2 = d.read_rts(pathname)
        time_series_dict[key]  = df
        # print(type(df))
a = time_series_dict.values()
combined_df = pd.concat(time_series_dict.values(), axis=1)
combined_df.columns = list(time_series_dict.keys())
    
combined_df = combined_df.reset_index()
combined_df = pd.melt(combined_df, id_vars=['index'], 
                  var_name='Delivery Variable', 
                  value_name='Deliveries')
#add whether deliveries are gw or surface water

combined_df_head = combined_df.head()
combined_df.to_csv('delivery_variables.csv')
