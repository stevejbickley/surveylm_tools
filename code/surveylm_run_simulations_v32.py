##### ------ IMPORT FUNCTIONS ------- ####

import os, sys, csv, time, glob, re, datetime,subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from tqdm import tqdm
import numpy as np
import pandas as pd
import random
import openpyxl

##### ------ DEFINE FUNCTIONS ------- ####

# 1) Write pandas dataframe to csv file
def dataframe_to_csv(filename, DataFrame):
    """Export entire DataFrame to csv."""
    output = DataFrame
    output.to_csv(filename, index=False)


# 2) Get html source source and write to txt file
def get_html(filename, url, browser):
    if os.path.exists(filename):  # CHANGE for euro / champions / europa / world cup
        pass
    else:
        try:
            browser.get(url)  # navigate to start url
            time.sleep(2)
            html = browser.page_source  # extract the HTML source code of start url
            with open(filename, 'w', encoding='utf8') as f:
                f.write(html)
        except:
            pass


# 3) Function to find indices of strings within list
def find_indices(main_list, search_strings):
    return [i for i, item in enumerate(main_list) if item.text in search_strings]


# 4) Function to find the element from known elements list via text
def find_element_from_elements_via_text(parent_element, xpath_for_elements, target_element_text, max_retry=5, retry_time=3):
    for _ in range(max_retry):  # Retry up to 5 times with default setting of 'max_retry'
        try:
            elements = WebDriverWait(parent_element, 20).until(EC.presence_of_all_elements_located((By.XPATH, xpath_for_elements)))
            target_elements = []
            targets_found = 0
            targets_possible = len(elements)
            for element in elements:
                if str(element.text.split('\n')[0]) == str(target_element_text):
                    target_elements.append(element)
                    targets_found += 1
            # Now return the output(s) back to the user
            if targets_found == 0:
                print(f"\nWarning: No element(s) were found with the 'find_element_from_elements_via_text' function using your provided inputs to target: {target_element_text}")
                print(f"{str(len(range(max_retry)) - _ - 1)} retries left before declaring defeat!")
                time.sleep(retry_time)
            elif targets_found == 1:
                print(f"\nSuccess!\n1 x 'SINGLE' element was successfully found with the 'find_element_from_elements_via_text' function using your provided inputs to target: {target_element_text}")
                return target_elements[0]
            else:  # if targets_found is more than 1, function returns a list of "target_element" values
                if targets_found == targets_possible:
                    print(f"\nWarning: All elements matched with the 'find_element_from_elements_via_text' function using your provided inputs to target: {target_element_text}")
                print("\nWarning: 1 x 'LIST' of elements was successfully found with the 'find_element_from_elements_via_text' function using your provided inputs to target:" + f"{target_element_text}")
                print("\nIf this was not intended, please review your provided inputs.")
                return [target_elements, targets_found, targets_possible]
        except Exception as e:
            try:
                print(f"Error finding target: {target_element_text} with exception: {e}.")
            except:
                print(f"Error finding target: {target_element_text}.")
            print(f"{str(len(range(max_retry)) - _ - 1)} retries left before declaring defeat!")
            time.sleep(retry_time)
    print(f"Error: not able to find the target '{target_element_text}' after {str(max_retry)} retries.")
    return None


