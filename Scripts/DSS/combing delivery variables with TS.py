# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 00:31:05 2024

@author: armen
"""
import pandas as pd
del_vars = pd.read_csv('delivery_variables.csv')
du_del_var = pd.read_csv('demand_unit_with_delivery_variables.csv')

#%%

df_grouped = du_del_var.groupby('Demand Unit')['Delivery_Variable_new'].apply(lambda x: ', '.join(set(x))).reset_index()
#%%
# Initialize an empty dictionary to store DataFrames
df_dict = {}

# Filter for '06_NA' Demand Unit
filtered_df = du_del_var[du_del_var['Demand Unit'] == '06_NA']

# Loop through unique 'Delivery_Variable_new' values for '06_NA'
for i in filtered_df['Delivery_Variable_new']:
    # Filter DataFrame for each Delivery Variable in del_vars
    df = del_vars.loc[del_vars['Delivery Variable'] == i]
    
    # Store the filtered DataFrame in the dictionary with key as the delivery variable
    df_dict[i] = df

# Now df_dict will have 'Delivery_Variable_new' as keys and corresponding DataFrames as values


#%%
# Initialize an empty dictionary to store DataFrames for each Demand Unit
all_df_dict = {}

# Loop through unique 'Demand Unit' values
for du in du_del_var['Demand Unit'].unique():
    # Initialize a dictionary for each Demand Unit
    df_dict = {}
    
    # Filter for the current Demand Unit
    filtered_df = du_del_var[du_del_var['Demand Unit'] == du]
    
    # Loop through unique 'Delivery_Variable_new' values for the current Demand Unit
    for i in filtered_df['Delivery_Variable_new']:
        # Filter DataFrame for each Delivery Variable in del_vars
        df = del_vars.loc[del_vars['Delivery Variable'] == i]
        
        # Store the filtered DataFrame in the dictionary with key as the delivery variable
        df_dict[i] = df
    
    # Store the dictionary for the current Demand Unit in the outer dictionary
    all_df_dict[du] = df_dict


#%%
# Initialize a new dictionary to store merged DataFrames
merged_df_dict = {}

# Iterate through each Demand Unit in all_df_dict
for du, df_dict in all_df_dict.items():
    # Check if there is more than one DataFrame for the current Demand Unit
    if len(df_dict) > 1:
        # Start with the first DataFrame
        merged_df = next(iter(df_dict.values()))
        
        # Merge the remaining DataFrames based on the 'index' column
        for df in list(df_dict.values())[1:]:
            merged_df = merged_df.merge(df, on='index', how='outer')  # Use outer join to keep all data
            merged_df['Deliveries'] = merged_df['Deliveries_x'] + merged_df['Deliveries_y']
        
        # Store the merged DataFrame in the new dictionary
        merged_df_dict[du] = merged_df
    elif len(df_dict) == 1:
        # If there is only one DataFrame, keep it as is
        merged_df_dict[du] = next(iter(df_dict.values()))
        
