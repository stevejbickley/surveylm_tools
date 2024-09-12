##### ------ IMPORT FUNCTIONS + SETUP CODE - START ------- ####

import random
import pandas as pd
import numpy as np
import openpyxl
import os
import re
from scipy.stats import norm
import glob

##### ------ DEFINE FUNCTIONS - START ------- ####

# Function to load the specified xlsx file, process the data by grouping it based on the "vignette" and "variation" columns, and save new xlsx files with the desired columns
def process_and_split_xlsx(file_path):
    # Load the xlsx file
    df = pd.read_excel(file_path)
    # Select only the required columns
    selected_columns = df[['question', 'question id', 'answer instruction', 'vignette', 'variation']]
    # Group by "vignette" and "variation" columns
    grouped = selected_columns.groupby(['vignette', 'variation'])
    # Iterate over each group and save to a new xlsx file
    for (vignette, variation), group in grouped:
        # Define the new file name
        file_name = f"questions_input_{vignette}_{variation}.xlsx"
        if os.path.exists(file_name):
            continue # skip this row if file already exists
        # Save the group to the new xlsx file
        group[['question', 'question id', 'answer instruction']].to_excel(file_name, index=False)

##### ------ MAIN CODE - START ------- ####

## ------ SECTION 1: Generate synthetic data using manually-designed agent inputs file ------ ##
input_file_paths = glob.glob('*scenario_database_final.xlsx')

# Read the file into a DataFrame
#input_file_path = 'sample_profile_generation_input_v5.xlsx'
#input_file_path = 'Ana_Maria_Matrix_for_agent_generation_updated_SB_31May2024.xlsx' # NOTE: old input file type used (v3)
#input_file_path = 'sample_profiles_input_DOOTSON_STUDY_v2.xlsx'

for input_file_path in input_file_paths:
    process_and_split_xlsx(input_file_path)



## ------ SECTION 2: XXXX ------ ##


##### ------ MAIN CODE - END ------- ####

