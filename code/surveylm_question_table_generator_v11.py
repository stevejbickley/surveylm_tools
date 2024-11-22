##### ------ IMPORT FUNCTIONS + SETUP CODE - START ------- ####

from pydantic import BaseModel
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

'''
1) Add examples for the format/grouping of consent page(s) and introduction page(s) to the transform_data_into_schema function/middle_content of the prompt. Refer to unused input CVSs on the JSM project with full replications of all question blocks per paper, i.e. for guidance on one-shot or few-shot examples.
2) Refine/optimise the prompts in the extract_questions_from_text and extract_questions_from_image function, i.e., so they capture the data/information/knowledge and/or other elements of the framework of eight classes of variables that define the research context, which Hendrick (1991) discusses.
3) Guiding principles (i.e., that can be customised and get entered into both the system and user/message prompts), e.g. "clear, simple/intuitive and easy to understand", "short/concise", "with a clear, simple/intuitive narrative or storytelling and examples"
4) XXXX.
5) XXXX.
6) XXXX.
7) XXXX.
8) XXXX.
9) XXXX.
10) XXXX.
'''

##### ------ DEFINE FUNCTIONS - START ------- ####


client = OpenAI()

# SDKs for structured response extraction

# Define BASIC item schema (old/decommissioned)
class ItemBasic(BaseModel):
    question: str
    question_id: str
    answer_instruction: str

# Define Hendrick schema
class HendrickResearchContext(BaseModel):
    primary_information_focus: str
    participant_characteristics: str
    research_history: str
    cultural_historical_context: str
    physical_setting: str
    control_agent: str
    specific_task_variables: str
    modes_of_data_reduction_and_presentation: str


# Define Bickley et al. schema
class BickleyResearchContext(BaseModel):
    research_question_and_hypotheses: str
    study_design: str
    sample_size_and_characteristics: str
    operationalization_of_key_variables: str
    controls_randomization_blinding_and_bias_prevention: str
    environmental_context: str
    cultural_and_social_context: str
    temporal_context: str


# Define EXTENDED item schema
class ItemExtended(BaseModel):
    question: str
    question_id: str
    answer_instruction: str
    data_information_knowledge_and_context: str
    reasoning_justification_relevant: str


# EXTENDED with Hendrick (old/decommissioned - summarises the hendrick_context_framework at the question level)
#class ItemExtendedHendrickFramework(BaseModel):
#    question: str
#    question_id: str
#    answer_instruction: str
#    data_information_knowledge_and_context: str
#    reasoning_justification_relevant: str
#    hendrick_context_framework: HendrickResearchContext



