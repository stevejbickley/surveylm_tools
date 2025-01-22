##### ------ IMPORT FUNCTIONS + SETUP CODE - START ------- ####

from pydantic import BaseModel
import PyPDF2
from openai import OpenAI
#from enum import Enum
from typing import Optional
import fitz  # PyMuPDF
import io
import os
from PIL import Image
import base64
import json
import psycopg2 # (Optional)
import pandas as pd

### --- Planned Updates, Wish List, Random Thoughts/Ideas Log: --- ###


##### ------ DEFINE FUNCTIONS - START ------- ####

def extract_text_from_pdf(pdf_path, start_page=None, end_page=None):
    """
    Extract text from a PDF file along with page numbers.
    Parameters:
    - pdf_path (str): The path to the PDF file.
    - start_page (int): The starting page number (inclusive).
    - end_page (int): The ending page number (inclusive).
    Returns:
    - list of tuples: Each tuple contains the page number and the extracted text.
    """
    pages = []
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(reader.pages)
        # Adjust page range to ensure valid bounds
        start_page = max(start_page, 1) if start_page else 1
        end_page = min(end_page, total_pages) if end_page else total_pages
        for page_num, page in enumerate(reader.pages, start=1):
            if start_page <= page_num <= end_page:
                pages.append((page_num, page.extract_text()))
    return pages


def transform_events_to_excel(json_data, output_file="events_data.xlsx"):
    """
    Transforms JSON-like data into individual DataFrames for each event and saves them to an Excel file.
    Parameters:
    - json_data (str): JSON-like string containing event data.
    - output_file (str): The name of the output Excel file. Default is "events_data.xlsx".
    Returns:
    - None
    """
    # Parse the JSON string into a Python dictionary
    data = json.loads(json_data)
    # Extract events
    events = data.get("event", [])
    # Create a dictionary to hold DataFrames
    with pd.ExcelWriter(output_file) as writer:  # Use a context manager
        for event in events:
            # Event name as sheet name (trim or adjust if too long)
            sheet_name = event["event_name"][:31]  # Excel sheet name limit
            # Flatten the event data
            response_interventions = pd.DataFrame(event.get("response_interventions", []))
            recovery_fund_activations = pd.DataFrame(event.get("recovery_fund_activations", []))
            # Add common event metadata to each DataFrame
            response_interventions["event_name"] = event["event_name"]
            response_interventions["event_type"] = event["event_type"]
            response_interventions["event_dates"] = event["event_dates"]
            response_interventions["affected_areas"] = event["affected_areas"]
            response_interventions["event_description"] = event["event_description"]
            response_interventions["source_links"] = event["links"]
            response_interventions["page_number"] = event["page_number"]
            recovery_fund_activations["event_name"] = event["event_name"]
            recovery_fund_activations["event_type"] = event["event_type"]
            recovery_fund_activations["event_dates"] = event["event_dates"]
            recovery_fund_activations["affected_areas"] = event["affected_areas"]
            recovery_fund_activations["event_description"] = event["event_description"]
            recovery_fund_activations["source_links"] = event["links"]
            recovery_fund_activations["page_number"] = event["page_number"]
            # Combine the two DataFrames
            combined_df = pd.concat([response_interventions, recovery_fund_activations], ignore_index=True)
            # Write to the Excel file
            combined_df.to_excel(writer, index=False, sheet_name=sheet_name)
    print(f"Data has been saved to {output_file}")


# Now for the OpenAI stuff
client = OpenAI()

# SDKs for structured response extraction
# Define BASIC item schema
class ResponseIntervention(BaseModel):
    response_intervention_type: str
    response_intervention_date: str
    responsible_party: str
    targeted_relief_to_whom: str
    description: str
    links: str
    page_number: str

# Define BASIC item schema
class RecoveryFundActivation(BaseModel):
    recovery_fund_type: str
    recovery_fund_amount: str
    recovery_fund_date: str
    responsible_party: str
    targeted_relief_to_whom: str
    description: str
    links: str
    page_number: str