# 6) Function to setup and open selenium driver/browser
def setup_selenium(download_path):
    # Set up Chrome options
    options = Options()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # Set up the default download directory
    prefs = {
        "download.default_directory": download_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    # Path to chromedriver
    #chromedriver_path = "/opt/homebrew/Caskroom/chromedriver/126.0.6478.126/chromedriver-mac-arm64/chromedriver"
    # Set up the service
    #service = ChromeService(executable_path=chromedriver_path)
    service = ChromeService()
    # Initialize the WebDriver
    driver = webdriver.Chrome(service=service, options=options)
    return driver


# 7) Function to wait until an element is clickable before clicking it
def wait_and_click_element(parent_element, element, wait_time=10, retry_time=3, max_retry=5):
    for _ in range(max_retry):
        try:
            WebDriverWait(parent_element, wait_time).until(EC.visibility_of(element))
            WebDriverWait(parent_element, wait_time).until(EC.element_to_be_clickable(element))
            element.click()
            print(f"Success: that's a click!")
            return True
        except TimeoutException:
            print(f"Error: Element not visible or not clickable within {wait_time} seconds")
            print(f"{str(len(range(max_retry)) - _ - 1)} retries left before declaring defeat!")
            time.sleep(retry_time)
            continue
        except Exception as e:
            try:
                print(f"Error clicking the element: {e}")
            except:
                print("Error clicking the element.")
            print(f"{str(len(range(max_retry)) - _ - 1)} retries left before declaring defeat!")
            time.sleep(retry_time)
            continue
    print(f"Error: not able to click the element '{element}' after {str(max_retry)} retries.")
    return False


# 8) Function to check and add any missing keys
def ensure_all_keys(parameters):
    # Define all of the required keys
    required_keys = ["batch_survey", "reset_parameters", "test_run", "test_q", "model",
                     "temperature_low", "temperature_high", "max_retries", "agent_role",
                     "justification", "critic", "agent_role_prob_dist", "justification_prob_dist",
                     "critic_prob_dist", "justification_prompt", "critic_prompt", "agent_count"]
    for key in required_keys:
        if key not in parameters:
            parameters[key] = ""


# 9A) (Old) Function to log into the SurveyLM platform using provided credentials
# NOTE: you can either supply these directly or set environment variables, create config ini files, etc
# E.g., export SURVEYLM_USERNAME="Your Name", etc
def login(driver, user_name, user_id, email, password, api_key,wait_time=3):
    # First, make sure you are in the "Platform" page
    wait_and_click_element(driver,find_element_from_elements_via_text(driver,".//a[@data-testid='stSidebarNavLink']",'Platform'))
    time.sleep(wait_time)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, ".//input[@aria-label='Your Name']"))).send_keys(user_name)
    driver.find_element(By.XPATH, ".//input[@aria-label='Username']").send_keys(user_id)
    driver.find_element(By.XPATH, ".//input[@aria-label='Email Address']").send_keys(email)
    driver.find_element(By.XPATH, ".//input[@aria-label='Password']").send_keys(password)
    driver.find_element(By.XPATH, ".//input[@aria-label='OpenAI API Key']").send_keys(api_key)
    time.sleep(wait_time)
    wait_and_click_element(driver,WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, ".//p[contains(text(), 'Login')]"))))


# 9B) (New) Function to log into the SurveyLM platform using provided credentials
def new_login(driver, email, password, api_key,wait_time=3):
    # First, make sure you are in the "Platform" page
    wait_and_click_element(driver,find_element_from_elements_via_text(driver,".//a[@data-testid='stSidebarNavLink']",'Platform'))
    time.sleep(wait_time)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, ".//input[@aria-label='Email']"))).send_keys(email)
    driver.find_element(By.XPATH, ".//input[@aria-label='Password']").send_keys(password)
    driver.find_element(By.XPATH, ".//input[@aria-label='OpenAI API Key']").send_keys(api_key)
    time.sleep(wait_time)
    wait_and_click_element(driver,WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, ".//p[contains(text(), 'Sign In')]"))))


# 10) Function to upload survey and agent Excel files
def upload_files(driver, survey_path, agent_path,wait_time=0.5):
    WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, ".//button[contains(text(), 'Browse files')]")))
    driver.find_element(By.XPATH, ".//section[@role='button' and @aria-label='Upload survey data']").find_element(By.XPATH,".//input[@type='file']").send_keys(survey_path)
    time.sleep(wait_time); wait_for_event_completion(driver, 'survey_upload', wait_time=1);  # wait until upload is completed
    driver.find_element(By.XPATH, ".//section[@role='button' and @aria-label='Upload agent profile data']").find_element(By.XPATH, ".//input[@type='file']").send_keys(agent_path)
    time.sleep(wait_time); wait_for_event_completion(driver, 'agent_upload', wait_time=1);  # wait until upload is completed


#Function to set the temperature range
def set_temperature(driver, lower_temp, upper_temp):
    # Wait for the slider to be present
    slider_elements = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, ".//div[@data-baseweb='slider']")))
    for slider_element in slider_elements:
        try:
            # Ensure the slider element is the temperature slider
            slider_element.find_element(By.XPATH, ".//div[@aria-label='Temperature']")
            # Locate the slider thumbs
            thumb_container = slider_element.find_elements(By.XPATH, ".//div[@aria-label='Temperature']")
            lower_thumb = thumb_container[0]
            upper_thumb = thumb_container[1]
            # Calculate the move offsets
            slider_width = slider_element.size['width']
            lower_offset = (float(lower_temp) / 1.5) * float(slider_width)
            upper_offset = (float(upper_temp) / 1.5) * float(slider_width)
            # Create action chain to move the sliders
            actions = ActionChains(driver)
            # Reset sliders to the start position
            actions.click_and_hold(lower_thumb).move_by_offset(-((float(lower_thumb.text)/ 1.5) * float(slider_width))+lower_thumb.size['width'], 0).release().perform()
            actions.click_and_hold(upper_thumb).move_by_offset(-((float(upper_thumb.text)/ 1.5) * float(slider_width))+upper_thumb.size['width'], 0).release().perform()
            # Move sliders to the new positions
            actions.click_and_hold(upper_thumb).move_by_offset(upper_offset, 0).release().perform()
            actions.click_and_hold(lower_thumb).move_by_offset(lower_offset, 0).release().perform()
        except Exception as e:
            print(f"Error setting temperature: {e}")
            pass