# Extracting questions from supplied text
def extract_questions_from_text(text_input, question_type="", temperature_setting=0.7, max_tokens_setting=None, top_p_setting=1, presence_penalty_setting=0, n_setting=1, frequency_penalty_setting=0, logprobs_setting=False, model_setting="gpt-4o-mini", chain_of_thought=True, hendrick_context_framework=False, bickley_context_framework=False, reflection=True, guiding_principles="Clear, simple/intuitive and easy to understand; short/concise; fact-driven and evidence-based, grounded in accurate data and reliable sources."): # stop_setting=None, logit_bias_setting=None,
    """
     Extracts 'question', 'question_id', 'answer_instruction', and contextual variables from a supplied text input.
    Parameters:
    - text_input (str): The raw text data to be processed.
    - question_type (str): The specific type of question generation function to be used (e.g., "scenario prompts", "Likert scale prompts").
    - temperature_setting (float): Temperature setting for model creativity.
    - model (str): The model to be used for the task.
    - chain_of_thought (bool): Whether to include chain-of-thought reasoning in the response.
    - hendrick_context_framework (bool): Include Hendrick context if True.
    - bickley_context_framework (bool): Include Bickley context if True.
    - guiding_principles (str): Customizable guiding principles for the output. E.g., "Clear, simple/intuitive and easy to understand; short/concise", "Detailed and informative, with nuanced explanations and context for deeper understanding.", "Critical and analytical, highlighting key implications and dissecting complex ideas.", "Objective and neutral, presenting balanced perspectives without bias or opinion.", "Engaging and conversational, designed to be approachable and easy to follow, with a friendly tone.", "Concise yet comprehensive, ensuring brevity without losing critical details.", "Fact-driven and evidence-based, grounded in accurate data and reliable sources.", "Creative and explorative, pushing the boundaries of traditional thinking and encouraging innovative ideas.", "Clear and practical, using real-world examples to illustrate complex ideas.", "Ethically responsible, ensuring that responses adhere to moral standards and promote fairness.", "Strategic and goal-oriented, with a focus on practical outcomes and actionable steps.", Thought-provoking and open-ended, encouraging deeper exploration and reflective thinking.", "Polished and professional, adhering to formal standards with well-structured, authoritative responses."
    Returns:
    - dict: Extracted structured data in JSON format.
    """
    system_prompt = f"""
    You are a text-based extraction tool that processes text documents to extract structured question-answer pairs 
    for generating benchmarking datasets designed to empirically evaluate the performance and behaviors of AI models 
    (like large language models) across different psychological, cognitive, knowledge, ethical/moral, and value-based dimensions.
    Your instructions: 
    1. Extract all available information related to 'question' and 'answer instruction' pairs from the supplied text.
    2. Generate a unique and interpretable "question id" for each extracted question.
    3. Always include 'data_information_knowledge_and_context' with the exact text which you reference/cited from the supplied text that inspired the question-answer pair.
    4. Provide 'reasoning_justification_relevant' to explain why the question is deemed important/relevant. 
    """
    # Append additional frameworks based on input flags
    if hendrick_context_framework:
        system_prompt += """
        5. Include relevant elements from the Hendrick context framework.
        For each question-answer pair, also provide responses based on the following 8 research context variables:
        - Primary Information Focus: What was the key focus of the study (e.g., instructions, materials, or events forming the stimulus)?
        - Participant Characteristics: Describe any important participant demographics (e.g., gender, age, experience).
        - Research History: Include any prior experiences or motivations for participation.
        - Cultural and Historical Context: Capture the broader setting (e.g., historical, cultural influences).
        - Physical Setting: Provide information about the physical aspects (e.g., lighting, room setup).
        - Control Agent: Who controlled the experiment and how were participants managed?
        - Specific Task Variables: Detail any minute or practical details (e.g., fonts, colors used).
        - Modes of Data Reduction and Presentation: Specify how data was collected, reduced, and presented.
        """
        system_prompt += "6. Ensure the output is in JSON format, maintaining consistency across all questions."
        # Define the final QuestionExtraction schema to be used
        class QuestionExtraction(BaseModel):
            items: list[ItemExtended]
            hendrick_context_framework: HendrickResearchContext
    elif bickley_context_framework:
        system_prompt += """
        5. Include relevant elements from the Bickley context framework.
        For each question-answer pair, extract and provide key information based on the following categories:
        - Research Question and Hypotheses: Describe the main research questions and hypotheses of the study.
        - Study Design: Structure of the study, such as randomized controlled trials, quasi-experiments, or observational studies.
        - Sample Size and Characteristics: Information on the sample size and characteristics, including demographics (age, gender, cultural background, etc.).
        - Operationalization of Key Variables: Definitions and measures of key variables, such as independent, dependent, mediating, and moderating variables.
        - Controls, Randomization, Blinding, and Bias Prevention: Methods used to control for extraneous variables, randomization techniques, blinding methods, and steps to prevent bias.
        - Environmental Context: The physical or virtual setting of the study (e.g., lab, workplace).
        - Cultural and Social Context: Broader cultural and social influences that might affect participant behavior.
        - Temporal Context: Time period and relevant situational factors during which the study was conducted.
        """
        system_prompt += "6. Ensure the output is in JSON format, maintaining consistency across all questions."
        # Define the final QuestionExtraction schema to be used
        class QuestionExtraction(BaseModel):
            items: list[ItemExtended]
            bickley_context_framework: BickleyResearchContext
    elif reflection:
        system_prompt += """
        5. After extracting each question-answer instruction pair, evaluate the logic and clarity of each pair using the following reflexive check measures:
        - Completeness of instruction: On a scale from 0 to 100, evaluate how well the provided questions and answer instructions enable a clear, unambiguous response.
        - Ambiguity: On a scale from 0 to 100, rate the degree of ambiguity present in the questions and answer instructions. 0 = completely unambiguous; 100 = highly ambiguous.
        - Logical consistency: On a scale from 0 to 100, evaluate whether the question-answer pairs logically fits together and can be understood as a coherent whole.
        - Instruction set completeness: Check whether the set of provided answer instruction options (if any) or answer instruction elements cover the full range of possible responses or necessary steps to answer the questions.
        6. Provide the corrected or improved final version of the question-answer pairs, incorporating adjustments to improve clarity and logical structure based on the reflective evaluation. For example, by enriching the 'question' with the full 'data_information_knowledge_and_context'."""
        system_prompt += "7. Ensure the output is in JSON format, maintaining consistency across all questions."
        # Define the final QuestionExtraction schema to be used
        class QuestionExtraction(BaseModel):
            draft_items: list[ItemExtended]
            instruction_completeness: str
            ambiguity: str
            logical_consistency: str
            option_completeness: str
            final_items: list[ItemBasic]
    else:
        system_prompt += "5. Ensure the output is in JSON format, maintaining consistency across all questions."
        # Define the final QuestionExtraction schema to be used
        class QuestionExtraction(BaseModel):
            items: list[ItemExtended]
    # Add guiding principles
    system_prompt += f"""
        Ensure the following guiding principles are applied throughout the data extraction process:
        - {guiding_principles}
        """
    # Dynamic prompt message with the provided prompt_type
    user_content = f"Extract the 'question', 'question_id', and 'answer_instruction' pairs from the provided document based on the specific experimental methods used in the document. Ensure relevant contextual variables and outputs are included in your JSON output."
    if str(question_type) != "":
        user_content = f"Extract the 'question', 'question_id', and 'answer_instruction' pairs from the provided document based on/inspired by the following type(s) of question(s), empirical/experimental framework(s) and/or method(s): {question_type}. Ensure relevant contextual variables and outputs are included in your JSON output."
    end_content = ""
    if chain_of_thought:
        end_content = " Let's think step-by-step."
    # The final user message prompt
    user_message = f"{user_content} Here is the supplied text: {text_input}. {end_content}"
    #response = client.chat.completions.create(
    response = client.beta.chat.completions.parse(
        model=model_setting,
        #response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [{
                    "type": "text", "text": user_message
                }]
            }
        ],
        response_format=QuestionExtraction,
        max_tokens=max_tokens_setting,
        temperature=temperature_setting,
        #stop=stop_setting,
        top_p=top_p_setting,
        presence_penalty=presence_penalty_setting,
        n=n_setting,
        frequency_penalty=frequency_penalty_setting,
        #logit_bias=logit_bias_setting,
        logprobs=logprobs_setting,
    )
    return response.choices[0].message.content


