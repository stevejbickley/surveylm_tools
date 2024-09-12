##### ------ IMPORT FUNCTIONS + SETUP CODE - START ------- ####

from pydantic import BaseModel
from openai import OpenAI
import fitz  # PyMuPDF
import io
import os
from PIL import Image
import base64
import json
import psycopg2
import pandas as pd


##### ------ DEFINE FUNCTIONS - START ------- ####


client = OpenAI()


@staticmethod
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def pdf_to_base64_images(pdf_path):
    #Handles PDFs with multiple pages
    pdf_document = fitz.open(pdf_path)
    base64_images = []
    temp_image_paths = []
    total_pages = len(pdf_document)
    for page_num in range(total_pages):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes()))
        temp_image_path = f"temp_page_{page_num}.png"
        img.save(temp_image_path, format="PNG")
        temp_image_paths.append(temp_image_path)
        base64_image = encode_image(temp_image_path)
        base64_images.append(base64_image)
    for temp_image_path in temp_image_paths:
        os.remove(temp_image_path)
    return base64_images


# In the extract_invoice_data function, modify the system prompt to extract relevant CV data such as name, contact information, work experience, education, skills, etc.
def extract_cv_data(base64_image, temperature_setting=0.0):
    system_prompt = f"""
    You are an OCR-like data extraction tool that extracts data from resumes/CVs.
    1. Please extract all available information about the person, grouping data into key categories: personal details (name, contact information), education, work experience, skills, certifications, and any other relevant sections like languages or hobbies.
    2. Please output the data in JSON format with meaningful and consistent keys for each section.
    3. If some sections (e.g., skills or certifications) are missing, include them as "null" values.
    4. Maintain the structure of the resume while grouping similar information together.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "extract the data from this resume and output it into JSON"},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/png;base64,{base64_image}", "detail": "high"}}
                ]
            }
        ],
        temperature=temperature_setting,
    )
    return response.choices[0].message.content


def extract_from_multiple_pages(base64_images, original_filename, output_directory):
    entire_invoice = []
    for base64_image in base64_images:
        invoice_json = extract_cv_data(base64_image)
        invoice_data = json.loads(invoice_json)
        entire_invoice.append(invoice_data)
    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)
    # Construct the output file path
    output_filename = os.path.join(output_directory, original_filename.replace('.pdf', '_extracted.json'))
    # Save the entire_invoice list as a JSON file
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(entire_invoice, f, ensure_ascii=False, indent=4)
    return output_filename


def main_extract(read_path, write_path):
    for filename in os.listdir(read_path):
        if filename[-4:] == '.pdf':
            file_path = os.path.join(read_path, filename)
            if os.path.isfile(file_path):
                base64_images = pdf_to_base64_images(file_path)
                extract_from_multiple_pages(base64_images, filename, write_path)


# SDK for structured response extraction
class ResumeInformationExtraction(BaseModel):
    class Personal(BaseModel):
        name: str
        email: str
        phone: str
        address: str
    personal_details: Personal
    class Work(BaseModel):
        company_name: str
        position: str
        start_date: str
        end_date: str
        description: str
    work_experience: list[Work]
    class Education(BaseModel):
        institution_name: str
        degree: str
        start_date: str
        end_date: str
        description: str
    education: list[Education]
    technical_skills: list[str]
    soft_skills: list[str]
    certifications: list[str]
    languages: list[str]
    hobbies: list[str]


def transform_data_into_schema(json_raw, json_schema, temperature_setting=0.2, model="gpt-4o-2024-08-06"):
    system_prompt = f"""
    You are a data transformation tool that takes in JSON data and a reference JSON schema, and outputs JSON data according to the schema.
    Not all of the data in the input JSON will fit the schema, so you may need to omit some data or add null values to the output JSON.
    Translate all data into English if not already in English.
    Ensure values are formatted as specified in the schema (e.g. dates as YYYY-MM-DD).
    If a section from the raw JSON closely matches a section in the schema, but doesn't fit exactly, use your judgment to map the data to the closest or most relevant section of the schema.
    For example, if there are sections such as "Interpersonal Skills" in the raw JSON, this should be mapped to the "soft_skills" field in the schema.
    Here is the schema:
    {json_schema}
    """
    response = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": f"Transform the following raw JSON data according to the provided schema. Ensure all data is in English and formatted as specified by values in the schema. Here is the raw JSON: {json_raw}"}
                ]
            }
        ],
        response_format = ResumeInformationExtraction,
        temperature=temperature_setting,
    )
    return json.loads(response.choices[0].message.content)


def main_transform(extracted_invoice_json_path, json_schema, save_path):
    # Ensure the save directory exists
    os.makedirs(save_path, exist_ok=True)
    # Process each JSON file in the extracted invoices directory
    for filename in os.listdir(extracted_invoice_json_path):
        if filename.endswith(".json"):
            file_path = os.path.join(extracted_invoice_json_path, filename)
            # Load the extracted JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                json_raw = json.load(f)
            # Transform the JSON data
            transformed_json = transform_data_into_schema(json_raw, json_schema)
            # Save the transformed JSON to the save directory
            transformed_filename = f"transformed_{filename}"
            transformed_file_path = os.path.join(save_path, transformed_filename)
            with open(transformed_file_path, 'w', encoding='utf-8') as f:
                json.dump(transformed_json, f, ensure_ascii=False, indent=2)


def save_to_csv(data, columns, filename):
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(filename, index=False)


def ingest_transformed_jsons_to_csv_files(json_folder_path, save_folder_path):
    resume_data = []
    work_experience_data = []
    education_data = []
    skills_data = []
    certifications_data = []
    for filename in os.listdir(json_folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(json_folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Collect Personal Details
            resume_data.append((
                data["personal_details"]["name"],
                data["personal_details"]["email"],
                data["personal_details"]["phone"],
                data["personal_details"]["address"]
            ))
            # Collect Work Experience
            for job in data["work_experience"]:
                work_experience_data.append((
                    data["personal_details"]["name"],  # Assuming name for identification
                    job["company_name"],
                    job["position"],
                    job["start_date"],
                    job["end_date"],
                    job["description"]
                ))
            # Collect Education
            for edu in data["education"]:
                education_data.append((
                    data["personal_details"]["name"],
                    edu["institution_name"],
                    edu["degree"],
                    edu["start_date"],
                    edu["end_date"],
                    edu["description"]
                ))
            # Collect Skills
            for skill in data["skills"]:
                skills_data.append((data["personal_details"]["name"], skill))
            # Collect Certifications
            for cert in data["certifications"]:
                certifications_data.append((data["personal_details"]["name"], cert))
    # Ensure the save directory exists
    os.makedirs(save_folder_path, exist_ok=True)
    # Save each dataset to CSV
    save_to_csv(resume_data, ["Name", "Email", "Phone", "Address"], os.path.join(save_folder_path, "resumes.csv"))
    save_to_csv(work_experience_data, ["Name", "Company", "Position", "Start Date", "End Date", "Description"], os.path.join(save_folder_path, "work_experience.csv"))
    save_to_csv(education_data, ["Name", "Institution", "Degree", "Start Date", "End Date", "Description"], os.path.join(save_folder_path, "education.csv"))
    save_to_csv(skills_data, ["Name", "Skill"], os.path.join(save_folder_path, "skills.csv"))
    save_to_csv(certifications_data, ["Name", "Certification"], os.path.join(save_folder_path, "certifications.csv"))


def ingest_transformed_jsons_to_wide_csv(json_folder_path, save_file_path):
    all_data = []
    max_work_exp = 0
    max_education = 0
    max_skills = 0
    max_certifications = 0
    for filename in os.listdir(json_folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(json_folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Collect Personal Details
            person_data = {
                "Name": data["personal_details"]["name"],
                "Email": data["personal_details"]["email"],
                "Phone": data["personal_details"]["phone"],
                "Address": data["personal_details"]["address"]
            }
            # Collect Work Experience
            for i, job in enumerate(data["work_experience"], start=1):
                person_data[f"Previous Employment {i} Company"] = job["company_name"]
                person_data[f"Previous Employment {i} Position"] = job["position"]
                person_data[f"Previous Employment {i} Start Date"] = job["start_date"]
                person_data[f"Previous Employment {i} End Date"] = job["end_date"]
                person_data[f"Previous Employment {i} Description"] = job["description"]
            # Track max number of work experiences for column creation
            max_work_exp = max(max_work_exp, len(data["work_experience"]))
            # Collect Education
            for i, edu in enumerate(data["education"], start=1):
                person_data[f"Education {i} Institution"] = edu["institution_name"]
                person_data[f"Education {i} Degree"] = edu["degree"]
                person_data[f"Education {i} Start Date"] = edu["start_date"]
                person_data[f"Education {i} End Date"] = edu["end_date"]
                person_data[f"Education {i} Description"] = edu["description"]
            # Track max number of education entries for column creation
            max_education = max(max_education, len(data["education"]))
            # Collect Skills
            for i, skill in enumerate(data["skills"], start=1):
                person_data[f"Skill {i}"] = skill
            # Track max number of skills
            max_skills = max(max_skills, len(data["skills"]))
            # Collect Certifications
            for i, cert in enumerate(data["certifications"], start=1):
                person_data[f"Certification {i}"] = cert
            # Track max number of certifications
            max_certifications = max(max_certifications, len(data["certifications"]))
            # Append person's data to all_data list
            all_data.append(person_data)
    # Dynamically create column headers based on max number of work experiences, education entries, skills, and certifications
    columns = ["Name", "Email", "Phone", "Address"]
    for i in range(1, max_work_exp + 1):
        columns += [f"Previous Employment {i} Company", f"Previous Employment {i} Position", f"Previous Employment {i} Start Date", f"Previous Employment {i} End Date", f"Previous Employment {i} Description"]
    for i in range(1, max_education + 1):
        columns += [f"Education {i} Institution", f"Education {i} Degree", f"Education {i} Start Date", f"Education {i} End Date", f"Education {i} Description"]
    for i in range(1, max_skills + 1):
        columns += [f"Skill {i}"]
    for i in range(1, max_certifications + 1):
        columns += [f"Certification {i}"]
    # Save the data to a wide CSV
    save_to_csv(all_data, columns, save_file_path)


def ingest_transformed_jsons_postgres(json_folder_path, db_config):
    # Connect to PostgreSQL
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    # Create necessary tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Resumes (
        person_id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        email VARCHAR(255),
        phone VARCHAR(50),
        address TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS WorkExperience (
        work_id SERIAL PRIMARY KEY,
        person_id INTEGER REFERENCES Resumes(person_id),
        company_name VARCHAR(255),
        position VARCHAR(255),
        start_date DATE,
        end_date DATE,
        description TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Education (
        edu_id SERIAL PRIMARY KEY,
        person_id INTEGER REFERENCES Resumes(person_id),
        institution_name VARCHAR(255),
        degree VARCHAR(255),
        start_date DATE,
        end_date DATE,
        description TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Skills (
        skill_id SERIAL PRIMARY KEY,
        person_id INTEGER REFERENCES Resumes(person_id),
        skill VARCHAR(255)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Certifications (
        cert_id SERIAL PRIMARY KEY,
        person_id INTEGER REFERENCES Resumes(person_id),
        certification VARCHAR(255)
    )
    ''')
    # Loop over all JSON files and insert data
    for filename in os.listdir(json_folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(json_folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Insert Personal Details
            cursor.execute('''
            INSERT INTO Resumes (name, email, phone, address) 
            VALUES (%s, %s, %s, %s) RETURNING person_id
            ''', (
                data["personal_details"]["name"],
                data["personal_details"]["email"],
                data["personal_details"]["phone"],
                data["personal_details"]["address"]
            ))
            person_id = cursor.fetchone()[0]
            # Insert Work Experience
            for job in data["work_experience"]:
                start_date = job["start_date"] if job["start_date"] else None
                end_date = job["end_date"] if job["end_date"] else None
                cursor.execute('''
                INSERT INTO WorkExperience (person_id, company_name, position, start_date, end_date, description) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    person_id,
                    job["company_name"],
                    job["position"],
                    start_date,
                    end_date,
                    job["description"]
                ))
            # Insert Education
            for edu in data["education"]:
                start_date = edu["start_date"] if edu["start_date"] else None
                end_date = edu["end_date"] if edu["end_date"] else None
                cursor.execute('''
                INSERT INTO Education (person_id, institution_name, degree, start_date, end_date, description) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    person_id,
                    edu["institution_name"],
                    edu["degree"],
                    start_date,
                    end_date,
                    edu["description"]
                ))
            # Insert Skills
            for skill in data["skills"]:
                cursor.execute('''
                INSERT INTO Skills (person_id, skill) 
                VALUES (%s, %s)
                ''', (person_id, skill))
            # Insert Certifications
            for cert in data["certifications"]:
                cursor.execute('''
                INSERT INTO Certifications (person_id, certification) 
                VALUES (%s, %s)
                ''', (person_id, cert))
    conn.commit()
    cursor.close()
    conn.close()


##### ------ MAIN CODE - START ------- ####

# -- Step 1)
read_path = "./data/inputs/pdfs/"
write_path = "./data/outputs/intermediate/"

main_extract(read_path, write_path)

# -- Step 2)

# Define the schema to capture standard resume fields such as personal details, education, work experience, skills, etc.
cv_schema = {
    "personal_details": {
        "name": "string",
        "email": "string",
        "phone": "string",
        "address": "string"
    },
    "work_experience": [
        {
            "company_name": "string",
            "position": "string",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "description": "string"
        }
    ],
    "education": [
        {
            "institution_name": "string",
            "degree": "string",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "description": "string"
        }
    ],
    "technical_skills": ["string"],
    "soft_skills": ["string"],
    "certifications": ["string"],
    "languages": ["string"],
    "hobbies": ["string"]
}

extracted_invoice_json_path = "./data/outputs/intermediate/"
save_path = "./data/outputs/intermediate/transformed/"
main_transform(extracted_invoice_json_path, cv_schema, save_path)

# -- Step 3)

# Get database connection details from environment variables
db_config = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

# Read in the jsons and ingest/push to postgres
json_folder_path = "./data/outputs/intermediate/transformed/"
ingest_transformed_jsons_postgres(json_folder_path, db_config)

# Example usage with save to csv files instead
#save_folder_path = "./data/outputs/"
#ingest_transformed_jsons_to_csv_files(json_folder_path, save_folder_path)

# Example usage
save_file_path = "./data/outputs/wide_resumes_output.csv"
ingest_transformed_jsons_to_wide_csv(json_folder_path, save_file_path)


##### ------ MAIN CODE - END ------- ####