# Function to clear text input fields manually by backspacing until they are empty strings
def clear_input_field(element,wait_time=0):
    wait_and_click_element(driver, element, max_retry=1)
    while element.get_attribute('value') != '':
        element.send_keys(Keys.BACKSPACE)
        time.sleep(wait_time)


# Basic function to interact with dropdowns that are multiple-choice to select one option
def select_dropdown_option(driver, parent_element, option_text, wait_time=0.1, retry_time = 2, max_retry=5):
    for _ in range(max_retry):
        if not wait_and_click_element(driver, find_element_from_elements_via_text(driver, ".//li[@role='option']", option_text,max_retry=1), max_retry=1):
            # Wait some time
            time.sleep(retry_time)
            # Try to re-open/re-click the drop-down list
            wait_and_click_element(driver, parent_element, max_retry=5)
            # Wait some time
            time.sleep(retry_time)
            # Try to re-click the option from the drop-down list, if not then retry again
            if not wait_and_click_element(driver,find_element_from_elements_via_text(driver, ".//li[@role='option']", option_text,max_retry=1), max_retry=1):
                # Wait some time
                time.sleep(retry_time)
                continue
        else:
            break
    time.sleep(wait_time)


# Function to clear all probability distribution and justification/critic or custom prompt text inputs
def clear_all_text_inputs(driver, ignore_api_key=True):
    # Text inputs for the probability distributions first then the text areas or custom prompts for the justification/critic prompts
    elements = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, ".//div[@data-testid='stTextInput']")))
    # Some validation before proceeding
    if ignore_api_key:
        elements = elements[1:]
    elements = elements + WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, ".//div[@data-testid='stTextArea']")))
    for element in elements:
        if element.text == '':
            continue
        try:
            clear_input_field(element.find_element(By.XPATH, ".//input[@type='text']"))
        except:
            continue


# Function to clear all with multiselect buttons
def clear_all_options_from_dropdown(driver, dropdown_xpath, wait_time=0.1):
    # Wait for the multiselect container to be present
    multiselect_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, dropdown_xpath)))
    # Wait for the "Clear all" button to be present and clickable
    clear_all_button = WebDriverWait(multiselect_element, 20).until(EC.element_to_be_clickable((By.XPATH, ".//svg[1][@fill-rule='evenodd']")))
    # Click the "Clear all" button
    wait_and_click_element(driver,clear_all_button,max_retry=2)
    time.sleep(wait_time)


# Function to clear all with multiselect buttons
def clear_all_multiselect_inputs(driver, wait_time=0.1):
    elements = driver.find_elements(By.XPATH, ".//span[@data-baseweb='tag']")
    for iii in range(len(elements)):
        try:
            wait_and_click_element(driver, driver.find_elements(By.XPATH, ".//span[@data-baseweb='tag']")[0].find_element(By.XPATH,".//span[@role='presentation']"), max_retry=1)
            time.sleep(wait_time)
        except:
            pass


# Convenience wrapper function to find the platform tab WebElements and return the specific one you want
def find_platform_tab(driver, target_tab):
    element = find_element_from_elements_via_text(driver, ".//button[@data-baseweb='tab']", target_tab)
    return element


# Convenience wrapper function to find the simulation menu WebElements and return the specific one you want
def find_simulation_menu(driver, target_tab):
    element = find_element_from_elements_via_text(driver, ".//details", target_tab)
    return element


# Function to open the simulation menus if they are not already open the platform tabs
def open_simulation_submenu(driver, target_tab,wait_time=0.5):
    element = find_simulation_menu(driver, target_tab)
    if int(element.size['height']) < 100: # if not already open then click to open it
        wait_and_click_element(driver,element)
        time.sleep(wait_time)
    else:
        print(f"Target menu '{target_tab}' is already open.")


# Function to open the download results tab if not already open
def open_results_submenu(driver, wait_time=0.5):
    element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH,".//div[@role='tabpanel' and @aria-labelledby='tabs-bui61-tab-3']"))).find_element(By.XPATH,".//details")
    if int(element.size['height']) < 100:  # if not already open then click to open it
        wait_and_click_element(driver, element.find_element(By.XPATH,".//summary"))
        time.sleep(wait_time)
    else:
        print(f"The 'Results' sub-menu is already open.")


