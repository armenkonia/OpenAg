# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 14:56:29 2024

@author: armen
"""

import pandas as pd
import ast
econ_data = pd.read_csv('../../Datasets/Output/processed_usda_crops_20.csv',index_col=0)

def process_and_fill_variable(crop_data, fill_column, categorization_column):
    """
    Processes crop data to calculate and fill missing values for a specific variable (e.g., price or yield)
    hierarchically based on neighboring counties, HRs, and the state average.
    
    Parameters:
        crop_data (pd.DataFrame): DataFrame containing crop data.
        fill_column (str): Column name for the variable data (e.g., 'price_2020' or 'yield_2020').
        
    Returns:
        pd.DataFrame: Updated crop data with filled variable values and source tracking.
        pd.Series: Percentage of acres associated with each source.
    """
    
    # 1. Calculate average value for neighboring counties
    expanded_crop_data = crop_data.explode('Neighboring Counties')
    merged_crop_data = pd.merge(expanded_crop_data, crop_data[[categorization_column, 'County', fill_column]],
                                left_on=['Neighboring Counties', categorization_column], right_on=['County', categorization_column],
                                suffixes=('', '_neighbor'),how='left')
    avg_neighbor_values = merged_crop_data.groupby([categorization_column, 'County'])[f'{fill_column}_neighbor'].mean()
    avg_neighbor_values_dict = avg_neighbor_values.to_dict()
    crop_data[f'neighboring_county_avg_{fill_column}'] = crop_data.set_index([categorization_column, 'County']).index.map(avg_neighbor_values_dict)

    # 2. Calculate average value for each crop in HRs
    hr_avg_values = crop_data.groupby([categorization_column, 'HR_NAME'])[fill_column].mean()
    hr_avg_values_dict = hr_avg_values.to_dict()
    crop_data[f'hr_avg_{fill_column}'] = crop_data.set_index([categorization_column, 'HR_NAME']).index.map(hr_avg_values_dict)

    # 3. Calculate average value for neighboring HRs
    counties_hr = pd.read_csv('../../Datasets/Output/counties_hr_neighbors.csv')
    hr_avg_values_df = pd.DataFrame(hr_avg_values).reset_index()
    hr_avg_values_with_neighbors = hr_avg_values_df.merge(counties_hr[['HR_NAME', 'Neighboring HR']],how='left',on='HR_NAME').drop_duplicates()
    hr_avg_values_with_neighbors['Neighboring HR'] = hr_avg_values_with_neighbors['Neighboring HR'].apply(ast.literal_eval)
    expanded_hr_avg_values = hr_avg_values_with_neighbors.explode('Neighboring HR')
    hr_avg_values_with_neighbor_values = expanded_hr_avg_values.merge(
        hr_avg_values_df[[categorization_column, 'HR_NAME', fill_column]],
        how='left',
        left_on=[categorization_column, 'Neighboring HR'],
        right_on=[categorization_column, 'HR_NAME']
    ).drop(columns=['HR_NAME_y']).rename(columns={
        'HR_NAME_x': 'HR_NAME',
        f'{fill_column}_x': f'base_hr_{fill_column}',
        f'{fill_column}_y': f'neighbor_hr_{fill_column}'
    })
    mean_neighbor_hr_values = hr_avg_values_with_neighbor_values.groupby([categorization_column, 'HR_NAME'])[f'neighbor_hr_{fill_column}'].mean()
    mean_neighbor_hr_values_dict = mean_neighbor_hr_values.to_dict()
    crop_data[f'neighboring_hr_avg_{fill_column}'] = crop_data.set_index([categorization_column, 'HR_NAME']).index.map(mean_neighbor_hr_values_dict)

    # 4. Calculate average value for each crop across the state
    avg_state_values = crop_data.groupby(categorization_column)[fill_column].mean()
    crop_data[f'state_avg_{fill_column}'] = crop_data[categorization_column].map(avg_state_values)

    # 5. Fill missing values hierarchically
    def fill_variable(row):
        if pd.notna(row[fill_column]):
            return row[fill_column], fill_column
        elif pd.notna(row[f'neighboring_county_avg_{fill_column}']):
            return row[f'neighboring_county_avg_{fill_column}'], f'neighboring_county_avg_{fill_column}'
        elif pd.notna(row[f'hr_avg_{fill_column}']):
            return row[f'hr_avg_{fill_column}'], f'hr_avg_{fill_column}'
        else:
            return row[f'state_avg_{fill_column}'], f'state_avg_{fill_column}'

    crop_data[[f'final_{fill_column}', f'{fill_column}_source']] = crop_data.apply(
        lambda row: pd.Series(fill_variable(row)), axis=1)
    
    columns_to_drop = [f'neighboring_county_avg_{fill_column}', 
                      f'hr_avg_{fill_column}', 
                      f'neighboring_hr_avg_{fill_column}', 
                      f'state_avg_{fill_column}',
                      f'{fill_column}_source']
    crop_data = crop_data.drop(columns=columns_to_drop)
   
    return crop_data

columns_to_fill = ['price_avg', 'production_avg', 'acres_avg', 'yield_avg', 'fraction']
categorization_column = 'Crop_Subtype'
for sel_variable in columns_to_fill:
    econ_data = process_and_fill_variable(econ_data, sel_variable, categorization_column)

econ_data = econ_data[['Crop_OpenAg','Crop_Subtype', 'County', 'HR_NAME', 'final_price_avg','final_yield_avg','final_acres_avg','final_fraction']]
econ_data.set_index(['Crop_OpenAg', 'County', 'HR_NAME'], inplace=True)
econ_data.columns = econ_data.columns.str.replace('final_', '', regex=True)
econ_data.to_csv('../../Datasets/Output/filled_crop_economic_data.csv')

# =============================================================================
# to check if the percentages are right 
# =============================================================================
pivot_table = econ_data.pivot_table(index='County', columns='Crop_Subtype', values='fraction', aggfunc='first')
pivot_table['sum'] = pivot_table.sum(axis=1)
