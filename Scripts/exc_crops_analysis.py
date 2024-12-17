# -*- coding: utf-8 -*-
"""
Created on Mon Dec 16 12:55:50 2024

@author: armen
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

usda_crops_av = pd.read_csv('../Datasets/Output/processed_usda_crops_18_22.csv', index_col=0)
usda_crops_av = usda_crops_av[['Crop Name', 'County', 'HR_NAME', 'price_avg', 'production_avg', 'acres_avg', 'yield_avg']]
grapes_df = usda_crops_av.loc[usda_crops_av['Crop Name'].str.contains("grapes", case=False, na=False)]
tomatoes_df = usda_crops_av.loc[usda_crops_av['Crop Name'].str.contains("tomatoes", case=False, na=False)]
tomatoes_grouped = tomatoes_df.groupby(['Crop Name','HR_NAME']).mean(numeric_only=True).reset_index()
grapes_grouped = grapes_df.groupby(['Crop Name','HR_NAME']).mean(numeric_only=True).reset_index()

# final_df = pd.read_csv('../Datasets/Output/final_crop_economic_data.csv')
#%%

# Create a grouped bar plot
plt.figure(figsize=(14, 8))
sns.barplot(data=tomatoes_grouped, x='HR_NAME', y='acres_avg', hue='Crop Name', palette='Dark2')

# Customizations
plt.xticks(rotation=45, ha='right')
plt.xlabel('HR_NAME')
plt.ylabel('Average Acres')
plt.title('Comparison of Crop Acres by HR_NAME')
plt.legend(title='Crop Name', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()
#%%
# Create a grouped bar plot
plt.figure(figsize=(14, 8))
sns.barplot(data=grapes_grouped, x='HR_NAME', y='acres_avg', hue='Crop Name', palette='Dark2')

# Customizations
plt.xticks(rotation=45, ha='right')
plt.xlabel('HR_NAME')
plt.ylabel('Average Acres')
plt.title('Comparison of Crop Acres by HR_NAME')
plt.legend(title='Crop Name', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()
#%%

fig, axes = plt.subplots(1, 2, figsize=(15, 5))

# Plot for tomatoes_grouped
sns.barplot(
    data=tomatoes_grouped, x='HR_NAME', y='acres_avg', hue='Crop Name', palette='Dark2', ax=axes[0]
)
axes[0].set_title('Tomatoes - Comparison of Crop Acres by HR_NAME')
axes[0].set_ylabel('Average Acres')
axes[0].tick_params(axis='x', rotation=90)
axes[0].legend(title='Crop Name', bbox_to_anchor=(1.05, 1), loc='upper left')

# Plot for grapes_grouped
sns.barplot(
    data=grapes_grouped, x='HR_NAME', y='acres_avg', hue='Crop Name', palette='Dark2', ax=axes[1]
)
axes[1].set_title('Grapes - Comparison of Crop Acres by HR_NAME')
axes[1].set_ylabel('')  # No y-axis label for the second plot to avoid redundancy
axes[1].tick_params(axis='x', rotation=90)
axes[1].legend(title='Crop Name', bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.show()
