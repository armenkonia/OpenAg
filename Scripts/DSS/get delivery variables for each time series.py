# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 23:40:21 2024

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
del_vars = del_vars['Delivery_Variable'].str.split(r'[;|+]', expand=True)
del_vars = del_vars.stack().str.strip().reset_index(drop=True)

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

stacked_df = del_vars.melt(id_vars=['Demand Unit'], value_vars=['Delivery_Variable_1', 'Delivery_Variable_2'],
                     var_name='Delivery_Variable_Type', value_name='Delivery_Variable_new').dropna()
df = pd.merge(stacked_df, del_vars[['Demand Unit', 'Delivery_Variable']], on='Demand Unit', how='left')
# df.to_csv('demand_unit_with_delivery_variables.csv')
