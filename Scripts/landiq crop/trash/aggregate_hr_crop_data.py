# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 18:31:47 2024

@author: armen
"""

import pickle 
import pandas as pd
import matplotlib.pyplot as plt
import os

with open(r"C:\Users\armen\Desktop\COEQWAL\Datasets\Outputs\hr_crop_analysis_results.pkl", 'rb') as f:
    hr_crop_analysis_results_dict = pickle.load(f)

agg_crops_dic = {}
for hr_name, result_dict_list in hr_crop_analysis_results_dict.items():
        agg_crops_dic[hr_name]=result_dict_list['agg_crops']
        

all_agg_crops_dfs = []
for hr_name, agg_crops_df in agg_crops_dic.items():
    agg_crops_df['HR_NAME'] = hr_name
    all_agg_crops_dfs.append(agg_crops_df)

merged_agg_crops_df = pd.concat(all_agg_crops_dfs, ignore_index=True)

#%%
wa_agg_crops_df = merged_agg_crops_df[merged_agg_crops_df['Crop Name'].str.startswith('WA_')]
save_folder = r"C:\Users\armen\Desktop\COEQWAL\Datasets\Outputs\commodity_crops\HR REGIONS"
os.makedirs(save_folder, exist_ok=True)

for hr_name in wa_agg_crops_df['HR_NAME'].unique():
    # Filter the DataFrame for the current HR_NAME
    hr_filtered_df = wa_agg_crops_df[wa_agg_crops_df['HR_NAME'] == hr_name]
    
    # Create the plot
    fig, axs = plt.subplots(1, 1, figsize=(15, 5))  # 2 subplots
    axs.bar(hr_filtered_df['Crop_OpenAg'], hr_filtered_df['Area (acreage)'])
    
    # Customize the plot
    axs.set_title(f'{hr_name} - Crop Area in 2020')
    axs.set_ylabel('Area (acreage)')
    axs.tick_params(axis='x', rotation=90)
    axs.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plot_filename = f"{hr_name.replace(' ', '_')}_crop_area_2020.png"
    plot_filepath = os.path.join(save_folder, plot_filename)
    plt.savefig(plot_filepath)
    plt.close()  # Close the figure to avoid displaying it in the notebook
#%%
fig, axs = plt.subplots(2, 5, figsize=(20, 10),sharey=True)  # Adjust figsize to accommodate all subplots

axs = axs.flatten()
for idx, hr_name in enumerate(wa_agg_crops_df['HR_NAME'].unique()):
    hr_filtered_df = wa_agg_crops_df[wa_agg_crops_df['HR_NAME'] == hr_name]
    axs[idx].bar(hr_filtered_df['Crop_OpenAg'], hr_filtered_df['Area (acreage)'])
    
    axs[idx].set_title(f'{hr_name} - Crop Area in 2020')
    axs[idx].set_ylabel('Area (acreage)')
    axs[idx].tick_params(axis='x', rotation=90)
    axs[idx].grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(r"C:\Users\armen\Desktop\COEQWAL\Datasets\Outputs\commodity_crops\HR REGIONS\combined_crop_area_2020.png")
plt.show()
