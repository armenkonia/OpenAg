# -*- coding: utf-8 -*-
"""
Created on Sat Oct 12 21:25:07 2024

@author: armen
"""


import pyhecdss
import pandas as pd
fname=r"C:\Users\armen\Desktop\COEQWAL\Datasets\s0002_DCR2023_9.3.1_danube_adj-20241012T184038Z-001\s0002_DCR2023_9.3.1_danube_adj\Model_Files\9.3.1_danube_adj\9.3.1_danube_adj\DSS\output\DCR2023_DV_9.3.1_v2a_Danube_Adj_v1.8_new.dss"
with pyhecdss.DSSFile(fname) as d:
    d.close()

with pyhecdss.DSSFile(fname) as d:
    catdf=d.read_catalog()
    # display(catdf)
catdf.F.unique()

# Function to build DSS pathname from the catalog DataFrame
def build_dss_path(row):
    return f"/{row['A']}/{row['B']}/{row['C']}/{row['D']}/{row['E']}/{row['F']}/"

first_row = catdf.iloc[0]  # Get the first row of the DataFrame
pathname = build_dss_path(first_row)  # Build DSS pathname using the first row
#%%
# Import the necessary class
from hecdss import HecDss

dss_file_path=r"C:\Users\armen\Desktop\COEQWAL\Datasets\s0002_DCR2023_9.3.1_danube_adj-20241012T184038Z-001\s0002_DCR2023_9.3.1_danube_adj\Model_Files\9.3.1_danube_adj\9.3.1_danube_adj\DSS\output\DCR2023_DV_9.3.1_v2a_Danube_Adj_v1.8_new.dss"
hec_dss = HecDss(dss_file_path)
hec_dss_catalog = hec_dss.get_catalog()


from hecdss import dsspath
dss = dsspath(dss_file_path)