# Encoding images as base64 for input to OpenAI chat completions API
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
def extract_questions_from_image(base64_image, question_type="", temperature_setting=0.7, max_tokens_setting=None, top_p_setting=1, presence_penalty_setting=0, n_setting=1, frequency_penalty_setting=0, logprobs_setting=False, model_setting="gpt-4o-mini", chain_of_thought=True, hendrick_context_framework=False, bickley_context_framework=False, reflection=True, guiding_principles="clear, simple/intuitive and easy to understand; short/concise"): # Spare/unused from OpenAI: stop_setting=[], logit_bias_setting=[],
    """
    Extracts 'question' and 'answer instruction' pairs from a base64-encoded image (PDF)
    using OCR, and outputs structured data in JSON format for machine learning datasets.
    Parameters:
    - base64_image (str): The base64 image string to be processed (e.g., a PDF).
    - question_type (str): The specific type of question generation function to be used (e.g., "scenario prompts", "Likert scale prompts").
    - temperature_setting (float): Temperature setting for model creativity.
    - model (str): The model to be used for the task.
    - chain_of_thought (bool): Whether to include chain-of-thought reasoning in the response.
    - hendrick_context_framework (bool): Include Hendrick context if True.
    - bickley_context_framework (bool): Include Bickley context if True.
    - guiding_principles (str): Customizable guiding principles for the output. E.g., "Clear, simple/intuitive and easy to understand; short/concise", "Detailed and informative, with nuanced explanations and context for deeper understanding.", "Critical and analytical, highlighting key implications and dissecting complex ideas.", "Objective and neutral, presenting balanced perspectives without bias or opinion.", "Engaging and conversational, designed to be approachable and easy to follow, with a friendly tone.", "Concise yet comprehensive, ensuring brevity without losing critical details.", "Fact-driven and evidence-based, grounded in accurate data and reliable sources.", "Creative and explorative, pushing the boundaries of traditional thinking and encouraging innovative ideas.", "Clear and practical, using real-world examples to illustrate complex ideas.", "Ethically responsible, ensuring that responses adhere to moral standards and promote fairness.", "Strategic and goal-oriented, with a focus on practical outcomes and actionable steps.", Thought-provoking and open-ended, encouraging deeper exploration and reflective thinking.", "Polished and professional, adhering to formal standards with well-structured, authoritative responses."
    Returns:
    - dict: Extracted structured data in JSON format.
    """
    system_prompt = f"""
        You aare an OCR-based extraction tool that processes images and PDF documents to extract structured question-answer pairs 
        for generating benchmarking datasets designed to empirically evaluate the performance and behaviors of AI models 
        (like large language models) across different psychological, cognitive, knowledge, ethical/moral, and value-based dimensions.
        Your instructions: 
        1. Extract all available information related to 'question' and 'answer instruction' pairs from the supplied text.
        2. Generate a unique and interpretable 'question id' for each extracted question.
        3. Always include 'data_information_knowledge_and_context' with the exact text which you reference/cited from the supplied text that inspired the question-answer pair.
        4. Provide 'reasoning_justification_relevant' to explain why the question is deemed important/relevant. 
        """
    # Append additional frameworks based on input flags
    if hendrick_context_framework:
        system_prompt += """
            5. Include relevant elements from the Hendrick context framework.
            For each question-answer pair, also provide responses based on the following 8 research context variables:
            - Primary Information Focus: What was the key focus of the study (e.g., instructions, materials, or events forming the stimulus)?
            - Participant Characteristics: Describe any important participant demographics (e.g., gender, age, experience).
            - Research History: Include any prior experiences or motivations for participation.
            - Cultural and Historical Context: Capture the broader setting (e.g., historical, cultural influences).
            - Physical Setting: Provide information about the physical aspects (e.g., lighting, room setup).
            - Control Agent: Who controlled the experiment and how were participants managed?
            - Specific Task Variables: Detail any minute or practical details (e.g., fonts, colors used).
            - Modes of Data Reduction and Presentation: Specify how data was collected, reduced, and presented.
            """
        system_prompt += "6. Ensure the output is in JSON format, maintaining consistency across all questions."
        # Define the final QuestionExtraction schema to be used
        class QuestionExtraction(BaseModel):
            items: list[ItemExtended]
            hendrick_context_framework: HendrickResearchContext # summarises the questions after seeing them all
    elif bickley_context_framework:
        system_prompt += """
            5. Include relevant elements from the Bickley context framework.
            For each question-answer pair, extract and provide key information based on the following categories:
            - Research Question and Hypotheses: Describe the main research questions and hypotheses of the study.
            - Study Design: Structure of the study, such as randomized controlled trials, quasi-experiments, or observational studies.
            - Sample Size and Characteristics: Information on the sample size and characteristics, including demographics (age, gender, cultural background, etc.).
            - Operationalization of Key Variables: Definitions and measures of key variables, such as independent, dependent, mediating, and moderating variables.
            - Controls, Randomization, Blinding, and Bias Prevention: Methods used to control for extraneous variables, randomization techniques, blinding methods, and steps to prevent bias.
            - Environmental Context: The physical or virtual setting of the study (e.g., lab, workplace).
            - Cultural and Social Context: Broader cultural and social influences that might affect participant behavior.
            - Temporal Context: Time period and relevant situational factors during which the study was conducted.
            """
        system_prompt += "6. Ensure the output is in JSON format, maintaining consistency across all questions."
        # Define the final QuestionExtraction schema to be used
        class QuestionExtraction(BaseModel):
            items: list[ItemExtended]
            bickley_context_framework: BickleyResearchContext # summarises the questions after seeing them all
    elif reflection:
        system_prompt += """
        5. After extracting each question-answer instruction pair, evaluate the logic and clarity of each pair using the following reflexive check measures:
        - Completeness of instruction: On a scale from 0 to 100, evaluate how well the provided questions and answer instructions enable a clear, unambiguous response.
        - Ambiguity: On a scale from 0 to 100, rate the degree of ambiguity present in the questions and answer instructions. 0 = completely unambiguous; 100 = highly ambiguous.
        - Logical consistency: On a scale from 0 to 100, evaluate whether the question-answer pairs logically fits together and can be understood as a coherent whole.
        - Instruction set completeness: Check whether the set of provided answer instruction options (if any) or answer instruction elements cover the full range of possible responses or necessary steps to answer the questions.
        6. Provide the corrected or improved final version of the question-answer pairs, incorporating adjustments to improve clarity and logical structure based on the reflective evaluation. For example, by enriching the 'question' with the full 'data_information_knowledge_and_context'."""
        system_prompt += "7. Ensure the output is in JSON format, maintaining consistency across all questions."
        # Define the final QuestionExtraction schema to be used
        class QuestionExtraction(BaseModel):
            draft_items: list[ItemExtended]
            instruction_completeness: str
            ambiguity: str
            logical_consistency: str
            option_completeness: str
            final_items: list[ItemBasic]
    else:
        system_prompt += "5. Ensure the output is in JSON format, maintaining consistency across all questions."
        # Define the final QuestionExtraction schema to be used
        class QuestionExtraction(BaseModel):
            items: list[ItemExtended]
    # Add guiding principles
    system_prompt += f"""
    Ensure the following guiding principles are applied throughout the data extraction process:
    - {guiding_principles}
    """
    # Dynamic prompt message with the provided prompt_type
    user_content = f"Extract the 'question', 'question_id', and 'answer_instruction' pairs from the provided document based on the specific experimental methods used in the document. Ensure relevant contextual variables and outputs are included in your JSON output."
    if str(question_type) != "":
        user_content = f"Extract the 'question', 'question_id', and 'answer_instruction' pairs from the provided document based on/inspired by the following type(s) of question(s): {question_type}. Ensure relevant contextual variables and outputs are included in your JSON output."
    end_content = ""
    if chain_of_thought:
        end_content = " Let's think step-by-step."
    # The final user message prompt
    user_message = f"{user_content}.{end_content}"
    #response = client.chat.completions.create(
    response = client.beta.chat.completions.parse(
        model=model_setting,
        #response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_message},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/png;base64,{base64_image}", "detail": "high"}}
                ]
            }
        ],
        response_format=QuestionExtraction,
        max_tokens=max_tokens_setting,
        temperature=temperature_setting,
        #stop=stop_setting,
        top_p=top_p_setting,
        presence_penalty=presence_penalty_setting,
        n=n_setting,
        frequency_penalty=frequency_penalty_setting,
        #logit_bias=logit_bias_setting,
        logprobs=logprobs_setting,
    )
    return response.choices[0].message.content



