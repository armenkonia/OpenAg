# -*- coding: utf-8 -*-
"""
Created on Sun Dec  1 12:12:26 2024

@author: armen
"""
import pandas as pd
import ast

merged_aggregates = pd.read_csv(r"C:\Users\armen\Desktop\OpenAg\Scripts\landiq crop\exc_crops.csv",index_col=0)
merged_aggregates['Neighboring Counties'] = merged_aggregates['Neighboring Counties'].apply(ast.literal_eval)
merged_aggregates['Neighboring HR'] = merged_aggregates['Neighboring HR'].apply(ast.literal_eval)
merged_aggregates = merged_aggregates.rename(columns={'Acres': 'ACRES'})

def process_and_fill_variable(crop_data, variable_column):
    """
    Processes crop data to calculate and fill missing values for a specific variable (e.g., price or yield)
    hierarchically based on neighboring counties, HRs, and the state average.
    
    Parameters:
        crop_data (pd.DataFrame): DataFrame containing crop data.
        variable_column (str): Column name for the variable data (e.g., 'price_2020' or 'yield_2020').
        
    Returns:
        pd.DataFrame: Updated crop data with filled variable values and source tracking.
        pd.Series: Percentage of acres associated with each source.
    """
    
    # 1. Calculate average value for neighboring counties
    expanded_crop_data = crop_data.explode('Neighboring Counties')
    merged_crop_data = pd.merge(
        expanded_crop_data,
        crop_data[['Crop_OpenAg', 'County', variable_column]],
        left_on=['Neighboring Counties', 'Crop_OpenAg'],
        right_on=['County', 'Crop_OpenAg'],
        suffixes=('', '_neighbor'),
        how='left'
    )
    avg_neighbor_values = merged_crop_data.groupby(['Crop_OpenAg', 'County'])[f'{variable_column}_neighbor'].mean()
    avg_neighbor_values_dict = avg_neighbor_values.to_dict()
    crop_data[f'neighboring_county_avg_{variable_column}'] = crop_data.set_index(['Crop_OpenAg', 'County']).index.map(avg_neighbor_values_dict)

    # 2. Calculate average value for each crop in HRs
    hr_avg_values = crop_data.groupby(['Crop_OpenAg', 'HR_NAME'])[variable_column].mean()
    hr_avg_values_dict = hr_avg_values.to_dict()
    crop_data[f'hr_avg_{variable_column}'] = crop_data.set_index(['Crop_OpenAg', 'HR_NAME']).index.map(hr_avg_values_dict)

    # 3. Calculate average value for neighboring HRs
    counties_hr = pd.read_csv('../../Datasets/econ_crop_data/counties_hr_neighbors.csv')
    hr_avg_values_df = pd.DataFrame(hr_avg_values).reset_index()
    hr_avg_values_with_neighbors = hr_avg_values_df.merge(
        counties_hr[['HR_NAME', 'Neighboring HR']],
        how='left',
        on='HR_NAME'
    ).drop_duplicates()
    hr_avg_values_with_neighbors['Neighboring HR'] = hr_avg_values_with_neighbors['Neighboring HR'].apply(ast.literal_eval)
    expanded_hr_avg_values = hr_avg_values_with_neighbors.explode('Neighboring HR')
    hr_avg_values_with_neighbor_values = expanded_hr_avg_values.merge(
        hr_avg_values_df[['Crop_OpenAg', 'HR_NAME', variable_column]],
        how='left',
        left_on=['Crop_OpenAg', 'Neighboring HR'],
        right_on=['Crop_OpenAg', 'HR_NAME']
    ).drop(columns=['HR_NAME_y']).rename(columns={
        'HR_NAME_x': 'HR_NAME',
        f'{variable_column}_x': f'base_hr_{variable_column}',
        f'{variable_column}_y': f'neighbor_hr_{variable_column}'
    })
    mean_neighbor_hr_values = hr_avg_values_with_neighbor_values.groupby(['Crop_OpenAg', 'HR_NAME'])[f'neighbor_hr_{variable_column}'].mean()
    mean_neighbor_hr_values_dict = mean_neighbor_hr_values.to_dict()
    crop_data[f'neighboring_hr_avg_{variable_column}'] = crop_data.set_index(['Crop_OpenAg', 'HR_NAME']).index.map(mean_neighbor_hr_values_dict)

    # 4. Calculate average value for each crop across the state
    avg_state_values = crop_data.groupby('Crop_OpenAg')[variable_column].mean()
    crop_data[f'state_avg_{variable_column}'] = crop_data['Crop_OpenAg'].map(avg_state_values)

    # 5. Fill missing values hierarchically
    def fill_variable(row):
        if pd.notna(row[variable_column]):
            return row[variable_column], variable_column
        elif pd.notna(row[f'neighboring_county_avg_{variable_column}']):
            return row[f'neighboring_county_avg_{variable_column}'], f'neighboring_county_avg_{variable_column}'
        elif pd.notna(row[f'hr_avg_{variable_column}']):
            return row[f'hr_avg_{variable_column}'], f'hr_avg_{variable_column}'
        else:
            return row[f'state_avg_{variable_column}'], f'state_avg_{variable_column}'

    crop_data[[f'final_{variable_column}', f'{variable_column}_source']] = crop_data.apply(
        lambda row: pd.Series(fill_variable(row)), axis=1
    )
    
    # 6. Calculate acres by value source and percentages
    # acres_by_value_source = crop_data.groupby(f'{variable_column}_source')['ACRES'].sum()
    # acres_percentage_by_value_source = (acres_by_value_source / acres_by_value_source.sum()) * 100
    
    columns_to_drop = [f'neighboring_county_avg_{variable_column}', 
                      f'hr_avg_{variable_column}', 
                      f'neighboring_hr_avg_{variable_column}', 
                      f'state_avg_{variable_column}',
                      f'{variable_column}_source']
    crop_data = crop_data.drop(columns=columns_to_drop)
   
    return crop_data

merged_aggregates = process_and_fill_variable(merged_aggregates, 'price_1')
merged_aggregates = process_and_fill_variable(merged_aggregates, 'price_2')
merged_aggregates = process_and_fill_variable(merged_aggregates, 'yield_1')
merged_aggregates = process_and_fill_variable(merged_aggregates, 'yield_2')
merged_aggregates = process_and_fill_variable(merged_aggregates, 'Fraction_1')
merged_aggregates['final_Fraction_2'] = 1-merged_aggregates['final_Fraction_1']
merged_aggregates.to_csv('../../Datasets/econ_crop_data/excptnl_crop_economic_data.csv')
