# -*- coding: utf-8 -*-
"""
Created on Sat Oct 12 21:07:47 2024

@author: armen
"""

from hecdss import HecDss
fname=r"C:\Users\armen\Desktop\COEQWAL\Datasets\s0002_DCR2023_9.3.1_danube_adj-20241012T184038Z-001\s0002_DCR2023_9.3.1_danube_adj\Model_Files\9.3.1_danube_adj\9.3.1_danube_adj\DSS\output\DCR2023_DV_9.3.1_v2a_Danube_Adj_v1.8.dss"
theFile = HecDss(fname) 
print(theFile)
dss = HecDss(fname)
print(f" record_count = {dss.record_count()}")