def extract_questions_from_images(base64_images, question_type="", temperature_setting=0.7, max_tokens_setting=None, top_p_setting=1, presence_penalty_setting=0, n_setting=1, frequency_penalty_setting=0, logprobs_setting=False, model_setting="gpt-4o-mini", chain_of_thought=True, hendrick_context_framework=False, bickley_context_framework=False, reflection=True, guiding_principles="clear, simple/intuitive and easy to understand; short/concise"): # Spare/unused from OpenAI: stop_setting=[], logit_bias_setting=[],
    """
    Extracts 'question' and 'answer instruction' pairs from a list of base64-encoded images (PDF)
    using OCR, and outputs structured data in JSON format for machine learning datasets.
    Parameters:
    - base64_images (list of str): A list of base64 image strings to be processed (e.g., PDF pages as images).
    - question_type (str): The specific type of question generation function to be used (e.g., "scenario prompts", "Likert scale prompts").
    - temperature_setting (float): Temperature setting for model creativity.
    - model (str): The model to be used for the task.
    - chain_of_thought (bool): Whether to include chain-of-thought reasoning in the response.
    - hendrick_context_framework (bool): Include Hendrick context if True.
    - bickley_context_framework (bool): Include Bickley context if True.
    - guiding_principles (str): Customizable guiding principles for the output. E.g., "Clear, simple/intuitive and easy to understand; short/concise", "Detailed and informative, with nuanced explanations and context for deeper understanding.", "Critical and analytical, highlighting key implications and dissecting complex ideas.", "Objective and neutral, presenting balanced perspectives without bias or opinion.", "Engaging and conversational, designed to be approachable and easy to follow, with a friendly tone.", "Concise yet comprehensive, ensuring brevity without losing critical details.", "Fact-driven and evidence-based, grounded in accurate data and reliable sources.", "Creative and explorative, pushing the boundaries of traditional thinking and encouraging innovative ideas.", "Clear and practical, using real-world examples to illustrate complex ideas.", "Ethically responsible, ensuring that responses adhere to moral standards and promote fairness.", "Strategic and goal-oriented, with a focus on practical outcomes and actionable steps.", Thought-provoking and open-ended, encouraging deeper exploration and reflective thinking.", "Polished and professional, adhering to formal standards with well-structured, authoritative responses."
    Returns:
    - dict: Extracted structured data in JSON format.
    """
    system_prompt = f"""
        You aare an OCR-based extraction tool that processes images and PDF documents to extract structured question-answer pairs 
        for generating benchmarking datasets designed to empirically evaluate the performance and behaviors of AI models 
        (like large language models) across different psychological, cognitive, knowledge, ethical/moral, and value-based dimensions.
        Your instructions: 
        1. Extract all available information related to 'question' and 'answer instruction' pairs from the supplied text.
        2. Generate a unique and interpretable 'question id' for each extracted question.
        3. Always include 'data_information_knowledge_and_context' with the exact text which you reference/cited from the supplied text that inspired the question-answer pair.
        4. Provide 'reasoning_justification_relevant' to explain why the question is deemed important/relevant. 
        """
    # Append additional frameworks based on input flags
    if hendrick_context_framework:
        system_prompt += """
            5. Include relevant elements from the Hendrick context framework.
            For each question-answer pair, also provide responses based on the following 8 research context variables:
            - Primary Information Focus: What was the key focus of the study (e.g., instructions, materials, or events forming the stimulus)?
            - Participant Characteristics: Describe any important participant demographics (e.g., gender, age, experience).
            - Research History: Include any prior experiences or motivations for participation.
            - Cultural and Historical Context: Capture the broader setting (e.g., historical, cultural influences).
            - Physical Setting: Provide information about the physical aspects (e.g., lighting, room setup).
            - Control Agent: Who controlled the experiment and how were participants managed?
            - Specific Task Variables: Detail any minute or practical details (e.g., fonts, colors used).
            - Modes of Data Reduction and Presentation: Specify how data was collected, reduced, and presented.
            """
        system_prompt += "6. Ensure the output is in JSON format, maintaining consistency across all questions."
        # Define the final QuestionExtraction schema to be used
        class QuestionExtraction(BaseModel):
            items: list[ItemExtended]
            hendrick_context_framework: HendrickResearchContext # summarises the questions after seeing them all
    elif bickley_context_framework:
        system_prompt += """
            5. Include relevant elements from the Bickley context framework.
            For each question-answer pair, extract and provide key information based on the following categories:
            - Research Question and Hypotheses: Describe the main research questions and hypotheses of the study.
            - Study Design: Structure of the study, such as randomized controlled trials, quasi-experiments, or observational studies.
            - Sample Size and Characteristics: Information on the sample size and characteristics, including demographics (age, gender, cultural background, etc.).
            - Operationalization of Key Variables: Definitions and measures of key variables, such as independent, dependent, mediating, and moderating variables.
            - Controls, Randomization, Blinding, and Bias Prevention: Methods used to control for extraneous variables, randomization techniques, blinding methods, and steps to prevent bias.
            - Environmental Context: The physical or virtual setting of the study (e.g., lab, workplace).
            - Cultural and Social Context: Broader cultural and social influences that might affect participant behavior.
            - Temporal Context: Time period and relevant situational factors during which the study was conducted.
            """
        system_prompt += "6. Ensure the output is in JSON format, maintaining consistency across all questions."
        # Define the final QuestionExtraction schema to be used
        class QuestionExtraction(BaseModel):
            items: list[ItemExtended]
            bickley_context_framework: BickleyResearchContext # summarises the questions after seeing them all
    elif reflection:
        system_prompt += """
        5. After extracting each question-answer instruction pair, evaluate the logic and clarity of each pair using the following reflexive check measures:
        - Completeness of instruction: On a scale from 0 to 100, evaluate how well the provided questions and answer instructions enable a clear, unambiguous response.
        - Ambiguity: On a scale from 0 to 100, rate the degree of ambiguity present in the questions and answer instructions. 0 = completely unambiguous; 100 = highly ambiguous.
        - Logical consistency: On a scale from 0 to 100, evaluate whether the question-answer pairs logically fits together and can be understood as a coherent whole.
        - Instruction set completeness: Check whether the set of provided answer instruction options (if any) or answer instruction elements cover the full range of possible responses or necessary steps to answer the questions.
        6. Provide the corrected or improved final version of the question-answer pairs, incorporating adjustments to improve clarity and logical structure based on the reflective evaluation. For example, by enriching the 'question' with the full 'data_information_knowledge_and_context'."""
        system_prompt += "7. Ensure the output is in JSON format, maintaining consistency across all questions."
        # Define the final QuestionExtraction schema to be used
        class QuestionExtraction(BaseModel):
            draft_items: list[ItemExtended]
            instruction_completeness: str
            ambiguity: str
            logical_consistency: str
            option_completeness: str
            final_items: list[ItemBasic]
    else:
        system_prompt += "5. Ensure the output is in JSON format, maintaining consistency across all questions."
        # Define the final QuestionExtraction schema to be used
        class QuestionExtraction(BaseModel):
            items: list[ItemExtended]
    # Add guiding principles
    system_prompt += f"""
    Ensure the following guiding principles are applied throughout the data extraction process:
    - {guiding_principles}
    """
    # Dynamic prompt message with the provided prompt_type
    user_content = f"Extract the 'question', 'question_id', and 'answer_instruction' pairs from the provided images/PDFs based on the specific experimental methods used in the images/PDFs. Ensure relevant contextual variables and outputs are included in your JSON output."
    if str(question_type) != "":
        user_content = f"Extract the 'question', 'question_id', and 'answer_instruction' pairs from the provided images/PDFs based on/inspired by the following type(s) of question(s): {question_type}. Ensure relevant contextual variables and outputs are included in your JSON output."
    end_content = ""
    if chain_of_thought:
        end_content = " Let's think step-by-step."
    # The final user message prompt
    user_message = f"{user_content}.{end_content}"
    # Initialize the messages list for the OpenAI API call
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {"type": "text",
                 "text": "You are an OCR-based extraction tool that processes images and PDF documents to extract structured question-answer pairs."}
            ]
        }
    ]
    # Loop through the base64 images and append them as individual image URLs in the message payload
    for base64_image in base64_images:
        messages[1]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}",
                "detail": "high"
            }
        })
    # Add the main task description as the second part of the message
    messages[1]["content"].append({
        "role": "user",
        "content": [
            {"type": "text",
             "text": user_message}
        ]
    })
    #response = client.chat.completions.create(
    response = client.beta.chat.completions.parse(
        model=model_setting,
        #response_format={"type": "json_object"},
        messages=messages,
        response_format=QuestionExtraction,
        max_tokens=max_tokens_setting,
        temperature=temperature_setting,
        #stop=stop_setting,
        top_p=top_p_setting,
        presence_penalty=presence_penalty_setting,
        n=n_setting,
        frequency_penalty=frequency_penalty_setting,
        #logit_bias=logit_bias_setting,
        logprobs=logprobs_setting,
    )
    return response.choices[0].message.content


