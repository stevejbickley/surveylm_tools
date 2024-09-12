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

# Function to
def parse_input_value(input_str):
    try:
        mean, sd = map(str, input_str.split(' (SD = '))
        mean = float(mean)
        sd = float(sd.strip(')'))
        return mean, sd
    except ValueError:
        raise ValueError(f"Invalid input format: {input_str}")

# Function to
def generate_option_set(mean, sd, value_type, num_options=5, jump=5, only_positive=True):
    options = []
    if value_type == "discrete":
        for i in range(num_options):
            option = round(mean + sd * (i - (num_options // 2)) * (1/jump))
            if only_positive:
                option = max(1, option)  # Ensure option is at least 1
            if option in options:
                print(f"Warning: considering reducing the num_options or increasing the jumps, skipping option: {option} as exists already in options")
                continue
            else:
                options.append(option)
        return options
    elif value_type == "grouped" or value_type == "":
        i = 0
        while len(options) < num_options:
            lower = round(mean + sd * (i - (num_options // 2)) * (1/jump))
            upper = round(mean + sd * (i - (num_options // 2) + 1) * (1/jump)) - 1
            if only_positive:
                if upper < 1:
                    i += 1
                    continue
                lower = max(1, lower)
                upper = max(1, upper)
            options.append(f"{lower}-{upper}")
            i += 1
        return options
    else:
        raise ValueError(f"Invalid value type: {value_type}")

# Function to
def extract_range(option):
    # Use regular expression to find all numbers and the "-" character between them
    match = re.search(r'(\d+)-(\d+)', option)
    if match:
        lower, upper = map(int, match.groups())
    else:
        # In case of no match, we will raise an error or handle it appropriately
        lower = upper = int(option)
        #print(f"Warning: invalid range format in option: {option}")
    return lower, upper

# (Expensive) Function to
def update_probability_distribution(df, ind, mean, sd,remove_diff_type="from_all_equally"):
    for index, row in df.iterrows():
        if int(index) == int(ind):
            options = row['option_set'].split(';')
            if pd.isna(row['item_probability_distribution']):
                uniform_probability = 1 / len(options)
                df.at[index, 'item_probability_distribution'] = ';'.join([str(uniform_probability)] * len(options))
            # Assuming options are given in a way that they can be mapped to ranges
            all_discrete = True  # To check if all options are discrete
            probabilities = []
            for option in options:
                lower, upper = extract_range(option)
                if lower != upper:
                    all_discrete = False
                # Calculate the cumulative distribution function values
                lower_cdf = norm.cdf(lower, mean, sd)
                upper_cdf = norm.cdf(upper + 1, mean, sd)
                probability = upper_cdf - lower_cdf
                probabilities.append(probability)
            if all_discrete:
                # Handle discrete options
                probabilities = [norm.pdf(int(option), mean, sd) for option in options]
            # Normalize the probabilities to sum to 1
            total_prob = sum(probabilities)
            normalized_probabilities = [p / total_prob for p in probabilities]
            # Round the probabilities to the specified number of decimal places
            rounded_probabilities = [p for p in normalized_probabilities]
            df.at[index, 'item_probability_distribution'] = ';'.join(map(str, rounded_probabilities))
            item_probabilities = df.at[index, 'item_probability_distribution'].split(';') if pd.notna(df.at[index, 'item_probability_distribution']) else []
            probability_values = [float(p) if p else 0.0 for p in item_probabilities]
            if not np.isclose(sum(probability_values), 1.0):
                diff_to_fix = sum(probability_values) - 1.0
                if remove_diff_type == "from_minimum":
                    min_value = min(probability_values)
                    probability_values = [float(p - diff_to_fix) if p == min_value else p for p in probability_values]
                elif remove_diff_type == "from_maximum":
                    max_value = max(probability_values)
                    probability_values = [float(p - diff_to_fix) if p == max_value else p for p in probability_values]
                else: # remove_diff_type == "from_all_equally"
                    avg_diff_to_fix = diff_to_fix / len(probability_values)
                    probability_values = [float(p - avg_diff_to_fix) if p else p for p in probability_values]
                df.at[index, 'item_probability_distribution'] = ';'.join(map(str, probability_values))
    return df

# Function to
def validate_and_normalize_input_data(df, remove_diff_type):
    if df.empty:
        return "Error: Input file is empty."
    for index, row in df.iterrows():
        if pd.notna(df.at[index, 'item_probability_set']): # Then parse input values
            try:
                mean, sd = parse_input_value(df.at[index, 'item_probability_set'])
                if pd.isna(df.at[index, 'option_set']):
                    options = generate_option_set(mean, sd, value_type=str(df.at[index, 'item_probability_set_type']), num_options=int(df.at[index, 'item_probability_set_n_options']), jump=int(df.at[index, 'item_probability_set_jumps']))
                    df.at[index, 'option_set'] = ';'.join(map(str, options))
                df = update_probability_distribution(df, index, mean, sd, remove_diff_type)
            except ValueError as e:
                return f"Error at row {index + 1}: {e}"
        # Validate option_set
        options = df.at[index, 'option_set'].split(';') if pd.notna(df.at[index, 'option_set']) else []
        if not options:
            return f"Error at row {index + 1}: 'option_set' must contain at least one option."
        # Validate item_cross_probability_with_item_names
        cross_items=[]
        if pd.notna(df.at[index, 'item_cross_probability_with_item_names']):
            cross_items = df.at[index, 'item_cross_probability_with_item_names'].split(';')
            if not all(item in df['item_name'].unique() for item in cross_items):
                return f"Error at row {index + 1}: 'item_cross_probability_with_item_names' must only include valid 'item_name' entries."
            if len(cross_items) > 1:
                return f"Error at row {index + 1}: 'item_cross_probability_with_item_names' should have one value but has {len(cross_items)}."
        # Validate item_cross_probability_with_item_probabilities
        if cross_items:
            cross_probabilities = df.at[index, 'item_cross_probability_with_item_probabilities'].split(';') if pd.notna(df.at[index, 'item_cross_probability_with_item_probabilities']) else []
            if cross_probabilities:
                cross_options_lengths = [len(df[df['item_name'] == item]['option_set'].values[0].split(';')) for item in cross_items]
                expected_length = len(options) * sum(cross_options_lengths)
                if len(cross_probabilities) != expected_length:
                    return f"Error at row {index + 1}: 'item_cross_probability_with_item_probabilities' should have {expected_length} values but has {len(cross_probabilities)}."
                # Split cross_probabilities into sublists for each age group
                sublists = [cross_probabilities[i:i + len(options)] for i in range(0, len(cross_probabilities), len(options))]
                # Validate each sublist
                for sublist in sublists:
                    probability_values = [float(p) if p else 0.0 for p in sublist]
                    if not np.isclose(sum(probability_values), 1.0) or any(p < 0 for p in probability_values):
                        return f"Error at row {index + 1}: Each set of cross probabilities must be nonnegative and sum to 1."
        # Validate individual item_probability_distribution
        item_probabilities = df.at[index, 'item_probability_distribution'].split(';') if pd.notna(df.at[index, 'item_probability_distribution']) else []
        if item_probabilities:
            if len(item_probabilities) != len(options):
                return f"Error at row {index + 1}: 'item_probability_distribution' must have {len(options)} values but has {len(item_probabilities)}."
            probability_values = [float(p) if p else 0.0 for p in item_probabilities]
            if not np.isclose(sum(probability_values), 1.0):
                return f"Error at row {index + 1}: Item probabilities must all sum to 1."
            if any(p < 0 for p in probability_values):
                return f"Error at row {index + 1}: Item probabilities must all be nonnegative."
    return df

# Function to
def read_input_file(file_path, remove_diff_type, ):
    df = pd.read_excel(file_path)
    # Preprocess and normalize the data
    for index, row in df.iterrows():
        # Check if the probability distribution is provided, if not, generate a uniform distribution
        if pd.isna(row['item_probability_distribution']):
            try:
                options = row['option_set'].split(';')
                uniform_probability = 1 / len(options)
                df.at[index, 'item_probability_distribution'] = ';'.join([str(uniform_probability)] * len(options))
            except:
                pass
    # Validate and normalize data
    validation_result = validate_and_normalize_input_data(df, remove_diff_type)
    if isinstance(validation_result, str) and validation_result.startswith("Error"):
        print(validation_result)
        return None
    else:
        df = validation_result
    return df

# Function to
def parse_joint_probabilities(joint_probabilities_str, dimension_sizes):
    probabilities = list(map(float, joint_probabilities_str.split(';')))
    joint_probabilities_matrix = np.reshape(probabilities, dimension_sizes)
    return joint_probabilities_matrix

# Function to
def generate_agent_profiles_with_dependencies(df, num_agents):
    # Additional preprocessing to handle joint probabilities
    agents = []
    for _ in range(num_agents):
        agent = {}
        dependent_values = {}
        for _, row in df.iterrows():
            options = row['option_set'].split(';')
            item_name = row['item_name']
            if 'item_cross_probability_with_item_names' in row and not row['item_cross_probability_with_item_names'] != row['item_cross_probability_with_item_names']:
                # Cross-dependency exists
                cross_items = row['item_cross_probability_with_item_names'].split(';')
                cross_options_lengths = [len(df[df['item_name'] == item]['option_set'].values[0].split(';')) for item in cross_items]
                dimension_sizes = (len(options), sum(cross_options_lengths))
                # Parse the joint probabilities
                joint_probabilities_matrix = parse_joint_probabilities(row['item_cross_probability_with_item_probabilities'], dimension_sizes)
                # Logic to select options based on joint probabilities
                if all(dependency in dependent_values for dependency in cross_items):
                    # All dependencies have been processed before
                    dependent_indexes = [dependent_values[dependency] for dependency in cross_items]
                    probabilities = joint_probabilities_matrix[:, dependent_indexes].flatten()
                    choice = random.choices(options, weights=probabilities, k=1)[0]
                else:
                    # Fallback to individual probabilities if dependencies are not yet processed
                    probabilities = row['item_probability_distribution'].split(';')
                    probabilities = [float(p) if p else 0.0 for p in probabilities]
                    choice = random.choices(options, weights=probabilities, k=1)[0]
            else:
                probabilities = row['item_probability_distribution'].split(';')
                probabilities = [float(p) if p else 0.0 for p in probabilities]
                choice = random.choices(options, weights=probabilities, k=1)[0]
            agent[item_name] = choice
            dependent_values[item_name] = options.index(choice)
        agents.append(agent)
    return agents

# Function to
def clean_special_characters(df):
    def replace_special_chars(text):
        # Replace "/" with " or "
        text = text.replace("/", " or ")
        # Replace " (" with ", "
        text = text.replace(" (", ", ")
        # Replace ")" with ""
        text = text.replace(")", "")
        # Replace "-" with " to " if it is surrounded by numbers
        text = re.sub(r'(\d+)-(\d+)', r'\1 to \2', text)
        return text
    # Clean the DataFrame values
    cleaned_df = df.map(lambda x: replace_special_chars(x) if isinstance(x, str) else x)
    # Clean the column names
    cleaned_df.columns = [replace_special_chars(col) for col in df.columns]
    return cleaned_df

# Function to extract filename without extension
# NOTE: we should also add "foldname_pattern" and "foldname" variables to the return for this function (i.e. file and source folder names separately)
def extract_filename(filepath):
    fname_pattern = r'([^/]+)(?=\.[^.]+$)' # Regular expression to match the filename without extension
    fname = re.search(fname_pattern, filepath)
    if fname:
        return fname.group(1)
    else:
        return None

##### ------ MAIN CODE - START ------- ####

## ------ SECTION 1: Generate synthetic data using manually-designed agent inputs file ------ ##
input_file_paths = glob.glob('sample_profiles_input_'+'*_v2.xlsx')

# Read the file into a DataFrame
#input_file_path = 'sample_profile_generation_input_v5.xlsx'
#input_file_path = 'Ana_Maria_Matrix_for_agent_generation_updated_SB_31May2024.xlsx' # NOTE: old input file type used (v3)
#input_file_path = 'sample_profiles_input_DOOTSON_STUDY_v2.xlsx'

for input_file_path in input_file_paths:
    if os.path.exists(input_file_path[:-5] + '_agents_output.xlsx'):
        continue
    else:
        input_data = read_input_file(file_path=input_file_path, remove_diff_type="from_all_equally")
        # Example usage
        num_agents = 500
        agents_data = generate_agent_profiles_with_dependencies(input_data, num_agents)
        # Convert agents data to DataFrame and save to xlsx
        agents_df = pd.DataFrame(agents_data)
        agents_df = clean_special_characters(agents_df)
        agents_df.to_excel(input_file_path[:-5] + '_agents_output.xlsx', index=False)
        #agents_df.columns # (OPTIONAL) Check column names



## ------ SECTION 2: Generate synthetic data using existing agent inputs file ------ ##

# Function to compute the joint probabilities of the specified columns in the dataset
def create_joint_probability_matrix(data, column_names):
    # Check if the input is a file path or a DataFrame
    if isinstance(data, str):
        data = pd.read_csv(data) if data.endswith('.csv') else pd.read_excel(data)
    # Filter the dataset to only include the specified columns
    df_subset = data[column_names]
    # Calculate the joint frequency of the specified columns
    joint_frequency = df_subset.value_counts(normalize=True)
    # Convert the joint frequency to a probability matrix
    joint_probability_matrix = joint_frequency.unstack(fill_value=0)
    return joint_probability_matrix

# Function that uses the joint probability matrix to generate a sample population of agents
def generate_sample_population(joint_prob_matrix, n):
    flat_probs = joint_prob_matrix.values.flatten()
    flat_probs /= flat_probs.sum()
    sample_indices = np.random.choice(len(flat_probs), size=n, p=flat_probs)
    # Convert flat indices to multi-dimensional indices
    row_indices, col_indices = np.unravel_index(sample_indices, joint_prob_matrix.shape)
    sampled_agents = []
    for row_idx, col_idx in zip(row_indices, col_indices):
        # Fetch the corresponding categories for each index
        row_values = joint_prob_matrix.index[row_idx]  # This will be a tuple for multi-level indices
        col_value = joint_prob_matrix.columns[col_idx]
        # Combine row values and column value(s) into a single list
        agent = list(row_values) + [col_value]
        sampled_agents.append(agent)
    # The column names consist of the row index names and column index names
    column_names = joint_prob_matrix.index.names + joint_prob_matrix.columns.names
    sample_df = pd.DataFrame(sampled_agents, columns=column_names)
    return sample_df

# Function to iteratively generate sample populations of 100 agents for each country
# E.g., grouping by the column "ISO 3166-1 numeric country code"
def generate_country_sample_populations(df, country_col, columns_of_interest, n_samples):
    sample_populations = {}
    # Get unique country codes
    unique_countries = df[country_col].unique()
    for country in unique_countries:
        # Filter dataframe for the specific country
        country_df = df[df[country_col] == country]
        # Generate the joint probability matrix for the country
        joint_prob_matrix = create_joint_probability_matrix(country_df, columns_of_interest)
        # Generate the sample population for the country
        sample_population = generate_sample_population(joint_prob_matrix, n_samples)
        # Store the sample population in the dictionary
        sample_populations[country] = sample_population
    return sample_populations

# Function to convert the sample populations dictionary back into a dataframe
def convert_sample_populations_to_df(sample_populations):
    combined_df = pd.DataFrame()
    for country_code, sample_df in sample_populations.items():
        sample_df = sample_df.reset_index()  # Reset index to convert multi-index to columns
        sample_df['Country_Code'] = country_code  # Add a new column for the country code
        combined_df = pd.concat([combined_df, sample_df], ignore_index=True)
    return combined_df

def optimize_dataframe(df):
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype == 'string':
            num_unique_values = len(df[col].unique())
            num_total_values = len(df[col])
            if num_unique_values / num_total_values < 0.5:
                df[col] = df[col].astype('category')
            else:
                df[col] = df[col].astype('string')
        elif df[col].dtype == 'int64':
            df[col] = pd.to_numeric(df[col], downcast='integer')
        elif df[col].dtype == 'float64':
            df[col] = pd.to_numeric(df[col], downcast='float')
    return df

# Applying the function to agents_df
optimized_agents_df = optimize_dataframe(agents_df)

# Define the existing agent dataset and the columns you are interested in
#original_data_path = '/Users/stevenbickley/stevejbickley/data_assorted/Integrated_values_surveys_1981-2021_decoded_dta2xlsx_python.csv'
original_data_path = '/Users/stevenbickley/stevejbickley/data_assorted/WVS_TimeSeries_1981_2022_Stata_v3_0.csv'
column_mappings_path = '/Users/stevenbickley/stevejbickley/data_assorted/F00003843_WVS_EVS_Integrated_Dictionary_Codebook_v_2014_09_22.csv'

# /Users/stevenbickley/stevejbickley/data_assorted/Integrated_values_surveys_1981-2021_decoded_stata.csv
# /Users/stevenbickley/stevejbickley/data_assorted/Integrated_values_surveys_1981-2021_decoded_dta2xlsx_python.csv
# /Users/stevenbickley/stevejbickley/data_assorted/SurveyLM_Agent_Profile_Generator/CustomisedProfile_WVS_v2.xlsx
# '/Users/stevenbickley/stevejbickley/data_assorted/WVS_TimeSeries_1981_2022_Stata_v3_0.csv'

# Now read in the xlsx or csv file:
# Note 1: agents_df.columns # View column names
# Note 2: agents_df.columns.tolist() # View column names for datasets with > 30 columns
try:
    agents_df = pd.read_excel(original_data_path)
except:
    agents_df = pd.read_csv(original_data_path)

# Create column mapping dictionary
column_mapping = {
    "version": "Version of Data File",
    "doi": "Digital Object Identifier",
    "S002VS": "Chronology of EVS-WVS waves",
    "S003": "ISO 3166-1 numeric country code",
    "COUNTRY_ALPHA": "ISO 3166-1 alpha-3 country code",
    "COW_NUM": "CoW country code numeric",
    "COW_ALPHA": "CoW country code alpha",
    "S006": "Original respondent number",
    "S007": "Unified respondent number",
    "S008": "Interviewer number",
    "mode": "Mode of data collection",
    "S010": "Total length of interview",
    "S011A": "Time of the interview - Start",
    "S011B": "Time at the end of interview",
    "S012": "Date interview",
    "S013": "Respondent interested during interview",
    "S013B": "Interview privacy",
    "S016": "Language of the interview",
    "S016B": "Language in which interview was conducted",
    "S017": "Weight",
    "S018": "Equilibrated weight-1000",
    "S020": "Year survey",
    "S021": "Country - wave - study - set",
    "S022": "Year/month of start-fieldwork",
    "S023": "Year/month of end-fieldwork",
    "S024": "Country - wave",
    "S025": "Country - year",
    "V001A": "Fathers country of birth - ISO 3166-1 code",
    "V002A": "Mothers country of birth - ISO 3166-1 code",
    "V004AF_01": "Highest educational level attained - Respondent’s Father ISCED",
    "V004AM_01": "Highest educational level attained - Respondent’s Mother ISCED",
    "V004RF": "Highest educational level attained - Respondent’s Father (Recoded)",
    "V004RM": "Highest educational level attained - Respondent’s Mother (Recoded)",
    "V097EF": "Respondent’s Father - Occupational group (when respondent was 14 years old)",
    "W002A_01": "Highest educational level attained - Respondent’s Spouse ISCED",
    "W002D": "Country specific: Education level partner",
    "W002R": "Educational level partner (recoded)",
    "W003": "Employment status - Respondent’s Spouse",
    "W006E": "Respondent’s Spouse - Occupational group (WVS)",
    "X001": "Sex",
    "X002": "Year of birth",
    "X002_02A": "Respondents country of birth - ISO 3166-1 code",
    "X003": "Age",
    "X003R": "Age recoded (6 intervals)",
    "X003R2": "Age recoded (3 intervals)",
    "X007": "Marital status",
    "X008": "Have you been married before",
    "X010": "Where respondent lived after married",
    "X011": "How many children do you have",
    "X011A": "Have you had any children",
    "X012": "How many are still living at home",
    "X013": "Number of people in household",
    "X023": "What age did you complete your education",
    "X023R": "What age did you complete your education (recoded in intervals)",
    "X024B": "Respondent - literate",
    "X025": "Highest educational level attained",
    "X025A_01": "Highest educational level attained - Respondent ISCED-2011",
    "X025CSWVS": "Education (country specific)",
    "X025LIT": "Was the respondent literate",
    "X025R": "Education level (recoded)",
    "X026": "Do you live with your parents",
    "X028": "Employment status",
    "X031": "Are you supervising someone",
    "X036": "Profession/job",
    "X036E": "Respondent - Occupational group (WVS)",
    "X040": "Are you the chief wage earner in your house",
    "X041": "Is the chief wage earner employed now",
    "X043": "Chief wage earner profession/job",
    "X044": "Family savings during past year",
    "X045": "Social class (subjective)",
    "X045B": "Social class (subjective) with 6 categories",
    "X047_WVS": "Scale of incomes",
    "X047CS": "Scale of incomes (Country specific)",
    "X047R_WVS": "Subjective income level (recoded in 3 groups)",
    "X048ISO": "Region ISO 3166-2",
    "X048WVS": "Region where the interview was conducted (WVS)",
    "X049": "Settlement size",
    "X049CS": "Settlement size (country specific)",
    "X050": "Type of habitat",
    "X050B": "Settlement type where interview was conducted",
    "X050C": "Urban/Rural habitat",
    "X051": "Ethnic group",
    "X052": "Institution of occupation",
    "X053": "Nature of tasks: manual vs. Cognitive",
    "X054": "Nature of tasks: routine vs. Creative",
    "X055": "Nature of tasks: independence",
    "Y001": "Post-Materialist index 12-item",
    "Y002": "Post-Materialist index 4-item",
    "Y003": "Autonomy Index",
    "Y010": "SACSECVAL.- Welzel Overall Secular Values",
    "Y011": "DEFIANCE.- Welzel defiance sub-index",
    "Y012": "DISBELIEF.- Welzel disbelief sub-index",
    "Y013": "RELATIVISM.- Welzel relativism",
    "Y014": "SCEPTICISM.- Welzel scepticism index",
    "Y020": "RESEMAVAL.- Welzel emancipative values",
    "Y021": "AUTONOMY.- Wezel Autonomy subindex",
    "Y022": "EQUALITY.- Welzel equality sub-index",
    "Y023": "CHOICE.- Welzel choice sub-index",
    "Y024": "VOICE.- Welzel voice sub-index",
    "Y011A": "AUTHORITY - Welzel defiance - 1: Inverse respect for authority",
    "Y011B": "NATIONALISM - Welzel defiance - 2: Inverse national pride",
    "Y011C": "DEVOUT- Welzel defiance - 3: Inverse devoutness",
    "Y012A": "RELIGIMP - Welzel disbelief- 1: Inverse importance of religion",
    "Y012B": "RELIGBEL - Welzel disbelief- 2: Inverse religious person",
    "Y012C": "RELIGPRAC - Welzel disbelief- 3: Inverse religious practice",
    "Y013A": "NORM1 - Welzel relativism- 1: Inverse norm conform1",
    "Y013B": "NORM2 - Welzel relativism- 2: Inverse norm conform2",
    "Y013C": "NORM3 - Welzel relativism- 3: Inverse norm conform3",
    "Y014A": "TRUSTARMY- Welzel scepticism- 1: Inverse trust in army",
    "Y014B": "TRUSTPOLICE- Welzel scepticism- 2: Inverse trust in police",
    "Y014C": "TRUSTCOURTS- Welzel scepticism- 3: Inverse trust in courts",
    "Y021A": "INDEP- Welzel autonomy-1: Independence as kid quality",
    "Y021B": "IMAGIN- Welzel autonomy-2: Imagination as kid quality",
    "Y021C": "NONOBED- Welzel autonomy-3: Obedience as kid quality",
    "Y022A": "WOMJOB- Welzel equality-1: Gender equality: job",
    "Y022B": "WOMPOL- Welzel equality-2: Gender equality: politics",
    "Y022C": "WOMEDU- Welzel equality-3: Gender equality: education",
    "Y023A": "HOMOLIB- Welzel choice-1: Homosexuality acceptance",
    "Y023B": "ABORTLIB- Welzel choice-2: Abortion acceptable",
    "Y023C": "DIVORLIB- Welzel choice-3: Divorce acceptable",
    "Y024A": "VOICE1- Welzel voice-1",
    "Y024B": "VOICE2- Welzel voice-2",
    "Y024C": "VOI2_00- Welzel voice-3 (auxiliary)",
    "E026": "Political action: joining in boycotts",
    "E026B": "Political action recently done: joining in boycotts",
    "E027": "Political action: attending lawful/peaceful demonstrations",
    "E028": "Political action: joining unofficial strikes",
    "E028B": "Political action recently done: Joining strikes",
    "E029": "Political action: occupying buildings or factories",
    "E032": "Freedom or equality",
    "E033": "Self positioning in political scale",
    "E034": "Basic kinds of attitudes concerning society",
    "E035": "Income equality",
    "E036": "Private vs state ownership of business",
    "E037": "Government responsibility",
    "E038": "Job taking of the unemployed",
    "E039": "Competition good or harmful",
    "E040": "Hard work brings success",
    "E041": "Wealth accumulation",
    "E044": "Major changes in life",
    "E045": "New and old ideas",
    "E047": "Personal characteristics: Changes, worry or welcome possibility",
    "E048": "Personal characteristics: I usually count on being successful in everything I do",
    "E049": "Personal characteristics: I enjoy convincing others of my opinion",
    "E050": "Personal characteristics: I serve as a model for others",
    "E051": "Personal characteristics: I am good at getting what I want",
    "E052": "Personal characteristics: I own many things others envy me for",
    "E053": "Personal characteristics: I like to assume responsibility",
    "E054": "Personal characteristics: I am rarely unsure about how I should behave",
    "E055": "Personal characteristics: I often give others advice",
    "E056": "Personal characteristics: None of the above",
    "E057": "The economic system needs fundamental changes",
    "E058": "Our government should be made much more open to the public",
    "E059": "Allow more freedom for individuals",
    "E060": "I could do nothing about an unjust law",
    "E061": "Political reform is moving too rapidly",
    "E062": "Importation of goods",
    "E063": "Current society: Egalitarian vs. competitive society",
    "E064": "Current society: Extensive welfare vs. low taxes",
    "E065": "Current society: Regulated vs. responsible society",
    "E066": "Society aimed: egalitarian vs. competitive",
    "E067": "Society aimed: extensive welfare vs. low taxes",
    "E069_01": "Confidence: Churches",
    "E069_02": "Confidence: Armed Forces",
    "E069_03": "Confidence: Education System",
    "E069_04": "Confidence: The Press",
    "E069_05": "Confidence: Labour Unions",
    "E069_06": "Confidence: The Police",
    "E069_07": "Confidence: Parliament",
    "E069_08": "Confidence: The Civil Services",
    "E069_09": "Confidence: Social Security System",
    "E069_10": "Confidence: Television",
    "E069_11": "Confidence: The Government",
    "E069_12": "Confidence: The Political Parties",
    "E069_13": "Confidence: Major Companies",
    "E069_14": "Confidence: The Environmental Protection Movement",
    "E069_15": "Confidence: The Women’s Movement",
    "E069_16": "Confidence: The Justice System/Courts",
    "E069_17": "Confidence: The European Union",
    "E069_18A": "Confidence: Major regional organization (combined from country-specific)",
    "E069_19": "Confidence: NATO",
    "E069_20": "Confidence: The United Nations",
    "E069_21": "Confidence: The Arab League",
    "E069_22": "Confidence: The Association of South East Asian Nations - ASEAN",
    "E069_23": "Confidence: The Organization for African Unity - OAU",
    "E069_24": "Confidence: The NAFTA",
    "E069_25": "Confidence: The Andean pact",
    "E069_26": "Confidence: The Mercosur",
    "E069_27": "Confidence: The SAARC",
    "E069_28": "Confidence: The ECO",
    "E069_29": "Confidence: The APEC",
    "E069_30": "Confidence: The Free Commerce Treaty (Tratado de libre comercio)",
    "E069_31": "Confidence: The United American States Organization (Organización de Estados Americanos)",
    "E069_32": "Confidence: The “Movimiento en pro de Vieques” (Puerto Rico)",
    "E069_33": "Confidence: Local/Regional Government",
    "E069_34": "Confidence: SADC/SADEC",
    "E069_35": "Confidence: East African Cooperation (EAC)",
    "E069_36": "Confidence: The Presidency",
    "E069_37": "Confidence: The Civil Society Groups",
    "E069_38": "Confidence: Charitable or humanitarian organizations",
    "E069_39": "Confidence: Banks",
    "E069_42": "Confidence: CARICOM",
    "D081": "Homosexual couples are as good parents as other couples",
    "E001": "Aims of country: first choice",
    "E002": "Aims of country: second choice",
    "E003": "Aims of respondent: first choice",
    "E004": "Aims of respondent: second choice",
    "E005": "Most important: first choice",
    "E006": "Most important: second choice",
    "E007": "National goals: Maintaining order in the nation",
    "E008": "National goals: Giving people more say",
    "E009": "National goals: Fighting rising prices",
    "E010": "National goals: free speech",
    "E012": "Willingness to fight for country",
    "E014": "Future changes: Less emphasis on money and material possessions",
    "E015": "Future changes: Less importance placed on work",
    "E016": "Future changes: More emphasis on technology",
    "E017": "Future changes: More emphasis on individual",
    "E018": "Future changes: Greater respect for authority",
    "E019": "Future changes: More emphasis on family life",
    "E020": "Future changes: A simple and more natural lifestyle",
    "E021": "Opinion about scientific advances",
    "E069_42": "Confidence: CARICOM",
    "E069_43": "Confidence: CIS",
    "E069_44": "Confidence: Confidence in CER with Australia",
    "E069_45": "Confidence: International Monetary Fund (IMF)",
    "E069_46": "Confidence: Non-governmental Organizations (NGOs)",
    "E069_47": "Confidence: The American Forces",
    "E069_48": "Confidence: The non-Iraqi television",
    "E069_49": "Confidence: TV News",
    "E069_50": "Confidence: Religious leaders",
    "E069_52": "Confidence: Evangelic Church",
    "E069_54": "Confidence: Universities",
    "E069_55": "Confidence: The Organization of the Islamic World",
    "E069_56": "Confidence: The Organization of American States (OAE)",
    "E069_57": "Confidence: UNASUR",
    "E069_58": "Confidence: The Arab Maghreb Union",
    "E069_59": "Confidence: Cooperation Council for the Arab states of Gulf (GCC)",
    "E069_60": "Confidence: Mainland government",
    "E069_61": "Confidence: The World Trade Organization (WTO)",
    "E069_62": "Confidence: The World Health Organization (WHO)",
    "E069_63": "Confidence: The World Bank",
    "E069_64": "Confidence: Elections",
    "E069_65": "Confidence: International Criminal Court (ICC)",
    "E069_66": "Confidence: UNDP United Nations Development Programme",
    "E069_67": "Confidence: The African Union (AU)",
    "E104": "Approval: Ecology movement or nature protection",
    "E105": "Approval: Anti-nuclear energy movement",
    "E106": "Approval: Disarmament movement",
    "E107": "Approval: Human rights movement",
    "E108": "Approval: Women’s movement",
    "E109": "Approval: Anti-apartheid movement",
    "E110": "Satisfaction with the way democracy develops",
    "E111": "Rate political system for governing country",
    "E112": "Rate political system as it was before",
    "E113": "Rate political system in ten years",
    "E114": "Political system: Having a strong leader",
    "E115": "Political system: Having experts make decisions",
    "E116": "Political system: Having the army rule",
    "E117": "Political system: Having a democratic political system",
    "E118": "Political system: Having a system governed by religious law in which there are no political parties",
    "E119": "Firm party leader vs. Cooperating party leader",
    "E120": "Government or freedom",
    "E121": "In democracy, the economic system runs badly",
    "E122": "Democracies aren’t good at maintaining order",
    "E123": "Democracy may have problems but is better",
    "E124": "Respect for individual human rights nowadays",
    "E125": "Satisfaction with the people in national office",
    "E127": "Free market economy right for country future",
    "E128": "Country is run by big interest vs. for all people’s benefit",
    "E129": "Economic aid to poorer countries",
    "E129A": "Amount of foreign aid of this country",
    "E129B": "How much more foreign aid this country should contribute",
    "E129C": "Be willing to pay higher taxes in order to increase country’s foreign aid",
    "E129D": "Economic aid to poorer countries (favor/against)",
    "E130": "Poverty compared to 10 years ago",
    "E131": "Why are people in need",
    "E132": "Chance to escape from poverty",
    "E133": "How much is the government doing against poverty",
    "E134": "Amount of help for less developed countries",
    "E135": "Who should decide: international peacekeeping",
    "E136": "Who should decide: protection of the environment",
    "E137": "Who should decide: aid to developing countries",
    "E138": "Who should decide: refugees",
    "E139": "Who should decide: human rights",
    "E140": "Country cannot solve environmental problems by itself",
    "E141": "Country cannot solve crime problems by itself",
    "E142": "Country cannot solve employment problems by itself",
    "E143": "Immigrant policy",
    "E150": "How often follows politics in the news",
    "E184": "Aggression from neighbouring country",
    "E185": "Exploitation of local resources",
    "E186": "Cultural invasion by the west",
    "E188": "Frequency watches TV",
    "E189": "TV most important entertainment",
    "E190": "Why are there people living in need: first",
    "E191": "Why are there people living in need: second",
    "E192": "Least liked group in society",
    "E193": "Least liked allow: hold office",
    "E194": "Least liked allow: teach",
    "E195": "Least liked allow: demonstrate",
    "E196": "Extent of political corruption",
    "E198": "Using violence for political goals not justified",
    "E203": "Rapid implementation of market reforms have negative impact on national economy",
    "E204": "Effect of market economic reforms",
    "E205": "Political parties serve the social and political needs of people",
    "E206": "Free and fair elections will reduce terrorism",
    "E207": "[Country] should have close relations with France",
    "E208": "[Country] should have close relations with United States",
    "E209": "Would persist to immigrate abroad if R’s economic situation was better",
    "E211": "Opinion about the problem of Palestine and Israel",
    "E212": "Opinion about 11th September airliners crash action by religious fundamentalists",
    "E213": "Woman should not work outside unless forced to do so",
    "E214": "Western democracy is the best political system for country",
    "E215": "It is necessary to fight terrorism by military means",
    "E216": "[Country] needs foreign military cooperation to combat terrorism",
    "E217": "Science and technology are making our lives healthier, easier, and more comfortable",
    "E218": "Because of science and technology, there will be more opportunities for the next generation",
    "E219": "Science and technology make our way of life change too fast",
    "E220": "We depend too much on science and not enough on faith",
    "E221B": "Political action recently done: Attending peaceful/lawful demonstrations",
    "E222": "Political action: Other",
    "E222B": "Political action recently done: Other",
    "E224": "Democracy: Governments tax the rich and subsidize the poor",
    "E225": "Democracy: Religious authorities interpret the laws",
    "E226": "Democracy: People choose their leaders in free elections",
    "E227": "Democracy: People receive state aid for unemployment",
    "E228": "Democracy: The army takes over when government is incompetent",
    "E229": "Democracy: Civil rights protect people’s liberty against oppression",
    "E230": "Democracy: The economy is prospering",
    "E231": "Democracy: Criminals are severely punished",
    "E232": "Democracy: People can change the laws in referendums",
    "E233": "Democracy: Women have the same rights as men",
    "E233A": "Democracy: The state makes people’s incomes equal",
    "E233B": "Democracy: People obey their rulers",
    "E234": "The world is better off, or worse off, because of science and technology",
    "E235": "Importance of democracy",
    "E236": "Democraticness in own country",
    "E237": "Heard of the Millennium Development Goals",
    "E238": "Most serious problem of the world: 1st choice",
    "E239": "Most serious problem of the world: 2nd choice",
    "E240": "Most serious problem for own country: 1st choice",
    "E241": "Most serious problem for own country: 2nd choice",
    "E242": "MDG: Reduce extreme poverty",
    "E243": "MDG: Increase primary education",
    "E244": "MDG: Reduce child mortality",
    "E245": "MDG: Fight HIV",
    "E246": "MDG: Improve housing conditions",
    "E247": "Priority: Global poverty versus National problems",
    "E248": "Information source: Daily newspaper",
    "E248B": "Information source: Daily newspaper (B)",
    "E249": "Information source: News broadcasts on radio or TV",
    "E250": "Information source: Printed magazines",
    "E250B": "Information source: Printed magazines (B)",
    "E251": "Information source: In-depth reports on radio or TV",
    "E252": "Information source: Books",
    "E253": "Information source: Internet, Email",
    "E253B": "Information source: Social media (Facebook, Twitter, etc.)",
    "E254": "Information source: Talk with friends or colleagues",
    "E254B": "Information source: Talk with friends or colleagues (B)",
    "E255": "How often use of PC",
    "E257": "Voted in recent parliament elections",
    "E258": "Information source: TV news",
    "E258B": "Information source: TV news (B)",
    "E259": "Information source: Radio news",
    "E259B": "Information source: Radio news (B)",
    "E260": "Information source: Mobile phone",
    "E260B": "Information source: Mobile phone (B)",
    "E261": "Information source: Email",
    "E261B": "Information source: Email (B)",
    "E262": "Information source: Internet",
    "E262B": "Information source: Internet (B)",
    "E263": "Vote in elections: local level",
    "E264": "Vote in elections: National level",
    "E265_01": "How often in country's elections: Votes are counted fairly",
    "E265_02": "How often in country's elections: Opposition candidates are prevented from running",
    "E265_03": "How often in country's elections: TV news favors the governing party",
    "E265_04": "How often in country's elections: Voters are bribed",
    "E265_05": "How often in country's elections: Journalists provide fair coverage of elections",
    "E265_06": "How often in country's elections: Election officials are fair",
    "E265_07": "How often in country's elections: Rich people buy elections",
    "E265_08": "How often in country's elections: Voters are threatened with violence at the polls",
    "E265_09": "How often in country's elections: Voters are offered a genuine choice in the elections",
    "E265_10": "How often in country's elections: Women have equal opportunities to run the election",
    "E266": "Some people think that having honest elections makes a lot of difference in who governs this country; others think that it doesn’t make much difference",
    "E267": "Importance of having honest elections in whether or not this country develops",
    "E268": "Scale corruption in [my country] - pay a bribe, give a gift, do a favor to other",
    "E270": "Groups of people involved in corruption: State authorities",
    "E271": "Groups of people involved in corruption: Local authorities",
    "E272": "Groups of people involved in corruption: Civil service providers (police, judiciary, etc.)",
    "E273": "Groups of people involved in corruption: Journalists and media",
    "E274": "Frequency ordinary people pay a bribe, give a gift, or do a favor to local officials",
    "E275": "Degree of agreement: On the whole, women are less corrupt than men",
    "E276": "Risk in this country to be held accountable for giving or receiving a bribe, gift, or doing a favor to a local official",
    "E277": "Standard of living comparing with your parents",
    "E278": "Should international organizations prioritize, being effective or being democratic?",
    "E289": "Social activism: Encouraging others to vote",
    "E290": "Justifiable: Political violence",
    "E279": "Five countries have permanent seats on the Security Council of the United Nations",
    "E280": "Where are the headquarters of the International Monetary Fund (IMF) located?",
    "E281": "Which of the following problems does the organization Amnesty International address?",
    "E282": "Political actions using Internet: Searching information about politics and political issues",
    "E283": "Political actions using Internet: Signing an electronic petition",
    "E284": "Political actions using Internet: Encouraging other people to take any form of online activism",
    "E285": "Political actions using Internet: Organizing political activities, events, protests, or campaigns",
    "E286": "Social activism: Donating to a group or campaign",
    "E287": "Social activism: Contacting a government official",
    "E288": "Social activism: Encouraging others to take action about political issues",
    "F001": "Thinking about meaning and purpose of life",
    "F003": "Thinking about death",
    "F004": "Life is meaningful because God exists",
    "F005": "Try to get the best out of life",
    "F006": "Death is inevitable",
    "F007": "Death has meaning if you believe in God",
    "F008": "Death is a natural resting point",
    "F009": "Sorrow has meaning if you believe in God",
    "F010": "Life has no meaning",
    "F022": "Statement: good and evil",
    "F024": "Belong to religious denomination",
    "F025": "Religious denominations - major groups",
    "F027": "Which former religious denomination",
    "F028": "How often do you attend religious services",
    "F028B": "How often do you pray",
    "F029": "Raised religiously",
    "F031": "Important: Religious service birth",
    "F032": "Important: Religious service marriage",
    "F033": "Important: Religious service death",
    "F034": "Religious person",
    "F035": "Churches give answers: moral problems",
    "F037": "Thinking about the nature of the universe",
    "F038": "Respect for parents",
    "F039": "Try to make own mind about religion",
    "F040": "Prefer to work together rather than individually",
    "F041": "Consider myself more a citizen of the world",
    "F042": "Pride in own nationality",
    "F043": "National pride in scientific achievements",
    "F044": "National pride in political influence",
    "F045": "National pride in military achievements",
    "F046": "National pride in history",
    "F047": "National pride in arts and literature",
    "F048": "National pride in sports achievements",
    "F049": "National pride in economy",
    "F050": "National pride in democracy",
    "F051": "National pride in social security system",
    "F052": "National pride in welfare system",
    "F053": "National pride in natural environment",
    "F054": "National pride in fair treatment of all groups in society",
    "F055": "National pride in equal rights",
    "F056": "National pride in equality of opportunity",
    "F057": "National pride in economic equality",
    "F058": "Importance of God in your life",
    "F059": "Importance of friends in your life",
    "F060": "Importance of family in your life",
    "G017": "Born in this country: birth country",
    "G018": "When came to country",
    "G019": "I see myself as a world citizen",
    "G020": "I see myself as member of my local community",
    "G021": "I see myself as citizen of the [country] nation",
    "G022A": "I see myself as citizen of [Latin America]",
    "G022B": "I see myself as citizen of [North America]",
    "G022C": "I see myself as citizen of the [European Union]",
    "G022D": "I see myself as citizen of [APEC]",
    "G022E": "I see myself as citizen of [ASIA]",
    "G022F": "I see myself as citizen of [Mercosur]",
    "G022G": "I see myself as citizen of [my province or region]",
    "G022H": "I see myself as citizen of [a country other than mine]",
    "G022I": "I see myself as citizen of [CIS]",
    "G022J": "I see myself as citizen of [The Caribbean]",
    "G022K": "I see myself as citizen of [The African Union]",
    "G022L": "I see myself as citizen of [Arab Maghreb Union]",
    "G022M": "I see myself as citizen of [ASEAN]",
    "G022N": "I see myself as citizen of [Arab Union]",
    "G022O": "I see myself as citizen of the [Northeast Asia Region]",
    "G022P": "I see myself as citizen of the [UNASUR]",
    "G022Q": "I see myself as citizen of the [Islamic nation]",
    "G022R": "I see myself as part of the Cooperation Council for the Arab states of Gulf (GCC)",
    "G023": "I see myself as an autonomous individual",
    "G024": "What thing are you proud of in your country - 1st",
    "G025": "What thing are you proud of in your country - 2nd",
    "G026": "Mother immigrant",
    "G027": "Father immigrant",
    "G027A": "Respondent immigrant",
    "G027B": "Respondent citizen",
    "G028": "Requirements for citizenship: having ancestors from my country",
    "G029": "Requirements for citizenship: being born on my country’s soil",
    "G030": "Requirements for citizenship: adopting the customs of my country",
    "G031": "Requirements for citizenship: abiding by my country’s laws",
    "G032": "Ethnic diversity",
    "G052": "Evaluate the impact of immigrants on the development of [your country]",
    "G053": "Effects of immigrants on the development of [your country]: Fill useful jobs that other people can’t",
    "G054": "Effects of immigrants on the development of [your country]: Strengthen cultural diversity",
    "G055": "Effects of immigrants on the development of [your country]: Increase the crime rate",
    "G056": "Effects of immigrants on the development of [your country]: Give asylum to people who need it",
    "G057": "Effects of immigrants on the development of [your country]: Increase the risk of terrorism",
    "G058": "Effects of immigrants on the development of [your country]: Help poor people improve their lives",
    "G059": "Effects of immigrants on the development of [your country]: Increase unemployment",
    "G060": "Effects of immigrants on the development of [your country]: Lead to social conflict",
    "G061": "People from other countries coming here to work - Which of the following types of workers do you prefer to come?",
    "G062": "How close you feel: Continent (e.g., Europe, Asia, etc.)",
    "G063": "How close you feel: World",
    "G255": "How close you feel: Your [village, town or city]",
    "H001": "Secure in neighborhood",
    "H002_01": "Frequency in your neighborhood: Robberies",
    "H002_02": "Frequency in your neighborhood: Alcohol consumed in the streets",
    "H002_03": "Frequency in your neighborhood: Police or military interfere with people’s privacy",
    "H002_04": "Frequency in your neighborhood: Racist behavior",
    "H002_05": "Frequency in your neighborhood: Drug sale in streets",
    "H003_01": "Things done for reasons of security: Didn’t carry much money",
    "H003_02": "Things done for reasons of security: Preferred not to go out at night",
    "H003_03": "Things done for reasons of security: Carried a knife, gun, or other weapon",
    "H004": "Respondent was victim of a crime during the past year",
    "H005": "Respondent’s family was victim of a crime during last year",
    "H006_01": "Worries: Losing my job or not finding a job",
    "H006_02": "Worries: Not being able to give one’s children a good education",
    "H006_03": "Worries: A war involving my country",
    "H006_04": "Worries: A terrorist attack",
    "H006_05": "Worries: A civil war",
    "H006_06": "Worries: Government wire-tapping or reading my mail or email",
    "H007": "Under some conditions, war is necessary to obtain justice",
    "H008_01": "Frequency you/family (last 12 months): Gone without enough food to eat",
    "H008_02": "Frequency you/family (last 12 months): Felt unsafe from crime in your own home",
    "H008_03": "Frequency you/family (last 12 months): Gone without needed medicine or treatment",
    "H008_04": "Frequency you/family (last 12 months): Gone without a cash income",
    "H008_05": "How frequently do the following things occur in your neighborhood: Street harassment",
    "H008_06": "How frequently do the following things occur in your neighborhood: Sexual harassment",
    "H008_07": "Freedom and Equality - Which more important",
    "H008_08": "Freedom and security - Which more important",
    "H008_09": "In the last 12 months, how often have you or your family: Gone without a safe place to stay",
    "H009": "Government has the right: Keep people under video surveillance in public areas",
    "H010": "Government has the right: Monitor all e-mails and any other information exchanged on the internet",
    "H011": "Government has the right: Collect information about anyone living in [COUNTRY] without their knowledge",
    "I002": "One of the bad effects of science is that it breaks down people’s ideas of right and wrong",
    "I002B": "It is not important for me to know about science in my daily life"
}

# Rename columns using the mapping
agents_df = agents_df.rename(columns=column_mapping)

# Read in the Codebook Mapping from question names to labels
column_mapping_df = pd.read_csv(column_mappings_path, encoding='latin1')

# Create a dictionary from the "VARIABLE" and "LABEL" columns
column_mapping = column_mapping_df.set_index('VARIABLE')['LABEL'].to_dict()

# Rename columns using the mapping
agents_df = agents_df.rename(columns=column_mapping)

# Create the code-to-country name mapping dictionary
iso31661_code_to_country = {
    8: 'Albania', 12: 'Algeria', 20: 'Andorra', 31: 'Azerbaijan', 32: 'Argentina', 36: 'Australia', 40: 'Austria',
    50: 'Bangladesh', 51: 'Armenia', 56: 'Belgium', 68: 'Bolivia', 70: 'Bosnia and Herzegovina', 76: 'Brazil',
    100: 'Bulgaria', 104: 'Myanmar', 112: 'Belarus', 124: 'Canada', 152: 'Chile', 156: 'China', 158: 'Taiwan ROC',
    170: 'Colombia', 191: 'Croatia', 196: 'Cyprus', 197: 'Northern Cyprus', 203: 'Czech Republic', 208: 'Denmark',
    214: 'Dominican Rep', 218: 'Ecuador', 222: 'El Salvador', 231: 'Ethiopia', 233: 'Estonia', 246: 'Finland',
    250: 'France', 268: 'Georgia', 275: 'Palestine', 276: 'Germany', 288: 'Ghana', 300: 'Greece', 320: 'Guatemala',
    332: 'Haiti', 344: 'Hong Kong SAR', 348: 'Hungary', 352: 'Iceland', 356: 'India', 360: 'Indonesia', 364: 'Iran',
    368: 'Iraq', 372: 'Ireland', 376: 'Israel', 380: 'Italy', 392: 'Japan', 398: 'Kazakhstan', 400: 'Jordan',
    410: 'South Korea', 414: 'Kuwait', 417: 'Kyrgyzstan', 422: 'Lebanon', 428: 'Latvia', 434: 'Libya', 440: 'Lithuania',
    442: 'Luxembourg', 446: 'Macau SAR', 458: 'Malaysia', 466: 'Mali', 470: 'Malta', 484: 'Mexico', 498: 'Moldova',
    499: 'Montenegro', 504: 'Morocco', 528: 'Netherlands', 554: 'New Zealand', 558: 'Nicaragua', 566: 'Nigeria',
    578: 'Norway', 586: 'Pakistan', 604: 'Peru', 608: 'Philippines', 616: 'Poland', 620: 'Portugal', 630: 'Puerto Rico',
    634: 'Qatar', 642: 'Romania', 643: 'Russia', 646: 'Rwanda', 682: 'Saudi Arabia', 688: 'Serbia', 702: 'Singapore',
    703: 'Slovakia', 704: 'Vietnam', 705: 'Slovenia', 710: 'South Africa', 716: 'Zimbabwe', 724: 'Spain', 752: 'Sweden',
    756: 'Switzerland', 762: 'Tajikistan', 764: 'Thailand', 780: 'Trinidad and Tobago', 788: 'Tunisia', 792: 'Turkey',
    800: 'Uganda', 804: 'Ukraine', 807: 'North Macedonia', 818: 'Egypt', 826: 'Great Britain', 834: 'Tanzania',
    840: 'United States', 854: 'Burkina Faso', 858: 'Uruguay', 860: 'Uzbekistan', 862: 'Venezuela', 887: 'Yemen',
    894: 'Zambia', 909: 'Northern Ireland', 915: 'Kosovo', 'a': "Don't know", 'b': 'No answer', 'c': 'Not applicable',
    'd': 'Not asked in survey', 'e': 'Missing: other', -1: "Missing: NaN or None/Empty"
}

# Invert the dictionary to map country names to their codes (OPTIONAL)
iso31661_country_to_code = {v: k for k, v in iso31661_code_to_country.items()}

# Dictionary for code-to-country name mappings
cow_code_to_country = {
    2: "United States", 6: "Puerto Rico", 20: "Canada", 41: "Haiti", 42: "Dominican Republic",
    52: "Trinidad and Tobago", 70: "Mexico", 90: "Guatemala", 92: "El Salvador", 93: "Nicaragua",
    100: "Colombia", 101: "Venezuela", 130: "Ecuador", 135: "Peru", 140: "Brazil",
    145: "Bolivia", 155: "Chile", 160: "Argentina", 165: "Uruguay", 200: "United Kingdom",
    201: "Great Britain", 202: "Northern Ireland", 205: "Ireland", 210: "Netherlands",
    211: "Belgium", 212: "Luxembourg", 220: "France", 225: "Switzerland", 230: "Spain",
    232: "Andorra", 235: "Portugal", 255: "Germany", 260: "German Federal Republic",
    290: "Poland", 305: "Austria", 310: "Hungary", 316: "Czech Republic", 317: "Slovakia",
    325: "Italy", 338: "Malta", 339: "Albania", 341: "Montenegro", 343: "Macedonia",
    344: "Croatia", 345: "Yugoslavia", 346: "Bosnia and Herzegovina", 347: "Kosovo",
    348: "Serbia", 349: "Slovenia", 350: "Greece", 352: "Cyprus", 353: "Northern Cyprus",
    355: "Bulgaria", 359: "Moldova", 360: "Romania", 365: "Russia", 366: "Estonia",
    367: "Latvia", 368: "Lithuania", 369: "Ukraine", 370: "Belarus", 371: "Armenia",
    372: "Georgia", 373: "Azerbaijan", 375: "Finland", 380: "Sweden", 385: "Norway",
    390: "Denmark", 395: "Iceland", 432: "Mali", 439: "Burkina Faso", 446: "Macau SAR",
    452: "Ghana", 475: "Nigeria", 500: "Uganda", 510: "Tanzania", 517: "Rwanda",
    530: "Ethiopia", 551: "Zambia", 552: "Zimbabwe", 560: "South Africa", 600: "Morocco",
    615: "Algeria", 616: "Tunisia", 620: "Libya", 630: "Iran", 640: "Turkey", 645: "Iraq",
    651: "Egypt", 660: "Lebanon", 663: "Jordan", 666: "Israel", 667: "Palestine",
    670: "Saudi Arabia", 679: "Yemen", 690: "Kuwait", 694: "Qatar", 702: "Tajikistan",
    703: "Kyrgyzstan", 704: "Uzbekistan", 705: "Kazakhstan", 710: "China", 713: "Taiwan ROC",
    714: "Hong Kong SAR", 732: "South Korea", 740: "Japan", 750: "India", 770: "Pakistan",
    771: "Bangladesh", 775: "Myanmar", 800: "Thailand", 816: "Vietnam", 820: "Malaysia",
    830: "Singapore", 840: "Philippines", 850: "Indonesia", 900: "Australia", 920: "New Zealand",
    "a": "Don't know", "b": "No answer", "c": "Not applicable", "d": "Not asked in survey", "e": "Missing: other",
    -1: "Missing: NaN or None/Empty"
}

# Invert the dictionary to map country names back to their numeric codes (OPTIONAL)
cow_country_to_code = {v: k for k, v in cow_code_to_country.items()}

# If numeric code is actually already country name then convert back to code then proceed..
agents_df['ISO 3166-1 numeric country code'] = agents_df['ISO 3166-1 numeric country code'].map(iso31661_country_to_code)
agents_df['CoW country code numeric'] = agents_df['CoW country code numeric'].map(cow_country_to_code)

# Convert the columns of interest to integer type
agents_df['ISO 3166-1 numeric country code'] = agents_df['ISO 3166-1 numeric country code'].fillna(-1) # But first... fill non-finite values with a placeholder (e.g., -1)
agents_df['CoW country code numeric'] = agents_df['CoW country code numeric'].fillna(-1)
agents_df['ISO 3166-1 numeric country code'] = agents_df['ISO 3166-1 numeric country code'].astype(int)
agents_df['CoW country code numeric'] = agents_df['CoW country code numeric'].astype(int)

# Create the 'country_name' column by combining the mappings
agents_df['country_name'] = agents_df['ISO 3166-1 numeric country code'].map(iso31661_code_to_country).combine_first(agents_df['CoW country code numeric'].map(cow_code_to_country)).fillna("Undefined")

# Applying "optimise_dataframe"  to agents_df to reduce memory usage of the dataset before writing to file/analysis
#agents_df = optimize_dataframe(agents_df)

# Save the result to csv file (OPTIONAL)
agents_df.to_csv("/Users/stevenbickley/stevejbickley/data_assorted/" + str(extract_filename(original_data_path)) + "_columns_renamed.csv",index=False,encoding='utf-8')

# Now read in the xlsx or csv file:
# Note 1: agents_df.columns # View column names
# Note 2: agents_df.columns.tolist() # View column names for datasets with > 30 columns
try:
    agents_df = pd.read_excel("/Users/stevenbickley/stevejbickley/data_assorted/" + str(extract_filename(original_data_path)) + "_columns_renamed.xlsx")
except:
    agents_df = pd.read_csv("/Users/stevenbickley/stevejbickley/data_assorted/" + str(extract_filename(original_data_path)) + "_columns_renamed.csv")

# Display the first 5 rows of agents_df
#pd.set_option('display.max_columns', None)
#pd.set_option('display.width', 1000)
#agents_df.head()

# Select the columns of interest - for example, see e.g., Hughes, Camden, Yangchen & College (2016) and Fassett, Wolcott, Harpe, McLaughlin (2022):
# The "Core Set": Age, Gender Identity, Biological Sex, Ethnicity/Race, Education, Location/Geographic Data
# The "Wider Set": Political Preferences, Family and Dependents, Language Spoken, Religion and Spiritual Beliefs/Group Membership(s), Sexual Orientation, Disability Status, Employment Status, Industry/Type of Employment, Social/Socioeconomic Class (Current), Marital/Relationship Status, Household Income
# The "Extended Set": Parent/Guardian's Highest Level of Education, Parent/Guardian's Industry/Type of Employment, Respondent's Household Wealth/Socio-Economic Status Growing Up

# 1) Core Set
#columns_of_interest = ['Sex','Age','Ethnic group','Highest educational level attained','country_name']

# 2) Wider Set
columns_of_interest = ['Sex','Age','Ethnic group','Highest educational level attained','country_name','How many children do you have','Language of the interview','Employment status','Profession/job','Social class (subjective)','Marital status','Scale of incomes','Self positioning in political scale','Religious denominations - major groups'] # Wider Set
# We are missing 'Disability Status/Diagnosis' and 'Sexual Identity/Orientation' from the World Values Survey (i.e. they do not collect this) but thankfully.. we can add this via the SurveyLM platform - e.g.g 'Disability Status/Diagnosis' we could do: 'Physical Disability', 'Mental Disability', 'Neurodivergent', 'Both mental and physical disability', 'No mental or physical disability', 'Prefer not to answer'
# From Hughes, Camden, Yangchen & College (2016) for the 'Disability Status/Diagnosis' variable/column: 'No diagnosed disability or impairment','A  sensory impairment (vision or hearing)', 'A mobility impairment','A learning disability (e.g., ADHD, dyslexia)', 'A mental health disorder','A disability or impairment not listed above'
# OR... From Fassett, Wolcott, Harpe, McLaughlin (2022) for the 'Disability Status/Diagnosis' variable/column: 'Blind or low vision', 'Deaf or hard of hearing', 'Mobility condition that affects walking', 'Mobility condition that does not affect walking', 'Speech or communication disorder', 'Traumatic or acquired brain injury', 'Anxiety', 'Attention deficit or hyperactivity disorder (ADD or ADHD)', 'Autism spectrum', 'Depression', 'Another mental health or developmental disability (schizophrenia, eating disorder, etc.)', 'Chronic medical condition (asthma, diabetes, Crohn's disease, etc.)', 'Learning disability', 'Intellectual disability', 'Disability or condition not listed'
# From Hughes, Camden, Yangchen & College (2016) for the 'Sexual Identity/Orientation' variable/column: 'Heterosexual or straight','Gay or lesbian','Bisexual','Fluid','Pansexual','Queer','Demisexual','Questioning','Asexual','I prefer not to answer.'

# 3) Extended Set
#columns_of_interest = ['Sex','Age','Ethnic group','Highest educational level attained','country_name','How many children do you have','Language of the interview','Employment status','Profession/job','Social class (subjective)','Marital status','Scale of incomes','Self positioning in political scale','Religious denominations - major groups','Employment status - Respondent’s Spouse','Highest educational level attained - Respondent’s Father ISCED','Highest educational level attained - Respondent’s Mother ISCED','Respondent’s Father - Occupational group (when respondent was 14 years old)']
# From Hughes, Camden, Yangchen & College (2016) for the 'Socioeconomic class/situation during childhood' variable/column: 'Poor','Working Class','Middle Class','Affluent'
# From Fassett, Wolcott, Harpe, McLaughlin (2022) for the 'Family status/situation growing up' variable/column: 'Raised by married parents', 'Raised by foster parents','Raised by single parent','Raised by divorced parents'
# From Fassett, Wolcott, Harpe, McLaughlin (2022) for the 'Geographic region raised during childhood' variable/column: 'Rural','Suburb','Urban'

## ---- From 'WVS_TimeSeries_1981_2022_Stata_v3_0_some_columns_renamed.csv':

# --> The "Core Set": ['Sex','Age','Ethnic group','Highest educational level attained','country_name']
# Possible alternatives to 'Age' variable/column: 'Year of birth', 'Age recoded (6 intervals)', 'Age recoded (3 intervals)'
# Possible alternatives to 'Highest educational level attained' variable/column: 'Highest educational level attained - Respondent ISCED-2011','Education level (recoded)','What age did you complete your education','What age did you complete your education (recoded in intervals)'
# Possible alternatives to 'country_name' variable/column: 'ISO 3166-1 alpha-3 country code','CoW country code alpha','Region ISO 3166-2','Region where the interview was conducted (WVS)','Settlement size','Settlement type where interview was conducted','Urban/Rural habitat','Type of habitat'

# --> The "Wider Set": ['How many children do you have','Language of the interview','Employment status','Profession/job','Social class (subjective)','Marital status','Scale of incomes','Self positioning in political scale','Religious denominations - major groups']
# Note: we are missing/yet to add... --> sexual orientation, disability
# Possible alternatives to 'How many children do you have' variable/column: 'Have you had any children', 'How many are still living at home', 'Number of people in household'
# Possible alternatives to 'Language of the interview' variable/column: 'Language in which interview was conducted'
# Possible alternatives to 'Profession/job' variable/column: 'Respondent - Occupational group (WVS)', 'Chief wage earner profession/job'
# Possible alternatives to 'Social class (subjective)' variable/column: 'Social class (subjective) with 6 categories','Family savings during past year'
# Possible alternatives to 'Marital status' variable/column: 'Have you been married before'
# Possible alternatives to 'Scale of incomes' variable/column: 'Scale of incomes (Country specific)','Subjective income level (recoded in 3 groups)'
# Possible alternatives to 'Self positioning in political scale' variable/column: 'Political action: joining in boycotts','Political action recently done: joining in boycotts','Political action: attending lawful/peaceful demonstrations','Current society: Egalitarian vs. competitive society','Current society: Extensive welfare vs. low taxes','Current society: Regulated vs. responsible society','Society aimed: egalitarian vs. competitive','Society aimed: extensive welfare vs. low taxes'
# Possible alternatives to 'Religious denominations - major groups' variable/column: 'Belong to religious denomination', 'F025_WVS', 'Which former religious denomination', 'How often do you attend religious services', 'How often do you pray', 'Raised religiously','Important in life: Religion','Personal God vs. Spirit or Life Force','How important is God in your life','Get comfort and strength from religion','Neighbours: People of a different religion','Neighbours: People of the same religion','Sharing with partner: attitudes towards religion','Sharing with parents: attitudes towards religion','Moments of prayer, meditation...','Pray to God outside of religious services (I)','Pray to God outside of religious services (ii)','Politicians who don't believe in God are unfit for public office',''



# --> The "Extended Set": ['Employment status - Respondent’s Spouse','Highest educational level attained - Respondent’s Father ISCED','Highest educational level attained - Respondent’s Mother ISCED','Respondent’s Father - Occupational group (when respondent was 14 years old)']
# Note: we are missing/yet to add... --> Respondent's Wealth/Socio-Economic Status/Living Situation During Childhood
# Possible alternatives to 'Highest educational level attained - Respondent’s Father ISCED' variable/column: 'Highest educational level attained - Respondent’s Father (Recoded)'
# Possible alternatives to 'Highest educational level attained - Respondent’s Mother ISCED' variable/column: 'Highest educational level attained - Respondent’s Mother (Recoded)'
# Possible alternatives to 'XXXX' variable/column: 'XXXX', 'XXXX', 'XXXX', 'XXXX'

## ----

# For the other synthetic/real-world datasets:
# 'agents_output.xlsx' --> ['Age in years', 'Self-described gender', 'Highest level of education']
# 'CustomisedProfile_WVS_v2.xlsx' --> ['Sex (1=Male, 2=Female)', 'Age', 'Marital status (1=Married, 6=Single)']
# 'Integrated_values_surveys_1981-2021_decoded_dta2xlsx_python.csv' -->

# Generate the joint probability matrix
joint_prob_matrix = create_joint_probability_matrix(agents_df, columns_of_interest)
#joint_prob_matrix.index.nlevels
#joint_prob_matrix.columns.nlevels

# Now, generate a sample population of 100 agents based on this joint probability matrix
sample_population = generate_sample_population(joint_prob_matrix, 1000)

# Save the result to csv file (OPTIONAL)
sample_population.to_csv("/Users/stevenbickley/stevejbickley/data_assorted/" + str(extract_filename(original_data_path)) + "_samplePopulations_1k_world_sample.csv",index=False,encoding='utf-8')

# Or... Generate sample populations for each country iteratively
country_col = 'country_name' # 'ISO 3166-1 numeric country code'
sample_populations = generate_country_sample_populations(agents_df, country_col, columns_of_interest, 100)

# Convert the sample populations dictionary to a dataframe
sample_populations = convert_sample_populations_to_df(sample_populations)

# Save the result to csv file (OPTIONAL)
sample_populations.to_csv("/Users/stevenbickley/stevejbickley/data_assorted/" + str(extract_filename(original_data_path)) + "_samplePopulations_100_per_country_sample.csv",index=False,encoding='utf-8')

## ------ SECTION 3: Summary Statistics - Compare the distributions of the original vs synthetic populations' characteristics ------ ##

# Compare the distributions
def compare_distributions(original_data_path, column_names, sample_population):
    original_joint_prob_matrix = create_joint_probability_matrix(original_data_path, column_names)
    sample_joint_prob_matrix = create_joint_probability_matrix(sample_population, column_names)
    print("Original Joint Probability Matrix:")
    print(original_joint_prob_matrix)
    print("\nSample Joint Probability Matrix:")
    print(sample_joint_prob_matrix)
    # Add further comparison logic or statistical analysis here

# Example usage
compare_distributions(original_data_path, columns_of_interest, sample_population)
#compare_distributions(input_file_path, columns_of_interest, sample_population)

from scipy.stats import ks_2samp

# Kolmogorov-Smirnov Test (KS Test)
# --> Good for numerical data (preferred continuous but can do discrete)
def ks_test(original_data, synthetic_data, column_name):
    ks_statistic, p_value = ks_2samp(original_data[column_name], synthetic_data[column_name])
    return ks_statistic, p_value

# Example usage
ks_test(agents_df,sample_population,columns_of_interest)

from scipy.stats import chi2_contingency
import itertools

# Function to perform pairwise chi-squared tests for a set of variables, using Bonferroni correction to adjust the p-values
# --> Good for string or categorical distributions
def perform_pairwise_chi_squared_tests(original_data, new_data, column_names):
    results = {}
    # For Bonferroni correction, count all pairwise comparisons
    num_comparisons = len(column_names)
    alpha = 0.05 / num_comparisons  # Adjust alpha for multiple testing
    for column_name in column_names:
        # Create contingency table for each column
        original_freq = original_data[column_name].value_counts()
        new_freq = new_data[column_name].value_counts()
        # Make sure both Series have the same index for accurate comparison
        combined_index = original_freq.index.union(new_freq.index)
        original_freq = original_freq.reindex(combined_index, fill_value=0)
        new_freq = new_freq.reindex(combined_index, fill_value=0)
        contingency_table = pd.DataFrame({
            'original': original_freq,
            'new': new_freq
        })
        # Compute the chi-squared test
        chi2, p_value, _, _ = chi2_contingency(contingency_table)
        # Store results
        results[column_name] = {'chi2': chi2, 'p_value': p_value, 'significant': p_value < alpha}
    return results

perform_pairwise_chi_squared_tests(agents_df, sample_population, columns_of_interest)

##### ------ MAIN CODE - END ------- ####