# Define BASIC item schema
class DisasterEvent(BaseModel):
    event_name: str
    event_type: str
    event_dates: str
    affected_areas: str
    event_description: str
    links: str
    page_number: str
    response_interventions: list[ResponseIntervention]
    recovery_fund_activations: list[RecoveryFundActivation]

# Overall schema
class DisasterEventDatabase(BaseModel):
    event: list[DisasterEvent]

# Extracting questions from supplied text
def extract_disaster_events_from_text(text_input, temperature_setting=0.7, max_tokens_setting=None, top_p_setting=1, presence_penalty_setting=0, n_setting=1, frequency_penalty_setting=0, logprobs_setting=False, model_setting="gpt-4o-mini", chain_of_thought=True, guiding_principles="Fact-driven and evidence-based, grounded in accurate data and reliable sources."):
    """
    Extracts information about disaster events from annual QLD disaster management reports.
    Parameters:
    - text_input (str): The raw text data to be processed.
    - temperature_setting (float): Temperature setting for model creativity.
    - model_setting (str): The model to be used for the task.
    - chain_of_thought (bool): Whether to include chain-of-thought reasoning in the response.
    - guiding_principles (str): Customizable guiding principles for the output.
    Returns:
    - dict: Extracted structured data in JSON format.
    """
    system_prompt = f"""
    You are a data extraction tool designed to analyze annual disaster management reports and extract structured information about ALL unique and significant disaster events mentioned.
    Your instructions:
    1. Identify and extract ALL significant disaster events, including but not limited to the following types:
       - Flooding
       - Tropical cyclones
       - Bushfires
       - Severe thunderstorms
       - Heatwaves
       - Pandemics
       - Biosecurity threats
       - Chemical, biological, or radiological incidents
       - Earthquakes
       - Tsunamis
       - Criminal/terrorist acts
       - Landslides
       - Other hazards.
    2. For each disaster event, collect the following information:
       - Event Name
       - Event Type
       - Event Dates
       - Affected Areas
       - Event Description/Overview
       - Links to related documents or websites
       - Page number(s) where the event is mentioned
       - Response Interventions:
           - Type of intervention
           - Date of intervention
           - Responsible party (i.e., who carried out the intervention)
           - Targeted relief (e.g., local government areas, individuals, groups/subpopulations)
           - Description of the intervention
           - Links to any supporting documents or resources
           - Page number(s) where the response intervention is mentioned
       - Recovery Fund Activations:
           - Type of fund
           - Amount of fund ($AUD)
           - Activation date
           - Responsible party (i.e., who administered or management the resource/funding allocations)
           - Targeted relief (e.g., local government areas, individuals, sectors)
           - Description of the activation
           - Links to any supporting documents or resources
           - Page number(s) where the recovery fund activation is mentioned.
    3. Cross-reference details within the text to ensure completeness and accuracy.
    4. Output the extracted data in JSON format according to the schema below:
    - event_name (str): Name of the disaster event.
    - event_name (str): Type/category of disaster event.
    - event_dates (str): Dates during which the event occurred.
    - affected_areas (str): Areas impacted by the disaster.
    - event_description (str): Description or overview of the event.
    - links (str): Relevant links.
    - page_number (str): Page numbers where the event is mentioned.
    - response_interventions (list[ResponseIntervention]): Details of response interventions.
    - recovery_fund_activations (list[RecoveryFundActivation]): Details of recovery fund activations.
    Guiding principles:
    - {guiding_principles}
    """
    # Dynamic user prompt to provide specific instructions
    user_content = f"Extract structured disaster event information based on the schema provided. Include ALL disaster events listed. Ensure all data is accurate and includes relevant details such as response interventions and recovery fund activations. Here is the supplied text: {text_input}."
    end_content = ""
    if chain_of_thought:
        end_content = " Let's think step-by-step."
    # The final user message prompt
    user_message = f"{user_content} {end_content}"
    # Call to the language model for processing
    response = client.beta.chat.completions.parse(
        model=model_setting,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        response_format=DisasterEventDatabase,
        max_tokens=max_tokens_setting,
        temperature=temperature_setting,
        top_p=top_p_setting,
        presence_penalty=presence_penalty_setting,
        n=n_setting,
        frequency_penalty=frequency_penalty_setting,
        logprobs=logprobs_setting,
    )
    return response.choices[0].message.content