# Function to input simulation parameters
def set_parameters(driver, parameters):
    # Ensure there are no missing key-value pairs from the parameters dictionary
    ensure_all_keys(parameters)
    # First, make sure you are in the "Simulation" menu
    wait_and_click_element(driver,find_platform_tab(driver, 'Simulation')); time.sleep(1);
    # Open up the "Simulation" sub-menus
    open_simulation_submenu(driver,'Model Parameters'); time.sleep(0.5);
    open_simulation_submenu(driver, 'Synthetic Profile Construction'); time.sleep(0.5);
    # Now clear all the multi-select options and text inputs across all submenus, incl. any previously inputted probability distributions and custom prompts
    clear_all_multiselect_inputs(driver); time.sleep(1); clear_all_text_inputs(driver); time.sleep(2);
    ## Now we can finally start to set parameters
    # First locate the 'Model Parameters' sub-menu in the 'Simulation' tab
    model_params_menu = find_simulation_menu(driver, 'Model Parameters'); time.sleep(5); #model_params_menu.click(); time.sleep(3); # NOTE: not sure if this will close the model_params_menu or not.. we don't want to close it but we do want to click somewhere in this container to focus on it in that sense..
    # 1) Enter the text inputs, if any...
    for param in ['agent_role_prob_dist','justification_prob_dist','critic_prob_dist','justification_prompt','critic_prompt']:
        data = parameters[param]
        if data != "":
            if param == "agent_role_prob_dist": # Find the probability distribution WebElements for 'Role','Justification',and 'Critic' inputs
                agent_role_prob_dist_input = find_element_from_elements_via_text(model_params_menu,".//div[@data-testid='stTextInput']",'Probability distribution for the Role parameter')
                agent_role_prob_dist_input.find_element(By.XPATH, ".//input[@type='text']").send_keys(data)
            elif param == "justification_prob_dist":
                justification_prob_dist_input = find_element_from_elements_via_text(model_params_menu,".//div[@data-testid='stTextInput']",'Probability distribution for the Justification parameter')
                justification_prob_dist_input.find_element(By.XPATH, ".//input[@type='text']").send_keys(data)
            elif param == "critic_prob_dist":
                critic_prob_dist_input = find_element_from_elements_via_text(model_params_menu,".//div[@data-testid='stTextInput']",'Probability Distribution for the Critic parameter')  # NOTE: capital "D" rather than lower case
                critic_prob_dist_input.find_element(By.XPATH, ".//input[@type='text']").send_keys(data)
            elif param == "justification_prompt":
                justification_prompt_input = find_element_from_elements_via_text(model_params_menu,".//div[@data-testid='stTextArea']",'Justification Prompt')
                justification_prompt_input.find_element(By.XPATH, ".//textarea[@aria-label='Justification Prompt']").send_keys(data)
            elif param == "critic_prompt":
                critic_prompt_input = find_element_from_elements_via_text(model_params_menu,".//div[@data-testid='stTextArea']",'Critic Prompt')
                critic_prompt_input.find_element(By.XPATH, ".//textarea[@aria-label='Critic Prompt']").send_keys(data)
            else:
                continue
        else:
            continue
    # 2) Enter the checkbox inputs, if any...
    for param in ['batch_survey','reset_parameters','test_run']: # 'Batch survey','Reset all parameters','Test run'
        data = parameters[param]
        if param == 'batch_survey':
            element_name = 'Batch survey'
        elif param == 'reset_parameters':
            element_name = 'Reset all parameters'
        elif param == 'test_run':
            element_name = 'Test run'
        else:
            continue
        # Now find the specific WebElement
        element = find_element_from_elements_via_text(model_params_menu, ".//label[@data-baseweb='checkbox']",element_name)
        # If user has defined a value then enter it:
        if data != "":
            if str(element.find_element(By.XPATH, f".//input[@aria-label='{element_name}']").get_attribute('aria-checked')) != str(parameters[param]).lower():
                wait_and_click_element(driver,element)
            else:
                continue
        else: # Otherwise, set the default value:
            if param in ['batch_survey','test_run']:
                if str(element.find_element(By.XPATH, f".//input[@aria-label='{element_name}']").get_attribute('aria-checked')) != str(True).lower():
                    wait_and_click_element(driver,element)
            elif param == 'reset_parameters':
                if str(element.find_element(By.XPATH, f".//input[@aria-label='{element_name}']").get_attribute('aria-checked')) != str(False).lower():
                    wait_and_click_element(driver,element)
            else:
                continue
    # 3) Enter the number entry inputs, if any...
    for param in ['test_q', 'max_retries', 'agent_count']:
        data = parameters[param]
        if param == 'test_q':
            element_name = 'Number of questions for the test run'
        elif param == 'max_retries':
            element_name = 'Max retry attempts'
        elif param == 'agent_count':
            element_name = 'Number of Agents'
        else:
            continue
        try: # Now find the specific WebElement
            element = find_element_from_elements_via_text(model_params_menu, ".//div[@data-testid='stNumberInput']",element_name)
            clear_input_field(element.find_element(By.XPATH, f".//input[@aria-label='{element_name}']"))
        except:
            pass
        if data != "": # If user has defined a value then enter it:
            element.find_element(By.XPATH, f".//input[@aria-label='{element_name}']").send_keys(data)
        else: # Otherwise, set the default value:
            if param in ['test_q', 'max_retries']:
                element.find_element(By.XPATH, f".//input[@aria-label='{element_name}']").send_keys(str(5))
            else:
                continue
    # 4) Enter into the temperature slider
    set_temperature(driver, parameters['temperature_low'], parameters['temperature_high'])
    # 5) Next is the dropdown lists/boxes covering first the single-selection or single answer dropdowns only
    for param in ['model']: # Multiple choice, single answer only
        data = parameters[param]
        if param == 'model':
            element_name = 'Model'
        else:
            continue
        # Find the drop-down list
        element = find_element_from_elements_via_text(model_params_menu, ".//div[@data-testid='stSelectbox']",element_name)
        if data != "":
            if str(element.text.split('\n')[-1]) != str(data):
                # Open the drop-down list
                wait_and_click_element(driver, element)
                time.sleep(0.5)
                select_dropdown_option(driver, element, data)
                time.sleep(3)
            else:
                continue
        else: # Default option(s)
            if str(element.text.split('\n')[-1]) != "GPT-3.5-Turbo":
                # Open the drop-down list
                wait_and_click_element(driver, element)
                time.sleep(0.5)
                select_dropdown_option(driver, element, "GPT-3.5-Turbo")
                time.sleep(3)
            else:
                continue
    # 6) Next is the dropdown lists/boxes covering now the multi-selection or dropdowns where multiple answers are allowed
    for param in ['agent_role', 'justification', 'critic']: # Multiple choice, multiple answers allowed
        data = parameters[param]
        if param == 'agent_role':
            element_name = 'Role'
        elif param == 'justification':
            element_name = 'Justification'
        elif param == 'critic':
            element_name = 'Critic'
        else:
            continue
        # Find the drop-down list
        element = find_element_from_elements_via_text(driver, ".//div[@data-testid='stMultiSelect']", element_name)
        # Open the drop-down list
        wait_and_click_element(driver, element.find_element(By.XPATH,".//div[@data-baseweb='select']"))
        time.sleep(0.5)
        if data != "":
            for dat in data:
                if dat in element.text.split('\n'):
                    continue
                else:
                    select_dropdown_option(driver, element.find_element(By.XPATH,".//div[@data-baseweb='select']"), dat)
        else: # Default options - NOTE: need to finish
            if param == 'agent_role':
                for dat in ['Person', 'Assistant', 'Language Model']:
                    select_dropdown_option(driver, element.find_element(By.XPATH,".//div[@data-baseweb='select']"), dat)
            elif param in ['justification','critic']:
                for dat in ['Yes', 'No']:
                    select_dropdown_option(driver, element.find_element(By.XPATH,".//div[@data-baseweb='select']"), dat)