def extract_from_multiple_pages(base64_images, original_filename, output_directory, guiding_principles="Clear, simple/intuitive and easy to understand; short/concise; fact-driven and evidence-based, grounded in accurate data and reliable sources."):
    entire_invoice = []
    for base64_image in base64_images:
        invoice_json = extract_questions_from_image(base64_image, model_setting="gpt-4o-2024-08-06", guiding_principles=guiding_principles, temperature_setting=0.2)
        # Check if the result is None/empty or if it is NOT an instance of str, bytes, or bytearray
        if not invoice_json: # or not isinstance(invoice_json, (str, bytes, bytearray)):
            continue # If yes, skip this iteration or step
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


def extract_from_multiple_pages(base64_images, original_filename, output_directory, guiding_principles="Clear, simple/intuitive and easy to understand; short/concise; fact-driven and evidence-based, grounded in accurate data and reliable sources."):
    invoice_json = extract_questions_from_images(base64_images, model_setting="gpt-4o-2024-08-06", guiding_principles=guiding_principles, temperature_setting=0.2)
    # Check if the result is None/empty or if it is NOT an instance of str, bytes, or bytearray
    if not invoice_json: # or not isinstance(invoice_json, (str, bytes, bytearray)):
        continue # If yes, skip this iteration or step
    invoice_data = json.loads(invoice_json)
    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)
    # Construct the output file path
    output_filename = os.path.join(output_directory, original_filename.replace('.pdf', '_extracted.json'))
    # Save the entire_invoice list as a JSON file
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(invoice_data, f, ensure_ascii=False, indent=4)
    return output_filename