# Example usage
pages=extract_text_from_pdf("queensland-disaster-management-committee-annual-report-2023-2024.pdf", start_page=2, end_page=7) # It starts to break down (i.e. miss events) a bit when we go beyond 10 pages
extract_df = extract_disaster_events_from_text(str(pages), temperature_setting=0.7, max_tokens_setting=None, top_p_setting=1, presence_penalty_setting=0, n_setting=1, frequency_penalty_setting=0, logprobs_setting=False, model_setting="gpt-4o", chain_of_thought=True, guiding_principles="Fact-driven and evidence-based, grounded in accurate data and reliable sources.")
extracted_data = (json.loads(extract_df)).get("event", [])
transform_events_to_excel(extract_df, "events_data.xlsx")

## -- Section 2: Extending this to chunks

# Chunks the PDF Text and yields a list of (page_number, text) tuples for each chunk
def chunk_pdf_text(pdf_path, chunk_size=5):
    """
    Reads the PDF and yields chunks of text (each chunk covers 'chunk_size' pages).
    """
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(reader.pages)
        for start in range(0, total_pages, chunk_size):
            end = min(start + chunk_size, total_pages)
            chunk_pages = []
            for page_num in range(start, end):
                # Extract text
                text = reader.pages[page_num].extract_text()
                chunk_pages.append((page_num+1, text))  # store 1-based page index
            yield chunk_pages


# First pass - identify ALL unique disaster events listed in the "The Year in Review"
# Note: typical document structure is events are all listed within first 4-8 pages

# Define BASIC item schema
class DisasterEvent(BaseModel):
    event_name: str
    event_type: str
    event_dates: str
    affected_areas: str
    event_description: str
    links: str
    page_number: str

# Overall schema
class DisasterEventDatabase(BaseModel):
    event: list[DisasterEvent]

# Now the function definition to call the API
def extract_disaster_events_from_text(text_input, temperature_setting=0.7, max_tokens_setting=None, top_p_setting=1, presence_penalty_setting=0, n_setting=1, frequency_penalty_setting=0, logprobs_setting=False, model_setting="gpt-4o-mini", chain_of_thought=True, guiding_principles="Fact-driven and evidence-based, grounded in accurate data and reliable sources."):
    """
    Extracts information about disaster events from annual QLD disaster management reports.
    Parameters:
    - text_input (str): The raw text data to be processed.
    - temperature_setting (float): Temperature setting for model creativity.
    - model_setting (str): The model to be used for the task.
    - chain_of_thought (bool): Whether to include chain-of-thought reasoning in the response.
    - guiding_principles (str): Customizable guiding principles for the output.
    Returns:
    - dict: Extracted structured data in JSON format.
    """
    system_prompt = f"""
    You are a data extraction tool designed to analyze annual disaster management reports and extract structured information about ALL unique and significant disaster events mentioned in the supplied text.
    Your instructions:
    1. Identify and extract ALL significant disaster events, including but not limited to the following types:
       - Flooding
       - Tropical cyclones
       - Bushfires
       - Severe thunderstorms
       - Heatwaves
       - Pandemics
       - Biosecurity threats
       - Chemical, biological, or radiological incidents
       - Earthquakes
       - Tsunamis
       - Criminal/terrorist acts
       - Landslides
       - Other hazards.
    2. For each disaster event, collect the following information:
       - Event Name
       - Event Type
       - Event Dates
       - Affected Areas
       - Event Description/Overview
       - Links to related documents or websites
       - Page number(s) where the event is mentioned.
    3. Cross-reference details within the text to ensure completeness and accuracy.
    4. Output the extracted data in JSON format according to the schema below:
    - event_name (str): Name of the disaster event.
    - event_name (str): Type/category of disaster event.
    - event_dates (str): Dates during which the event occurred.
    - affected_areas (str): Areas impacted by the disaster.
    - event_description (str): Description or overview of the event.
    - links (str): Relevant links.
    - page_number (str): Page number/s where the event is mentioned.
    Guiding principles:
    - {guiding_principles}
    """
    # Dynamic user prompt to provide specific instructions
    user_content = f"Extract structured disaster event information based on the schema provided. Include ALL disaster events listed in the supplied text. Ensure all data is accurate and includes relevant details. Supplied Text: {text_input}."
    end_content = ""
    if chain_of_thought:
        end_content = " Let's think step-by-step."
    # The final user message prompt
    user_message = f"{user_content} {end_content}"
    # Call to the language model for processing
    response = client.beta.chat.completions.parse(
        model=model_setting,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        response_format=DisasterEventDatabase,
        max_tokens=max_tokens_setting,
        temperature=temperature_setting,
        top_p=top_p_setting,
        presence_penalty=presence_penalty_setting,
        n=n_setting,
        frequency_penalty=frequency_penalty_setting,
        logprobs=logprobs_setting,
    )
    return response.choices[0].message.content

