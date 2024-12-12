# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 20:26:00 2024

@author: armen
"""
#checking if the demand units are the same, im not looking at any other column
import pandas as pd

DU_SJ_TL = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\calsim demand units\Agricultural_Demand_Units_in_San_Joaquin_and_Tulare_Lake_Hydrologic_Regions_3_6.xlsx")
DU_SJ_TL['Demand Unit'] = DU_SJ_TL['Demand Unit'].ffill()

DU_Sac = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\calsim demand units\Sacramento_River_Hydrologic_Region_Demand_Units_3_3.xlsx")
DU_Sac['Demand Unit'] = DU_Sac['Demand Unit'].ffill()

Div_Sac_NP = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\calsim demand units\Non_Project_Agricultural_Diversions_from_Sacramento_River_3_4.xlsx")
Div_Sac_NP['Demand Unit'] = Div_Sac_NP['Demand Unit'].ffill()
Div_Sac_NP['Area (acres)'] = Div_Sac_NP['Area (acres)'].ffill()

Div_Feather_ND = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\calsim demand units\Non_District_Agricultural_Diversions_from_Feather_River_3_5.xlsx")
Div_Feather_ND['Demand Unit'] = Div_Feather_ND['Demand Unit'].ffill()

DU_ag = pd.concat([DU_SJ_TL, DU_Sac])
DU_ag = DU_ag.sort_values(by='Demand Unit')

#%%
DU_all = pd.read_excel(r"C:\Users\armen\Desktop\COEQWAL\calsim\cs3rpt2022_all_demand_units_v20241003.xlsx",sheet_name='all_demand_units',header=1)
DU_all_ag = DU_all.loc[DU_all['Unit Type (Ag, MI, Refuge/Wetland)'] == 'AG']
DU_all_ag = DU_all_ag.sort_values(by='Demand Unit')

#%%%
DU_all_ag.reset_index(drop=True, inplace=True)
DU_ag.reset_index(drop=True, inplace=True)
DU_all_ag['Demand Unit'].equals(DU_ag['Demand Unit'])
differences = DU_all_ag['Demand Unit'][DU_all_ag['Demand Unit'] != DU_ag['Demand Unit']]