def main_extract(read_path, write_path):
    for filename in os.listdir(read_path):
        if filename[-4:] == '.pdf':
            file_path = os.path.join(read_path, filename)
            if os.path.isfile(file_path):
                base64_images = pdf_to_base64_images(file_path)
                extract_from_multiple_pages(base64_images, filename, write_path)



# SDK for structured response extraction
class Item(BaseModel):
    question: str
    question_id: str
    answer_instruction: str


class AgentReasoning(BaseModel):
    items: list[Item]
    epistemology_ontology_methodology: str
    questions_hypotheses: str
    methods: str


def transform_data_into_schema(json_raw, json_schema, temperature_setting=0.7, max_tokens_setting=None, top_p_setting=1, presence_penalty_setting=0, n_setting=1, frequency_penalty_setting=0, logprobs_setting=False, model_setting="gpt-4o-mini", chain_of_thought=True, group_questions=True, max_group_size="", guiding_principles="clear, simple/intuitive and easy to understand; short/concise"): # stop_setting=None, logit_bias_setting=None,
    """
    Extracts 'question' and 'answer instruction' pairs from a supplied json input
    and outputs structured data in JSON format for machine learning datasets.
    Parameters:
    - json_raw (json object/file): The raw json data to be processed.
    - json_schema (json object/schema, python dictionary): XXXX.
    - temperature_setting (float): Temperature setting for model creativity.
    - model (str): The model to be used for the task.
    - chain_of_thought (bool): Whether to include chain-of-thought reasoning in the response.
    - group_questions (bool): Whether to include task-specific prompting to group similar/like questions into question blocks in the response.
    - guiding_principles (str): Customizable guiding principles for the output. E.g., "Clear, simple/intuitive and easy to understand; short/concise", "Detailed and informative, with nuanced explanations and context for deeper understanding.", "Critical and analytical, highlighting key implications and dissecting complex ideas.", "Objective and neutral, presenting balanced perspectives without bias or opinion.", "Engaging and conversational, designed to be approachable and easy to follow, with a friendly tone.", "Concise yet comprehensive, ensuring brevity without losing critical details.", "Fact-driven and evidence-based, grounded in accurate data and reliable sources.", "Creative and explorative, pushing the boundaries of traditional thinking and encouraging innovative ideas.", "Clear and practical, using real-world examples to illustrate complex ideas.", "Ethically responsible, ensuring that responses adhere to moral standards and promote fairness.", "Strategic and goal-oriented, with a focus on practical outcomes and actionable steps.", Thought-provoking and open-ended, encouraging deeper exploration and reflective thinking.", "Polished and professional, adhering to formal standards with well-structured, authoritative responses.
    Returns:
    - dict: Extracted structured data in JSON format/python dictionary like the following, {"items": [{"question", "question id", "answer instruction"}], "epistemology_ontology_methodology", "questions_hypotheses", "methods"}.
    """
    if str(json_schema) == "":
        json_schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string"
                            },
                            "question_id": {
                                "type": "string"
                            },
                            "answer_instruction": {
                                "type": "string"
                            }
                        },
                        "required": ["question", "question_id", "answer_instruction"]
                    }
                },
                "epistemology_ontology_methodology": {
                    "type": "string"
                },
                "questions_hypotheses": {
                    "type": "string"
                },
                "methods": {
                    "type": "string"
                }
            },
            "required": ["items", "epistemology_ontology_methodology", "questions_hypotheses", "methods"]
        }
    system_prompt = f"""
        You are a data transformation tool that processes JSON data and transforms it into structured JSON objects according to the provided schema. 
        The schema is designed for generating structured question-answer instruction pairs, as well as capturing epistemological, ontological, and methodological insights and justification/reasoning.
        - Your first task is to extract questions, question IDs, and corresponding answer instructions from the raw JSON data and format them as 'Item' objects.
        - You second task is to map any relevant epistemological, ontological, or methodological insights from the raw data to the 'epistemology_ontology_methodology' (i.e., summarize the scientific paradigms, worldviews, or approaches underlying the extracted questions and answers. Focus on identifying the philosophical foundations, such as the nature of knowledge (epistemology), reality (ontology), and research strategies (methodology)), 'questions_hypotheses' (i.e., capture the core research questions or hypotheses implied by the extracted questions and answers. Reflect on the primary aims or problems the questions are designed to investigate), and 'methods' (i.e., summarize the scientific or research methods relevant to the extracted questions and answers. Specify the data collection, analysis, or experimental techniques that seem central to answering the identified questions) fields in the 'AgentReasoning' schema.
        Important notes:
        - Not all input data will fit the schema exactly, so omit irrelevant data or use null values as necessary.
        - Translate all data into English if it's not already.
        - Ensure the formatting is correct, such as dates being formatted as YYYY-MM-DD.
        - If certain sections of the raw JSON resemble parts of the schema but don't match exactly, use your judgment to map the data to the closest matching field.
        Here is the 'AgentReasoning' schema you should follow: 
        {json_schema}
        """
    # Add guiding principles
    system_prompt += f"""
        Ensure the following guiding principles are applied throughout the data extraction process:
        - {guiding_principles}
        """
    end_content = ""
    middle_content = ""
    if chain_of_thought:
        end_content = " Let's think step-by-step."
    if group_questions:
        middle_content_start = " Where applicable, group related or similarly structured questions into a single entry in the output."
        middle_content_end = ""
        if max_group_size != "":
            middle_content_start = f" Where applicable, group related or similarly structured questions into a single entry in the output with a strict maximum group size of {max_group_size} questions."
            middle_content_end = f" Remember: there is a strict maximum group size of {max_group_size} questions."
        middle_content_middle = f"""
        For each group, create one combined question, a range of question IDs (e.g., 'Q18_to_Q26'), and a consolidated answer instruction that explains how to answer all questions in the group.
        When grouping questions:
        1. Identify questions with similar themes, phrasing, or patterns (e.g., 'On this list are various groups of people. Could you please mention any that you would not like to have as neighbors? (Code an answer for each group):').
        2. Combine these related questions into a single row, ensuring that the question clearly explains the set as a whole (e.g., the 'question' would be something 'On this list are various groups of people. Could you please mention any that you would not like to have as neighbors? (Code an answer for each group):').
        3. Format the combined answer instruction to begin with: "Code XX for each XX, and return a list where each element of the list corresponds to your coded number for each XX." - Replace 'XX' with appropriate terms based on the specific dataset (e.g., "Code a number on the provided scale for each statement, and return a list where each element corresponds to your coded number for each statement:").
        4. List the relevant question IDs as a range (e.g., 'Q18_to_Q26').
        5. Ensure the combined answer instruction includes numbered sub-items corresponding to each question in the group, formatted as: "<br>1. [First item]: 1 (Mentioned), 2 (Not mentioned);<br>2. [Second item]: 1 (Mentioned), 2 (Not mentioned);" and so on.
        6. Preserve clarity by including specific details for each option within the group.
        For Example:
            - Example 1: 
                - question: "On this list are various groups of people. Could you please mention any that you would not like to have as neighbors? (Code an answer for each group):"
                - question id: "Q18_to_Q26"
                - answer instruction: "Code one number on the provided scale for each of the 9 statements, and return a list where each element of the list corresponds to your coded number for each of the 9 statements:<br>1. Drug addicts: 1 (Mentioned), 2 (Not mentioned);<br>2. People of a different race: 1 (Mentioned), 2 (Not mentioned);<br>3. People who have AIDS: 1 (Mentioned), 2 (Not mentioned;<br>4. Immigrants/foreign workers: 1 (Mentioned), 2 (Not mentioned;<br>5. Homosexuals: 1 (Mentioned), 2 (Not mentioned;<br>6. People of a different religion: 1 (Mentioned), 2 (Not mentioned;<br>7. Heavy drinkers: 1 (Mentioned), 2 (Not mentioned;<br>8. Unmarried couples living together: 1 (Mentioned), 2 (Not mentioned;<br>9. People who speak a different language: 1 (Mentioned), 2 (Not mentioned."
            - Example 2: 
                - question: "The following questions ask about your general trust in others:"
                - question id: "Q1_to_Q18"
                - answer instruction: "Code one number on the provided scale for each of the 16 statements, and return a list where each element of the list corresponds to your coded number for each of the 16 statements:<br>1. In dealing with strangers, it is better to be cautious until they have provided evidence that they are trustworthy: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly)<br>2. Most people keep their promises:  1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>3. Most people answer questions honestly: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>4. Most people say what they believe themselves and not what they think you want to hear: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>5. Most people tell the truth about the limits of their knowledge: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>6. Most people cannot be counted on to do what they say they will do: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>7. These days, you must be alert or someone is likely to take advantage of you: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>8. I normally rely on the task-related skills and abilities of others: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>9. I would not follow the advice of others on important issues.: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>10. I confidently allow other people to make decisions for me during an absence: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>11. I would rely on task-related judgments made by others: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>12. I usually monitor others when they have to do something for me: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>13. I generally prefer to work as part of a team: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>14. I am eager to work with others in a team: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>15. I find that working as a member of a team increases my ability to perform effectively: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly).<br>16. I feel that given a choice, I would prefer to work in a team rather than work alone: 1 (Disagree Strongly), 2 (Disagree), 3 (Neither Agree nor Disagree), 4 (Agree), 5 (Agree Strongly)."
            - Example 3:
                - question: "The future of top-tier sports content
        Purpose of this Study
        We examine how digital innovation, technology, and sustainability will impact the consumption of top-tier sports content by the end of the decade. Specifically, we want to focus on the year 2030.
        This study facilitates an anonymous online discussion among selected experts.
        We identified you as an expert on this topic and highly value your personal opinion. In return, you will be among the first to get our results. Moreover, we hope that you will benefit from participation through a valuable exchange with your peers.
        The survey - conducted in collaboration with DFL Deutsche Fußball Liga - will take 25-30 minutes of your time.
        Thank you very much for your participation!
        Principal investigator:
        Prof. Dr. XXXX XXXX,
        XXXX@XXXX.edu
        Project coordinators:
        XXXX XXXX,
        XXXX@XXXX.edu
        Apl. Prof. Dr. XXXX,
        XXXX@XXXX.edu
        This study is conducted by XXXX. It is sponsored by XXXX. If you need any further information, please contact the project coordinators."
                - question id: "PRODUCT_V0_PURPOSE"
                - answer instruction: "Please click the arrow below to proceed to the next question."
        Note: If no grouping is possible, please output the data in its original structure.
        """
        middle_content = middle_content_start + middle_content_middle + middle_content_end
    # The final user message prompt
    user_message = f"Transform the following raw JSON data according to the provided 'AgentReasoning' schema. Ensure all data is in English and formatted as required. Here is the raw JSON: {json_raw}.{middle_content}{end_content}"
    response = client.beta.chat.completions.parse(
        model=model_setting,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_message
                    }
                ]
            }
        ],
        response_format=AgentReasoning,
        max_tokens=max_tokens_setting,
        temperature=temperature_setting,
        #stop=stop_setting,
        top_p=top_p_setting,
        presence_penalty=presence_penalty_setting,
        n=n_setting,
        frequency_penalty=frequency_penalty_setting,
        #logit_bias=logit_bias_setting,
        logprobs=logprobs_setting,
    )
    return json.loads(response.choices[0].message.content)