# Function to initiate the estimation process and waits for completion
def run_estimation(driver,wait_time=3):
    find_element_from_elements_via_text(driver, ".//button[@kind='secondaryFormSubmit']", 'Estimate Cost').click()
    time.sleep(wait_time); wait_for_event_completion(driver,'estimation',wait_time=wait_time);


# Function to wait for event completion
def wait_for_event_completion(driver, which_process, wait_time=5, max_faults=10):
    """
    Wait for a specified event to complete and print progress updates.
    Parameters:
    driver (webdriver): The Selenium WebDriver instance.
    which_process (str): The process to wait for. Should be one of: 'estimation', 'start_simulation', 'stop_simulation',
                         'survey_upload', 'agent_upload', 'erase_data', 'page_refresh'.
    wait_time (int): The time to wait between checks in seconds.
    """
    success_messages = {
        'estimation': 'Estimation completed successfully',
        'start_simulation': 'Simulation completed successfully',
        'stop_simulation': 'The simulation has been stopped',
        'survey_upload': 'Survey data uploaded successfully',
        'agent_upload': 'agents were created successfully',
        'erase_data': 'The data was erased successfully',
        'page_refresh': 'The app has been refreshed'
    }
    if which_process not in success_messages:
        print('Error: You have called an undefined process in the wait_for_event_completion function.')
    success_text = success_messages[which_process]
    done = 0; fault = 0;
    while (not done > 0) and (not fault > max_faults):
        try:
            time.sleep(wait_time)  # Wait for the specified time before checking again
            alert_text = get_UI_alert(driver)
        except Exception as e:
            alert_text = None
            print(f"Error getting UI alert: {e}")
            fault += 1
        if not alert_text:
            try:
                progress_update = get_simulation_progress(driver)
                if progress_update:
                    print(f"The process of '{which_process}' is still running. Progress is at {progress_update}")
                else:
                    print('Error: No progress update available.')
                    fault += 1
                    #break
            except Exception as e:
                print(f"Error getting simulation progress: {e}")
                fault += 1
                #break
        else:
            if success_text in alert_text:
                print(f"The process of '{which_process}' completed successfully. Here is the UI message: {alert_text}")
                done += 1
                #break
            elif any(error_text in alert_text for error_text in ['Something went wrong', 'There is no data to erase',
                                                                 'No completed simulation data was found',
                                                                 'You have not started a survey yet']): # 'Error', 'Warning'
                print(f"Warning: Something went wrong during the process of '{which_process}'. Here is the UI message: {alert_text}")
                done += 1
                #break
            elif 'Initializing concurrent requests' in alert_text:
                print(f"The process of '{which_process}' is still initializing.")
            else:
                print(f"Unexpected UI message: {alert_text}")
                fault += 1
                #break