# Now run on the first few pages (in chunks?)
pages=extract_text_from_pdf("queensland-disaster-management-committee-annual-report-2023-2024.pdf", start_page=2, end_page=7) # It starts to break down (i.e. miss events) a bit when we go beyond 10 pages
events_df = extract_disaster_events_from_text(str(pages), temperature_setting=0.7, max_tokens_setting=None, top_p_setting=1, presence_penalty_setting=0, n_setting=1, frequency_penalty_setting=0, logprobs_setting=False, model_setting="gpt-4o", chain_of_thought=True, guiding_principles="Fact-driven and evidence-based, grounded in accurate data and reliable sources.")
events_catalog = (json.loads(events_df)).get("event", [])

# Second pass - collect detailed info for each event across the full PDF

# Define the Schemas first
class ResponseIntervention(BaseModel):
    response_intervention_type: str
    response_intervention_date: str
    responsible_party: str
    targeted_relief_to_whom: str
    description: str
    links: str
    page_number: str

# Define BASIC item schema
class RecoveryFundActivation(BaseModel):
    recovery_fund_type: str
    recovery_fund_amount: str
    recovery_fund_date: str
    responsible_party: str
    targeted_relief_to_whom: str
    description: str
    links: str
    page_number: str

class DisasterEvent(BaseModel):
    event_name: str
    event_dates: str
    response_interventions: list[ResponseIntervention]
    recovery_fund_activations: list[RecoveryFundActivation]

# Overall schema
class DisasterEventDatabase(BaseModel):
    event: list[DisasterEvent]

