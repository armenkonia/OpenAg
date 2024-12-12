# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 22:52:44 2023

@author: armen
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
import matplotlib.pyplot as plt
from tqdm import tqdm

sac_id = gpd.read_file(r"C:\Users\armen\Desktop\COEQWAL\Datasets\ppic-sacramento-valley-delta-surface-water-availability\PPIC_SacramentoValley_SW_Availability_Shapes\ppic-sacramentovalley-sw-availability.shp")
sj_id = gpd.read_file(r"C:\Users\armen\Desktop\COEQWAL\Datasets\ppic-san-joaquin-valley-surface-water-availability\ppic_sjv_sw_availability.shp")

sac_id = sac_id.to_crs(epsg=3310)
sj_id = sj_id.to_crs(epsg=3310)

sac_id = sac_id.rename(columns={'AGENCYNAME': 'Agency_Nam',})
sac_id = sac_id.loc[:, ['Agency_Nam', 'geometry','gross_serv']]
sj_id = sj_id.loc[:, ['Agency_Nam', 'geometry','Service_Ar']]
sac_id = sac_id.rename(columns={'gross_serv': 'Total area',})
sj_id = sj_id.rename(columns={'Service_Ar': 'Total area',})
cv_id = pd.concat([sj_id, sac_id])

gdb_path = r"C:\Users\armen\Documents\ArcGIS\Projects\COEQWAL\COEQWAL.gdb"
cv_id.to_file(gdb_path, layer='central_valley_irrigation_districts', driver="GPKG")

data_temp = cv_id
data_temp = data_temp.rename(columns={"Agency_Nam": "id"})

# data_temp = gpd.read_file(r"C:\Users\armen\OneDrive - UCLA IT Services\UCLA Projects\COEQWAL\Data\Geospatial Data\i03_WaterDistricts\i03_WaterDistricts.shp")
#%%
data_temp = gpd.read_file(r"C:\Users\armen\OneDrive - UCLA IT Services\UCLA Projects\COEQWAL\Data\Geospatial Data\i03_WaterDistricts\i03_WaterDistricts.shp")
data_temp.plot(figsize=(12, 12))

# data_temp = data_temp.rename(columns={"Basin_ID": "id"})
data_temp = data_temp.rename(columns={"OBJECTID": "id"})

data_temp = data_temp[data_temp['geometry'].notna()]
data_temp = data_temp.loc[:,['id','AGENCYNAME','geometry']]
#%%
data_overlaps=gpd.GeoDataFrame()
for index, row in tqdm(data_temp.iterrows(), total=len(data_temp), desc="Processing rows"):
    data_temp1=data_temp.loc[data_temp.id!=row.id,]
    # check if intersection occured
    overlaps=data_temp1[data_temp1.geometry.overlaps(row.geometry)]['id'].tolist()
    if len(overlaps)>0:
        temp_list=[]
        # compare the area with threshold
        for y in overlaps:
            temp_area=gpd.overlay(data_temp.loc[data_temp.id==y,],data_temp.loc[data_temp.id==row.id,],how='intersection')
            temp_area=temp_area.loc[temp_area.geometry.area>=9e-9]
            if temp_area.shape[0]>0:
                data_overlaps=gpd.GeoDataFrame(pd.concat([temp_area,data_overlaps],ignore_index=True),crs=data_temp.crs)
#%%
# get unique of list id
data_overlaps['sorted']=data_overlaps.apply(lambda y: sorted([y['id_1'],y['id_2']]),axis=1)
data_overlaps['sorted']=data_overlaps.sorted.apply(lambda y: ''.join(y))
data_overlaps=data_overlaps.drop_duplicates('sorted')
data_overlaps=data_overlaps.reset_index()[['id_1','id_2','geometry']]
#%%
ax=data_temp.plot(figsize=(12, 12),alpha=0.7,edgecolor='black',linewidth=2)
data_overlaps.plot(ax=ax,color='red',edgecolor='green')
