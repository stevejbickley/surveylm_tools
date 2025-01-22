##### ------ IMPORT FUNCTIONS + SETUP CODE - START ------- ####

import PyPDF2
import pandas as pd
import numpy as np
import openpyxl
import os
import re
from collections import defaultdict
import glob
from fuzzywuzzy import fuzz
from datetime import datetime

##### ------ DEFINE FUNCTIONS - START ------- ####

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file along with page numbers."""
    pages = []
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page_num, page in enumerate(reader.pages, start=1):
            pages.append((page_num, page.extract_text()))
    return pages


def extract_significant_events(pages):
    """Extract significant events and related details from the text."""
    event_pattern = r"(.*?(Bushfires|Cyclone|Flooding|Severe Storms).*?)\n"
    link_pattern = r"https?://\S+"
    event_details = []
    mentions = defaultdict(list)
    for page_num, text in pages:
        # Extract event matches
        events = re.findall(event_pattern, text)
        links = re.findall(link_pattern, text)
        for event_match in events:
            event_name = event_match[0].strip()
            # Extract contextual details (e.g., dates, locations)
            date_pattern = r"\d{1,2}\s\w+\s\d{4}\s?-\s?\d{1,2}\s\w+\s\d{4}"
            dates = re.findall(date_pattern, event_name)
            recovery_pattern = r"Disaster Recovery Funding Arrangements.*?\n"
            recovery_info = re.findall(recovery_pattern, text)
            affected_areas_pattern = r"activated for (.+?)\."
            affected_areas = re.findall(affected_areas_pattern, text)
            event_details.append({
                "Event Name": event_name,
                "Dates": ", ".join(dates) if dates else "N/A",
                "Affected Areas": ", ".join(affected_areas) if affected_areas else "N/A",
                "Recovery Info": recovery_info[0].strip() if recovery_info else "N/A",
                "Links": ", ".join(links) if links else "N/A",
                "Page Number": page_num
            })
            mentions[event_name].append(page_num)
    return event_details, mentions


def extract_significant_events(pages, selected_pages=None):
    """Extract significant events and related details from the text.
    Args:
        pages (list): List of tuples containing page numbers and text.
        selected_pages (tuple): Optional (start_page, end_page) range for extracting main events.
    Returns:
        list: Extracted event details.
        defaultdict: Mentions of events across the document.
    """
    event_pattern = r"(.*?(Bushfires|Cyclone|Flooding|Severe Storms).*?)\n"
    link_pattern = r"https?://\S+"
    event_details = []
    mentions = defaultdict(list)
    # Determine the page range for extracting significant events
    if selected_pages:
        start_page, end_page = selected_pages
    else:
        start_page, end_page = 1, len(pages)
    for page_num, text in pages:
        if start_page <= page_num <= end_page:
            # Extract event matches
            events = re.findall(event_pattern, text)
            links = re.findall(link_pattern, text)
            for event_match in events:
                event_name = event_match[0].strip()
                # Extract contextual details (e.g., dates, locations)
                #date_pattern = r"\d{1,2}\s\w+\s\d{4}\s?-\s?\d{1,2}\s\w+\s\d{4}"
                date_pattern = r"""
                \d{1,2}            # Day: 1 or 2 digits
                [\s_]              # Separator: space or underscore
                \w+                # Month: word (e.g., September)
                (?:[\s_-](?:to|TO|-|TO))? # Optional connector: to, -, or underscore
                [\s_]?
                (?:\d{1,2}[\s_]\w+)? # Optional second day and month
                [\s_]
                \d{4}              # Year: 4 digits
                """
                date_pattern = re.compile(date_pattern, re.VERBOSE | re.IGNORECASE)
                dates = re.findall(date_pattern, event_name)
                recovery_pattern = r"Disaster Recovery Funding Arrangements.*?\n"
                recovery_info = re.findall(recovery_pattern, text)
                affected_areas_pattern = r"activated for (.+?)\."
                affected_areas = re.findall(affected_areas_pattern, text)
                event_details.append({
                    "Event Name": event_name,
                    "Dates": ", ".join(dates) if dates else "N/A",
                    "Affected Areas": ", ".join(affected_areas) if affected_areas else "N/A",
                    "Recovery Info": recovery_info[0].strip() if recovery_info else "N/A",
                    "Links": ", ".join(links) if links else "N/A",
                    "Page Number": page_num
                })
                mentions[event_name].append(page_num)
    if selected_pages:
        # Find mentions of extracted events across the rest of the document
        for page_num, text in pages[end_page+1:]:
            for event in [event["Event Name"] for event in event_details]:
                if event in text:
                    mentions[event].append(page_num)
    return event_details, mentions



def deduplicate_events(event_details, similarity_threshold=90):
    """Deduplicate events by grouping similar entries based on fuzzy matching and optional date comparison.
    Args:
        event_details (list): List of dictionaries containing event details.
        similarity_threshold (int): Threshold for fuzzy similarity to group events.
    Returns:
        list: Deduplicated event details.
    """
    deduplicated = []
    seen_events = []
    #event_pattern = r"((?:\S+\s){0,2}(Bushfires|Cyclone|Flooding|Severe Storms)(?:\s\S+){0,2})"
    # Define regex for extracting core event names with location and descriptors
    event_pattern = r"""
    (?:(?:Tropical|Severe|Southern|Northern|East|West|Southwest|Southeast)\s+(?:\w+\s+)?(?:\w+\s+)?)?
    (?:[A-Z][a-z]*(?:\s+and\s+[A-Z][a-z]*)?)\s+ # Locations or descriptors with optional 'and'
    (?:Cyclone|Bushfires|Flooding|Storms)           # Core event type
    (?:\s+[A-Z][a-z]*){0,2}                           # Optional additional words (e.g., names or descriptors, capitalized)
    (?=\s+[a-z]|$)                                  # Ensure next word is not lowercase
    """
    event_pattern = re.compile(event_pattern, re.VERBOSE | re.IGNORECASE)
    # Helper function to extract month and year from date strings
    def extract_month_year(date_str):
        try:
            match = re.search(r"(\w+)\s+(\d{4})", date_str)
            if match:
                return datetime.strptime(f"1 {match.group(1)} {match.group(2)}", "%d %B %Y")
        except Exception:
            pass
        return None
    for event in event_details:
        # Apply regex pattern to shorten event name
        full_event_name = event.get("Event Name", "")
        dates = event.get("Dates", "N/A")
        # Apply regex pattern to extract shortened event name
        match = re.search(event_pattern, full_event_name)
        if match:
            event_name = match.group(0).strip()
        else:
            event_name = full_event_name  # Fallback to full event name if no match
        # Extract the first month and year from the "Dates" column
        event_date = extract_month_year(dates)
        matched = False
        for existing_event in seen_events:
            # Compare dates if both have valid dates
            existing_date = extract_month_year(existing_event.get("Dates", "N/A"))
            if event_date and existing_date and event_date.year == existing_date.year and event_date.month == existing_date.month:
                # Merge based on matching dates
                existing_event["Links"] = ", ".join(set(existing_event["Links"].split(", ") + event["Links"].split(", ")))
                existing_event["Page Number"] = f"{existing_event['Page Number']}, {event['Page Number']}"
                matched = True
                break
            # If dates are missing or do not match, rely on fuzzy matching of event names
            elif not event_date or not existing_date:
                similarity = fuzz.token_sort_ratio(event_name, existing_event.get("Event Name (Short)", ""))
                if similarity >= similarity_threshold:
                    existing_event["Links"] = ", ".join(set(existing_event["Links"].split(", ") + event["Links"].split(", ")))
                    existing_event["Page Number"] = f"{existing_event['Page Number']}, {event['Page Number']}"
                    matched = True
                    break
        if not matched:
            event["Event Name (Short)"] = event_name
            seen_events.append(event)
    deduplicated = seen_events
    return deduplicated



def compile_mentions_to_dataframe(mentions):
    """Compile event mentions into a structured DataFrame."""
    data = []
    for event_name, pages in mentions.items():
        data.append({"Event Name": event_name, "Mentioned on Pages": ", ".join(map(str, pages))})
    return pd.DataFrame(data)


def save_to_excel(event_details, mentions_df, output_path):
    """Save extracted data to an Excel file with multiple sheets."""
    with pd.ExcelWriter(output_path) as writer:
        events_df = pd.DataFrame(event_details)
        events_df.to_excel(writer, index=False, sheet_name="Events")
        mentions_df.to_excel(writer, index=False, sheet_name="Mentions")
    print(f"Data saved to {output_path}")


def main(pdf_path, output_path):
    pages = extract_text_from_pdf(pdf_path)
    event_details, mentions = extract_significant_events(pages, selected_pages)
    event_details = deduplicate_events(event_details)
    mentions_df = compile_mentions_to_dataframe(mentions)
    save_to_excel(event_details, mentions_df, output_path)

##### ------ MAIN CODE - START ------- ####

## ------ SECTION 1: XXXX ------ ##
#input_file_paths = glob.glob('*scenario_database_final.xlsx')

# Example usage
pdf_path = "queensland-disaster-management-committee-annual-report-2023-2024.pdf"
output_path = "significant_disaster_events.xlsx"
selected_pages = (2, 7)  # Example: Extract main events from pages 2 to 10
main(pdf_path, output_path, selected_pages)

## ------ SECTION 2: XXXX ------ ##


##### ------ MAIN CODE - END ------- ####

