##### ------ IMPORT FUNCTIONS + SETUP CODE ------- ####

import pandas as pd

##### ------ DEFINE FUNCTIONS ------- ####

# Function to generate pairwise combinations of baseline scenarios and treatment variations, and assign unique IDs
def generate_combinations_with_ids_to_excel(baseline_scenarios, treatment_variations, baseline_prefixes, treatment_prefixes, answer_instruction, output_filename, treatment_to_baseline_map=None):
    """
    Generate all combinations of baseline scenarios and treatment variations with unique IDs and save them to an Excel file.
    Args:
    - baseline_scenarios (list): List of baseline scenarios.
    - treatment_variations (list): List of treatment variations.
    - baseline_prefixes (list): List of short descriptors for each baseline scenario.
    - treatment_prefixes (list): List of short descriptors for each treatment variation.
    - answer_instruction (str): The standardized answer instruction for all questions.
    - output_filename (str): The filename for the output Excel file.
    - treatment_to_baseline_map (dict): A mapping of treatment prefixes to explicitly excluded baseline prefixes.
    """
    # Ensure prefixes match the scenarios and treatments
    if len(baseline_scenarios) != len(baseline_prefixes):
        raise ValueError("Number of baseline prefixes must match the number of baseline scenarios.")
    if len(treatment_variations) != len(treatment_prefixes):
        raise ValueError("Number of treatment prefixes must match the number of treatment variations.")
    # Initialize the map as empty if None is provided
    if treatment_to_baseline_map is None:
        treatment_to_baseline_map = {}
    # Create a list of all combinations
    combinations = []
    for baseline_idx, baseline in enumerate(baseline_scenarios):
        baseline_prefix = baseline_prefixes[baseline_idx]
        # Add the baseline-only question
        baseline_id = f"{baseline_prefix}_baseline_treatment"
        combinations.append({"question": baseline,
                             "question id": baseline_id,
                             "answer instruction": answer_instruction})
        # Add the baseline with each treatment variation
        for treatment_idx, treatment in enumerate(treatment_variations):
            treatment_prefix = treatment_prefixes[treatment_idx]
            # Check if the treatment explicitly excludes the current baseline prefix
            if treatment_prefix in treatment_to_baseline_map and baseline_prefix in treatment_to_baseline_map[treatment_prefix]:
                continue
            # Combine baseline and treatment
            full_question = f"{baseline.rstrip('?')}, considering that {treatment}?"
            combinations.append({"question": full_question,
                                 "question id": f"{baseline_prefix}_{treatment_prefix}",
                                 "answer instruction": answer_instruction})
    # Convert to a DataFrame
    df = pd.DataFrame(combinations)
    # Save to Excel
    df.to_excel(output_filename, index=False)
    print(f"Combinations with IDs and instructions saved to {output_filename}")

##### ------ MAIN CODE ------- ####

# Define baseline scenarios
baseline_scenarios = [
    "You are a teacher working in a school, and there is a shortage of staff. How many extra hours per week, above and beyond your normal working hours, would you offer to help your school deal with this problem?",
    "You are a nurse working in a hospital, and there is a shortage of staff. How many extra hours per week, above and beyond your normal working hours, would you offer to help your hospital deal with this problem?"
]

# Define short descriptors for baseline scenarios
baseline_prefixes = ["teacher_baseline", "nurse_baseline"]

# Define treatment variations
treatment_variations = [
    "you contributing extra hours would grant you the option to set and manage your daily schedule during regular work hours in the next school term",
    "you would be compensated with additional paid vacation days",
    "you would receive a financial bonus worth two weeks of your salary"
]

# Define short descriptors for treatment variations
treatment_prefixes = ["flexible_hours", "vacation_days", "financial_bonus"]

# Define the treatment to baseline mappings for excluding certain treatment_prefixes from combining with certain baseline_prefixes
treatment_to_baseline_map = {
    "flexible_hours": ["nurse_baseline"],  # Exclude nurses from this treatment
}

# Define a standardized answer instruction
answer_instruction = "Please write the number of extra hours per week you are willing to work as a numerical value, with a maximum of 2 decimal places."

# Define the output file name
output_filename = "combinations_with_ids.xlsx"

# Generate combinations with IDs and save to Excel
generate_combinations_with_ids_to_excel(baseline_scenarios, treatment_variations, baseline_prefixes, treatment_prefixes, treatment_to_baseline_map, answer_instruction, output_filename)

##### ------ END OF CODE/SCRIPT ------- ####