# Function to retrieve the current progress of the simulation from the UI and print it to the terminal
def get_UI_alert(driver):
    try:
        element = driver.find_element(By.XPATH, ".//div[@data-testid='stAlert']")
        return element.text
    except:
        print("Warning: No message displayed on the UI currently.")
        return None


# Function to retrieve the current progress of the simulation from the UI and print it to the terminal
def get_simulation_progress(driver):
    try:
        element = driver.find_element(By.XPATH, ".//div[@data-testid='stProgress']")
        #print(f"Progress is currently at {element.text}")
        return element.text
    except:
        print("Warning: Current simulation is either finished/complete, caused an error/failed, or does not exist.")
        return None


# Function to initiate the simulation process and waits for completion
def run_simulation(driver,wait_time=10):
    wait_and_click_element(driver,find_element_from_elements_via_text(driver, ".//button[@kind='secondaryFormSubmit']", 'Run Simulation'))
    time.sleep(wait_time); wait_for_event_completion(driver, 'start_simulation', wait_time=wait_time);


# Function to refresh button the page internally to SurveyLM platform
def internal_page_refresh_soft(driver,wait_time=2):
    find_element_from_elements_via_text(driver, ".//button[@kind='secondaryFormSubmit']", 'Refresh Page')
    time.sleep(wait_time); wait_for_event_completion(driver, 'page_refresh', wait_time=wait_time);


# Function to refresh button the page internally to SurveyLM platform
def internal_page_refresh_hard(driver,wait_time=4):
    elements = driver.find_elements(By.XPATH, ".//a[@data-testid='stSidebarNavLink']") # THIS IS THE CODE I CANNOT CHANGE??
    for element in elements:
        if str(element.text) == str('Concept'):
            wait_and_click_element(driver, element)
        if str(element.text) == str('Platform'):
            wait_and_click_element(driver, element)
        time.sleep(wait_time)


# Function to refresh button the page internally to SurveyLM platform
def stop_simulation(driver,wait_time=5):
    wait_and_click_element(driver,find_element_from_elements_via_text(driver, ".//button[@kind='secondaryFormSubmit']", 'Stop Simulation'))
    time.sleep(wait_time); wait_for_event_completion(driver, 'stop_simulation', wait_time=wait_time)


# Function to navigate to the results tab and downloads the results files
def download_results(driver,wait_time=5):
    wait_and_click_element(driver,find_platform_tab(driver, 'Results'))
    time.sleep(3)
    # Open up the "Results" sub-menu
    #open_results_submenu(driver)
    # Now lets try to download the data
    wait_and_click_element(driver,find_element_from_elements_via_text(driver, ".//button[@data-testid='baseButton-secondaryFormSubmit']","View Simulation Data")); time.sleep(wait_time);
    try:
        #open_results_submenu(driver)
        wait_and_click_element(driver,find_element_from_elements_via_text(driver,".//button[@kind='secondary' and @data-testid='baseButton-secondary']","Download Usage Data", max_retry=2), max_retry=2)
    except:
        print("No 'usage' data available for download.")
    wait_and_click_element(driver,find_element_from_elements_via_text(driver, ".//button[@data-testid='baseButton-secondaryFormSubmit']","View Simulation Data")); time.sleep(wait_time);
    try:
        #open_results_submenu(driver)
        wait_and_click_element(driver,find_element_from_elements_via_text(driver, ".//button[@kind='secondary' and @data-testid='baseButton-secondary']","Download Completed Data", max_retry=2), max_retry=2)
    except:
        print("No 'completed' data available for download.")
    wait_and_click_element(driver,find_element_from_elements_via_text(driver, ".//button[@data-testid='baseButton-secondaryFormSubmit']","View Simulation Data")); time.sleep(wait_time);
    try:
        #open_results_submenu(driver)
        wait_and_click_element(driver,find_element_from_elements_via_text(driver, ".//button[@data-testid='baseButton-secondaryFormSubmit']","Download Uncompleted Data", max_retry=1), max_retry=1);
    except:
        print("No 'uncompleted' data available for download.")


