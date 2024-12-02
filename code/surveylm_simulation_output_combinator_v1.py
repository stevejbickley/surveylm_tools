import pandas as pd
import os
from glob import glob

def process_survey_files(survey_files, metadata_file):
    # Load metadata
    metadata = pd.read_excel(metadata_file)
    # Initialize an empty list to store processed dataframes
    processed_dataframes = []
    for survey_file in survey_files:
        # Load each survey CSV file
        survey_data = pd.read_csv(survey_file)
        # Extract the last segment of 'question id' for merging
        survey_data["question_id_key"] = survey_data["question id"].apply(lambda x: "_".join(x.split("_")[3:]))
        # Create unique_agent_number column
        survey_data["unique_agent_number"] = survey_data["simulation id"].astype(str) + "_" + survey_data["agent"].astype(str)
        # Merge metadata based on condition
        merged_data = survey_data.merge(
            metadata,
            how="left",
            left_on="question_id_key",
            right_on="id"
        )
        # Append the processed dataframe to the list
        processed_dataframes.append(merged_data)
    # Concatenate all processed dataframes into one
    combined_dataframe = pd.concat(processed_dataframes, ignore_index=True)
    return combined_dataframe

# Define folder paths
#metadata_folder = "/Users/stevenbickley/Library/CloudStorage/Dropbox/chatGPT-research-QUT/doc/intrinsic_extrinsic_motivations/data/inputs/"
#survey_folder = "/Users/stevenbickley/Library/CloudStorage/Dropbox/chatGPT-research-QUT/doc/intrinsic_extrinsic_motivations/data/outputs/raw/"
metadata_folder = "/Users/stevenbickley/stevejbickley/surveylm_tools/data/inputs/treatment_combinations/"
survey_folder = "/Users/stevenbickley/stevejbickley/surveylm_tools/data/simulations/outputs/"


# Define paths for the TEACHER survey files and metadata file
teacher_survey_files = ["steve@panalogy-lab.com_completed_survey_data_1732614007.csv", "steve@panalogy-lab.com_completed_survey_data_1732678784.csv", "steve@panalogy-lab.com_completed_survey_data_1732574240_INCOMPLETE_CANCELLED_SLOW_RUN.csv"]
teacher_survey_files = [survey_folder + file for file in teacher_survey_files]
teacher_metadata_file = metadata_folder+"teacher_treatments_metadata.xlsx"

# Define paths for the NURSE survey files and metadata file
nurse_survey_files = ["steve@panalogy-lab.com_completed_survey_data_1732534195.csv"]
nurse_survey_files = [survey_folder + file for file in nurse_survey_files]
nurse_metadata_file = metadata_folder+"nurse_treatments_metadata.xlsx"

# Process the files
teacher_final_dataframe = process_survey_files(teacher_survey_files, teacher_metadata_file)
nurse_final_dataframe = process_survey_files(nurse_survey_files, nurse_metadata_file)

# Save or display the result
# i) Teachers
teacher_final_dataframe.to_csv("./combined_teacher_simulation_data.csv", index=False)
print("Processed data saved to 'combined_teacher_simulation_data.csv'")

# ii) Nurses
nurse_final_dataframe.to_csv("./combined_nurse_simulation_data.csv", index=False)
print("Processed data saved to 'combined_nurse_simulation_data.csv'")

# Print the question id counts for each of the _final_dataframe's...
teacher_final_dataframe["question id"].value_counts().tolist() # All with 50 observations
nurse_final_dataframe["question id"].value_counts().tolist() # All with 50 observations