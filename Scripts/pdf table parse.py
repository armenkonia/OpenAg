# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 12:01:16 2024

@author: armen
"""

import pdfplumber
import pandas as pd
from io import StringIO
from PyPDF2 import PdfReader

doc_path = r"C:\Users\armen\Desktop\COEQWAL\calsim-3-report-final.pdf"
page_number = 57

with pdfplumber.open(doc_path) as pdf:
    # Get the specific page (0-indexed)
    page = pdf.pages[page_number - 1]
    text = page.extract_text()
    
data_lines = text.splitlines()[8:51]  # Remove first 6 lines
cleaned_data = "\n".join(data_lines)
column_names = ['Calendar Year','Local Supplies','LA Aqueduct','Colorado river Aqueduct','State Water Project', 'Total']
df = pd.read_csv(StringIO(cleaned_data), delimiter=' ', on_bad_lines='skip')
df.set_index('Year', inplace=True)
df = df.replace(',', '').apply(pd.to_numeric)

#%%
import pdfplumber
with pdfplumber.open(doc_path) as pdf:
    page = pdf.pages[56]  # Page 57 in zero-indexing
    table = page.extract_table()

page.to_image().debug_tablefinder()
bbox = (50, 100, 550, 600)
image = page.to_image()
image.draw_rect(bbox)

#%%
# Open the PDF and select the desired page
with pdfplumber.open(doc_path) as pdf:
    page = pdf.pages[56]  # Page 57 in zero-indexing

    # Define table settings to ensure it uses lines for cell boundaries
    table_settings = {
        "vertical_strategy": "text",  # Use text positions to define vertical boundaries
        "horizontal_strategy": "lines",  # Use horizontal lines to define row boundaries
        "snap_tolerance": 3,
        "intersection_tolerance": 5,
    }

    # Extract the table with the defined settings
    table = page.extract_table(table_settings)

table_settings = {
    "vertical_strategy": "text",  # Use text positions to define vertical boundaries
    "horizontal_strategy": "lines",  # Use horizontal lines to define row boundaries
    "snap_tolerance": 3,
    "intersection_tolerance": 5,
}

image = page.to_image()
image.debug_tablefinder(table_settings=table_settings)