# Supporting functions for the 'process_all_files' function below
def extract_pattern(filename):
    """Extract the study pattern from the filename."""
    # Ensure we're only working with the filename, not the full path
    if '/' in filename:
        filename = filename.split('/')[-1]
    parts = filename.split("_")
    pattern = ""
    # Look for the "STUDY" part
    for i, part in enumerate(parts):
        if part == "STUDY":
            # Include the part before "STUDY"
            pattern = parts[i - 1] + "_STUDY"
            # Check if the part after "STUDY" begins with a number
            if i + 1 < len(parts) and parts[i + 1][0].isdigit():
                pattern += "_" + parts[i + 1]
            break
    return pattern


def match_files(files, pattern):
    """Match question files with agent files based on the pattern."""
    question_files = [f for f in files if f.startswith(f"questions_input_{pattern}")]
    agent_files = [f for f in files if f.startswith(f"sample_profiles_input_{pattern}")]
    return question_files, agent_files


# Function to convert relative to absolute path
def to_absolute_path(path):
    """Convert a relative path to an absolute path."""
    return os.path.abspath(path)


# Function to iterate through all survey and agent file combinations in the current working directory and its
# subdirectories, performing the complete automation process for each pair - NOTE: not sure about this code...
# With specific_pattern input variable/parameter you can call e.g., ['SRIVASTAVA_STUDY','TARIQ_STUDY_1','TARIQ_STUDY_2'] or e.g., 'YAN_STUDY_1B' to focus on these specific files/patterns and running those associated simulations
def process_all_files(driver, parameters, download_path, start_folder=".", wait_time=5, backwards_process=False, crawl_subfolders=True, specific_pattern=None):
    for root, dirs, files in os.walk(start_folder):
        # If not crawling subfolders, clear the dirs list to prevent os.walk from entering subdirectories
        if not crawl_subfolders:
            dirs.clear()
        # Extract unique patterns from the filenames
        patterns = set()
        for file in files:
            if file.startswith("questions_input_") or file.startswith("sample_profiles_input_"):
                pattern = extract_pattern(file)
                patterns.add(pattern)
        # Convert patterns to a list and reverse if backwards_process is True
        patterns = list(patterns)
        if backwards_process:
            patterns.reverse()
        # If specific_pattern is provided, filter the patterns
        if specific_pattern:
            if isinstance(specific_pattern, str):
                specific_pattern = [specific_pattern]
            specific_pattern = [str(pattern) for pattern in specific_pattern]
            patterns = [str(pattern) for pattern in patterns if str(pattern) in specific_pattern]
        # Now begin the main run of simulations according to the matched question_files and agent_files of each pattern in patterns
        for pattern in patterns:
            question_files, agent_files = match_files(files, pattern)
            # Reverse the order of question_files and agent_files if backwards_process is True
            #if backwards_process:
                #question_files.reverse()
                #agent_files.reverse()
            for question_file in question_files:
                for agent_file in agent_files:
                    question_path = to_absolute_path(os.path.join(root, question_file))
                    agent_path = to_absolute_path(os.path.join(root, agent_file))
                    if os.path.exists(question_path) and os.path.exists(agent_path):
                        driver.quit() # Close the old WebDriver
                        # Initialize the WebDriver (e.g., for Chrome)
                        driver = setup_selenium(download_path); time.sleep(wait_time)
                        # Open the URL - note: use "https://surveylm.panalogy-lab.com/Platform" for the online version
                        #driver.get("https://surveylm.panalogy-lab.com/Platform"); time.sleep(wait_time);
                        driver.get("http://localhost:8501/Concept"); time.sleep(wait_time);
                        login(driver, username, userid, email, password, api_key)
                        #new_login(driver, email, password, api_key)
                        upload_files(driver, question_path, agent_path)
                        set_parameters(driver, parameters)
                        run_estimation(driver)
                        run_simulation(driver)
                        download_results(driver)
                        #internal_page_refresh_hard(driver,wait_time=5)


##### ------ NOW RUN THE SCRIPT ------- ####

# Run script
if __name__ == "__main__":
    # Get current working directory
    CURR_PATH = os.getcwd()
    # Load credentials from environment variables
    username = SURVEYLM_USERNAME = "Steve Bickley"
    userid = os.getenv('SURVEYLM_USERID')
    email = os.getenv('SURVEYLM_EMAIL')
    password = os.getenv('SURVEYLM_PASSWORD')
    api_key = os.getenv('SURVEYLM_APIKEY')
    # Set parameters dictionary
    parameters = {"batch_survey": False, "reset_parameters": False, "test_run": False, "test_q": 5,
                  "model": "GPT-3.5-Turbo",
                  "temperature_low": 0.00, "temperature_high": 0.00, "max_retries": 5,
                  "agent_role": ["Person"], "justification": ["Yes", "No"],
                  "critic": ["No"]}
    #              "agent_role_prob_dist": "0.8;0.2", "justification_prob_dist": "0.8;0.2"}
    # Setup the download path for the simulation outputs
    download_path = CURR_PATH + "/data/simulations/"
    driver = setup_selenium(download_path)
    try:
        # Run for all files in the start_folder
        process_all_files(driver=driver, parameters=parameters, download_path=download_path, start_folder=CURR_PATH + '/simulation_outputs/inputs/', backwards_process=False, crawl_subfolders=False, specific_pattern=None)
        # (Optional) Run only select files in the start_folder
        #process_all_files(driver=driver, parameters=parameters, download_path=download_path, start_folder=CURR_PATH + '/simulation_outputs/inputs/', backwards_process=False, crawl_subfolders=False,specific_pattern=['SRIVASTAVA_STUDY', 'TARIQ_STUDY_1', 'TARIQ_STUDY_2'])
    except:
        print('Oh no! An error has occurred...')
    # Now let's close the driver
    finally:
        driver.quit()