def main_transform(extracted_invoice_json_path, json_schema, save_path, guiding_principles="Clear, simple/intuitive and easy to understand; short/concise; fact-driven and evidence-based, grounded in accurate data and reliable sources."):
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
            transformed_json = transform_data_into_schema(json_raw, json_schema, model_setting="gpt-4o-2024-08-06", guiding_principles=guiding_principles)
            # Save the transformed JSON to the save directory
            transformed_filename = f"transformed_{filename}"
            transformed_file_path = os.path.join(save_path, transformed_filename)
            with open(transformed_file_path, 'w', encoding='utf-8') as f:
                json.dump(transformed_json, f, ensure_ascii=False, indent=2)


def save_to_csv(data, columns, filename):
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(filename, index=False)


def ingest_transformed_jsons_to_csv_files(json_folder_path, save_folder_path):
    items_data = []
    main_data = []
    for filename in os.listdir(json_folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(json_folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Collect main details
            main_data.append((
                data["epistemology_ontology_methodology"],
                data["questions_hypotheses"],
                data["methods"]
            ))
            # Collect items (question data)
            for item in data["items"]:
                items_data.append((
                    item["question"],
                    item["question_id"],
                    item["answer_instruction"]
                ))
    # Ensure the save directory exists
    os.makedirs(save_folder_path, exist_ok=True)
    # Save main data and items data to CSV files
    save_to_csv(main_data, ["epistemology_ontology_methodology", "questions_hypotheses", "methods"],
                os.path.join(save_folder_path, "main_data.csv"))
    save_to_csv(items_data, ["question", "question id", "answer instruction"],
                os.path.join(save_folder_path, "items_data.csv"))


def ingest_transformed_jsons_postgres(json_folder_path, db_config):
    # Connect to PostgreSQL
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    # Create necessary tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS MainData (
        main_id SERIAL PRIMARY KEY,
        epistemology_ontology_methodology TEXT,
        questions_hypotheses TEXT,
        methods TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Items (
        item_id SERIAL PRIMARY KEY,
        main_id INTEGER REFERENCES MainData(main_id),
        question TEXT,
        question_id VARCHAR(255),
        answer_instruction TEXT
    )
    ''')
    # Loop over all JSON files and insert data
    for filename in os.listdir(json_folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(json_folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Insert main data
            cursor.execute('''
            INSERT INTO MainData (epistemology_ontology_methodology, questions_hypotheses, methods) 
            VALUES (%s, %s, %s) RETURNING main_id
            ''', (
                data["epistemology_ontology_methodology"],
                data["questions_hypotheses"],
                data["methods"]
            ))
            main_id = cursor.fetchone()[0]
            # Insert each item in the 'items' array
            for item in data["items"]:
                cursor.execute('''
                INSERT INTO Items (main_id, question, question_id, answer_instruction) 
                VALUES (%s, %s, %s, %s)
                ''', (
                    main_id,
                    item["question"],
                    item["question_id"],
                    item["answer_instruction"]
                ))
    conn.commit()
    cursor.close()
    conn.close()


##### ------ MAIN CODE - START ------- ####

# -- Step 1)
read_path = "./data/inputs/pdfs/"
write_path = "./data/outputs/intermediate/"

main_extract(read_path, write_path)

# -- Step 2)

# Define the json_schema
json_schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string"
                            },
                            "question_id": {
                                "type": "string"
                            },
                            "answer_instruction": {
                                "type": "string"
                            }
                        },
                        "required": ["question", "question_id", "answer_instruction"]
                    }
                },
                "epistemology_ontology_methodology": {
                    "type": "string"
                },
                "questions_hypotheses": {
                    "type": "string"
                },
                "methods": {
                    "type": "string"
                }
            },
            "required": ["items", "epistemology_ontology_methodology", "questions_hypotheses", "methods"]
        }

extracted_json_path = "./data/outputs/intermediate/"
save_path = "./data/outputs/intermediate/transformed/"
main_transform(extracted_json_path, json_schema, save_path)

# -- Step 3)

# - Option A) Example usage with save to csv files
json_folder_path = "./data/outputs/intermediate/transformed/"
save_folder_path = "./data/outputs/"
ingest_transformed_jsons_to_csv_files(json_folder_path, save_folder_path)

# - Option B) Example usage with save to postgresql (Optional)
# Get database connection details from environment variables
#db_config = {"dbname": "XXXX", "user": "XXXX", "password": "XXXX", "host": "XXXX", "port": "1234"}

# Read in the jsons and ingest/push to postgres
#json_folder_path = "./data/outputs/intermediate/transformed/"
#ingest_transformed_jsons_postgres(json_folder_path, db_config)

##### ------ MAIN CODE - END ------- ####