# Now the function definition to call the API itself
def extract_disaster_event_details_from_text(text_input, temperature_setting=0.7, max_tokens_setting=None, top_p_setting=1, presence_penalty_setting=0, n_setting=1, frequency_penalty_setting=0, logprobs_setting=False, model_setting="gpt-4o-mini", chain_of_thought=True, guiding_principles="Fact-driven and evidence-based, grounded in accurate data and reliable sources."):
    """
    Extracts information about disaster events from annual QLD disaster management reports.
    Parameters:
    - text_input (str): The raw text data to be processed.
    - temperature_setting (float): Temperature setting for model creativity.
    - model_setting (str): The model to be used for the task.
    - chain_of_thought (bool): Whether to include chain-of-thought reasoning in the response.
    - guiding_principles (str): Customizable guiding principles for the output.
    Returns:
    - dict: Extracted structured data in JSON format.
    """
    system_prompt = f"""
    You are a data extraction tool designed to analyze annual disaster management reports and extract structured information from the supplied text that references these known disaster events: {events_catalog}.
    Your instructions:
    1. For each disaster event, gather the following information:
       - Event Name
       - Event Dates
       - Response Interventions:
           - Type of intervention/s
           - Date of intervention/s
           - Responsible party/parties (i.e., who carried out the intervention)
           - Targeted relief/s (e.g., local government areas, individuals, groups/subpopulations)
           - Description of the intervention/s
           - Links to any supporting documents or resources
           - Page number(s) where the response intervention is mentioned
       - Recovery Fund Activations:
           - Type of fund/s
           - Amount of fund/s ($AUD)
           - Activation date/s
           - Responsible party/parties (i.e., who administered or management the resource/funding allocations)
           - Targeted relief/s (e.g., local government areas, individuals, sectors)
           - Description of the recovery fund activation/s
           - Links to any supporting documents or resources
           - Page number(s) where the recovery fund activation is mentioned.
    3. Cross-reference details within the text to ensure completeness and accuracy.
    4. Output the extracted data in JSON format according to the schema below:
    - event_name (str): Name of the disaster event.
    - event_dates (str): Dates during which the event occurred.
    - response_interventions (list[ResponseIntervention]): Details of response interventions.
    - recovery_fund_activations (list[RecoveryFundActivation]): Details of recovery fund activations.
    Guiding principles:
    - {guiding_principles}
    """
    # Dynamic user prompt to provide specific instructions
    user_content = f"Extract structured disaster event information based on the schema provided. Include ALL disaster events listed. Ensure all data is accurate and includes relevant details. Supplied Text: {text_input}."
    end_content = ""
    if chain_of_thought:
        end_content = " Let's think step-by-step."
    # The final user message prompt
    user_message = f"{user_content} {end_content}"
    # Call to the language model for processing
    response = client.beta.chat.completions.parse(
        model=model_setting,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        response_format=DisasterEventDatabase,
        max_tokens=max_tokens_setting,
        temperature=temperature_setting,
        top_p=top_p_setting,
        presence_penalty=presence_penalty_setting,
        n=n_setting,
        frequency_penalty=frequency_penalty_setting,
        logprobs=logprobs_setting,
    )
    return response.choices[0].message.content

# Now run the LLM API processing pipeline on the chunks (all pages of the supplied pdf)
def collect_all_event_details(pdf_path, events_catalog, chunk_size=5):
    """
    Goes through entire document in chunks, uses LLM to gather details from each chunk that reference those events.
    Returns a Python dictionary keyed by event name.
    """
    from collections import defaultdict
    # Prepare the data structure for final results - each event gets a dictionary for storing info
    consolidated_data = {
        (event["event_name"], event["event_dates"]): {
            "event_name": event["event_name"],
            "event_dates": event["event_dates"],
            "event_type": event.get("event_type"),
            "affected_areas": event.get("affected_areas"),
            "event_description": event.get("event_description", ''),
            "links": event.get("links", []),
            "page_number": event.get("page_number", []),
            "response_interventions": [],
            "recovery_fund_activations": []
        }
        for event in events_catalog
    }
    for chunk_pages in chunk_pdf_text(pdf_path, chunk_size=chunk_size):
        # Prepare the 'Supplied Text'
        chunk_text = "\n".join([f"(Page {pnum}) {txt}" for pnum, txt in chunk_pages])
        # Make the LLM API call using the chunk text
        response = extract_disaster_event_details_from_text(chunk_text)
        # Get the text as a python dictionary-like dataframe
        chunk_details = (json.loads(response)).get('event', [])
        # Now we merge these chunk-level details into the consolidated_data
        #for event_name, info in chunk_details.items():
        for i, event_uniq in enumerate(chunk_details):
            event_name = event_uniq['event_name'] # Extract the event_name and event_dates from the chunk's data
            event_dates = event_uniq['event_dates']
            event_key = (event_name, event_dates) # Create a composite key
            if event_key in consolidated_data:
                # Now extend or update data in the existing dictionary entry
                info = consolidated_data[event_key]
                # Merge the data appropriately
                if event_uniq['response_interventions']:
                    info['response_interventions'].extend(event_uniq['response_interventions'])
                if event_uniq['recovery_fund_activations']:
                    info['recovery_fund_activations'].extend(event_uniq['recovery_fund_activations'])
    return consolidated_data