##### ------ TESTING ONLY ------- ####

# Get current working directory
#CURR_PATH = os.getcwd()

# Define the other key file paths
#question_path = CURR_PATH + '/simulation_outputs/inputs/questions_input_DOOTSON_STUDY_ROBOT_H1.xlsx'
#agent_path = CURR_PATH + '/simulation_outputs/inputs/sample_profiles_input_DOOTSON_STUDY_v2_agents_output.xlsx'
#download_path = CURR_PATH + "/simulation_outputs/"

# simulation and outputs
allfiles = glob.glob(download_path + '/inputs/questions_input_'+'*.xlsx') + glob.glob(download_path + '/inputs/sample_profiles_input_'+'*.xlsx')
allfiles_questions_only = glob.glob(download_path + '/inputs/questions_input_'+'*.xlsx')
allfiles_profiles_only = glob.glob(download_path + '/inputs/sample_profiles_input_'+'*.xlsx')

# Load credentials from environment variables
#username = SURVEYLM_USERNAME = "Steve Bickley"
#userid = os.getenv('SURVEYLM_USERID')
#email = os.getenv('SURVEYLM_EMAIL')
#password = os.getenv('SURVEYLM_PASSWORD')
#api_key = os.getenv('SURVEYLM_APIKEY')

#Note: 
#You can either supply these directly or set environment variables, create config .ini files, etc.

#For example: 
#export SURVEYLM_USERNAME="Your Name"

#Alternatively: 
#echo 'export SURVEYLM_USERNAME="Steven Bickley"' >> ~/.zshrc
#source ~/.zshrc
#username = os.getenv('SURVEYLM_USERNAME')

# Initialise the "driver" and the associated selenium session
#driver = setup_selenium(download_path)

# Open the URL - note: use "https://surveylm.panalogy-lab.com/Platform" for the online version
#driver.get("http://localhost:8501/Concept")
#time.sleep(5)

# Login to SurveyLM platform
#login(driver,username,userid,email,password,api_key)

# Set parameters dictionary - default
#parameters = {"batch_survey":True,"reset_parameters":False,"test_run":True,"test_q":5,"model":"GPT-3.5-Turbo",
#              "temperature_low":0.00,"temperature_high":0.50,"max_retries":5,
#              "agent_role":["Person","Assistant","Language Model"],"justification":["Yes","No"],"critic":["Yes","No"],
#              "agent_role_prob_dist":"0.33;0.33;0.34","justification_prob_dist":"0.5;0.5","critic_prob_dist":"0.5;0.5",
#              "justification_prompt":"Person:The justification should consider and remain grounded in your profile;Assistant:The justification should consider and remain grounded in the person's profile;Language Model:The justification should consider and remain grounded in your knowledge and training",
#              "critic_prompt":"Person:The analysis should be coherent and thoughtful, whilst remaining grounded in your profile;Assistant:The analysis should be coherent and thoughtful, whilst remaining grounded in the person's profile;Language Model:The analysis should be coherent and thoughtful, whilst remaining grounded in your knowledge and training as a language model"}


# Set parameters dictionary
#parameters = {"batch_survey": True, "reset_parameters": False, "test_run": False, "test_q": 5,
#                  "model": "GPT-3.5-Turbo",
#                  "temperature_low": 0.00, "temperature_high": 0.00, "max_retries": 5,
#                  "agent_role": ["Person","Assistant"], "justification": ["Yes", "No"],
#                  "critic": ["No"],
#                  "agent_role_prob_dist": "0.8;0.2", "justification_prob_dist": "0.8;0.2"}



# Run process all files function
#process_all_files(driver, parameters, CURR_PATH + '/simulation_outputs/inputs/')

# Upload agent and survey files
#upload_files(driver, question_path, agent_path, wait_time=1)

# Get parameters ready for simulation
#set_parameters(driver, parameters)

# Run estimation
#run_estimation(driver,wait_time=1)

# Run simulation
#run_simulation(driver,wait_time=1)

# Call the download_results function
#download_results(driver)

# Close the WebDriver after completion
#driver.quit()

# ----------------------------------------------------------------------------------------------------------------------