def transform_events_dict_to_excel(events_data, output_file="events_database.xlsx"):
    """
    Transforms event data from a dictionary into individual DataFrames for each event and saves them to an Excel file.
    Parameters:
    - json_data (str): JSON-like string containing event data.
    - output_file (str): The name of the output Excel file. Default is "events_data.xlsx".
    Returns:
    - None
    """
    # Ensure that events_data is a dictionary
    if not isinstance(events_data, dict):
        raise TypeError(f"Expected events_data to be a dict, but got {type(events_data).__name__}")
    # Extract events from the dictionary values
    events = events_data.values()
    # Create a dictionary to hold DataFrames
    with pd.ExcelWriter(output_file) as writer:  # Use a context manager
        for event in events:
            # Ensure the event has the necessary keys
            required_keys = ["event_name", "event_type", "event_dates",
                             "affected_areas", "event_description",
                             "links", "page_number",
                             "response_interventions", "recovery_fund_activations"]
            missing_keys = [key for key in required_keys if key not in event]
            if missing_keys:
                print(f"Skipping event due to missing keys: {missing_keys}")
                continue
            # Event name as sheet name (trim or adjust if too long)
            sheet_name = event["event_name"][:31]  # Excel sheet name limit
                        # Define metadata to add to each DataFrame
            metadata = {
                "event_name": event["event_name"],
                "event_type": event["event_type"],
                "event_dates": event["event_dates"],
                "event_affected_areas": event["affected_areas"],
                "event_description": event["event_description"],
                "event_source_links": event["links"],
                "event_page_number": event["page_number"]  # Renamed to avoid conflict
            }
            # Flatten the event details data next
            response_interventions = pd.DataFrame(event.get("response_interventions", []))
            recovery_fund_activations = pd.DataFrame(event.get("recovery_fund_activations", []))
            # Identify shared columns between the two DataFrames
            ri_columns = set(response_interventions.columns)
            rfa_columns = set(recovery_fund_activations.columns)
            shared_columns = ri_columns.intersection(rfa_columns)
            # Define prefix mappings for shared columns
            ri_shared_keys = {key: f'ri_{key}' for key in shared_columns}
            rfa_shared_keys = {key: f'rfa_{key}' for key in shared_columns}
            # Rename shared columns with prefixes
            if ri_shared_keys:
                response_interventions.rename(columns=ri_shared_keys, inplace=True)
            if rfa_shared_keys:
                recovery_fund_activations.rename(columns=rfa_shared_keys, inplace=True)
            # Add metadata to response interventions
            for key, value in metadata.items(): # ['response_intervention_type', 'response_intervention_date', 'responsible_party', 'targeted_relief_to_whom', 'description', 'links', 'page_number']
                response_interventions[key] = value
            # Add metadata to recovery fund activations
            for key, value in metadata.items(): # ['recovery_fund_type', 'recovery_fund_amount', 'recovery_fund_date', 'responsible_party', 'targeted_relief_to_whom', 'description', 'links', 'page_number']
                recovery_fund_activations[key] = value
            # Combine the two DataFrames
            combined_df = pd.concat([response_interventions, recovery_fund_activations], ignore_index=True)
            # Write the combined DataFrame to the Excel sheet
            combined_df.to_excel(writer, index=False, sheet_name=sheet_name)
    print(f"Data has been saved to {output_file}")


# Now actually use the function
events_database = collect_all_event_details("queensland-disaster-management-committee-annual-report-2023-2024.pdf", events_catalog)

#And write to excel
transform_events_dict_to_excel(events_database, "queensland-disaster-management-committee-annual-report-2023-2024_events_database.xlsx")

##### ------ MAIN CODE - END ------- ####