import requests
import json
import os
import logging
import datetime
import argparse

# GitHub API base URL
API_URL = "https://api.github.com"

# Repository input file delimiter 
INPUT_FILE_DELIMITER = "::"  
SETTINGS_DELIMITER = ","

# GitHub token and organization/repo details
GITHUB_TOKEN = None
CERT_PATH = None
ORG_NAME = "source-org-test"
#REPO_NAME = "usmg-capgemini-migration-utilities" 
# Headers for GitHub API authentication
headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
# Load repositories and property-value mappings from a file
def load_repositories_from_file(repo_file_path):
    repos = []
    try:
        with open(repo_file_path, "r", encoding='utf-8-sig') as file:
            for line in file:
                # Split into repo, properties, and settings parts using the same delimiter
                parts = line.strip().split(INPUT_FILE_DELIMITER)
                if len(parts) >= 2:
                    repo_detail = parts[0]
                    properties = parts[1]
                    repo_settings = parts[2] if len(parts) > 2 else ''
                    repos.append((repo_detail, properties, repo_settings))
    except Exception as e:
        log_and_print(f"Error reading the file {repo_file_path}: {e}", "error")
    return repos
 
def log_and_print(message, log_level='info'):
    RED = '\033[31m'
    GREEN = '\033[32m'
    RESET = '\033[0m'
    # Get the current datetime with seconds
    log_datetime = datetime.datetime.now().strftime('%d%b%Y_%H%M%S')
    # Log the message to the file based on the log level
    if log_level == 'error':
        logging.error(f": {message}")
        print(f"{RED}{log_datetime}: {message} {RESET}") # Print the message to the console with the formatted datetime & color 
    elif log_level == 'success':
        logging.info(f":{message}")  
        print(f"{GREEN}{log_datetime}: {message} {RESET}") # Print the message to the console with the formatted datetime & color
    else:
        logging.info(f": {message}")
        print(f"{log_datetime}: {message}") # Print the message to the console with the formatted datetime


def process_repo_settings(full_repo_path, settings_str):
    try:
        # Extract org name and repo name from full path
        if '/' in full_repo_path:
            org_name, repo_name = full_repo_path.split('/')
        else:
            # If no organization specified, use the default org
            org_name = "source-org-test"  # You can make this configurable if needed
            repo_name = full_repo_path
        
        # Parse settings string
        settings_dict = {}
        if settings_str:
            for setting in settings_str.split(','):
                if '=' in setting:
                    key, value = setting.split('=')
                    # Convert string 'true'/'false' to boolean for certain settings
                    if key == 'delete_branch_on_merge':
                        settings_dict[key] = value.lower() == 'true'
        
        # URL to update repository settings
        repo_settings_url = f"{API_URL}/repos/{org_name}/{repo_name}"
        
        if settings_dict:
            log_and_print(f"Updating repository settings for '{full_repo_path}'...")
            
            # Make the API request to update repository settings
            response = requests.patch(
                repo_settings_url,
                headers=headers,
                json=settings_dict,
                verify=CERT_PATH if CERT_PATH else False
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                log_and_print(f"✓ Successfully updated repository settings for '{full_repo_path}'","success")
                for key, value in settings_dict.items():
                    log_and_print(f"  - {key}: {value}","success")
            else:
                log_and_print(f"✗ Failed to update repository settings - status code: {response.status_code}","error")
                log_and_print(response.json(),"error")
    except Exception as e:
        log_and_print(f"Error processing repository settings for '{full_repo_path}': {str(e)}", "error")


def custom_setting_update(full_repo_path, custom_properties):
    try:
        # Extract org name and repo name from full path
        if '/' in full_repo_path:
            org_name, repo_name = full_repo_path.split('/')
        else:
            # If no organization specified, use the default org
            org_name = "source-org-test"  # You can make this configurable if needed
            repo_name = full_repo_path
        
        # URL to update repository settings
        custom_property_url = f"{API_URL}/repos/{org_name}/{repo_name}/properties/values"
        
        # Make the API request
        response = requests.patch(
            custom_property_url,
            headers=headers,
            json=custom_properties,
            verify=CERT_PATH if CERT_PATH else False
        )
        
        # Check if the request was successful
        if response.status_code == 204:
            log_and_print(f"...Successfully set custom property [] for repository '{full_repo_path}'...","success")
        else:
            log_and_print(f"...Failed to set custom property - status code: {response.status_code}","error")
            log_and_print(response.json(),"error")
    except Exception as e:
        log_and_print(f"Error updating custom properties for '{full_repo_path}': {str(e)}", "error")


def main():
    # Setup argument parser for command-line flags
    parser = argparse.ArgumentParser(description=f"...Branch Protection ruleset creation for repositories...")
    parser.add_argument('-r', '--repo_file',type=str,required=True,help="Path to the CSV file containing list of repositories")
    parser.add_argument('-o', '--output_folder', type=str, default='./output', help="Path to the folder where the migration summary will be saved (default: './output').")
    parser.add_argument('-c', '--cert', type=str, help="Path to the certificate file (optional)")
    parser.add_argument('-t', '--token_env', type=str, default='GITHUB_TOKEN', help="Name of environment variable containing GitHub token (default: GITHUB_TOKEN)")
    
    args = parser.parse_args()
    
    # Get GitHub token from specified environment variable
    global GITHUB_TOKEN, CERT_PATH
    GITHUB_TOKEN = os.getenv(args.token_env)
    CERT_PATH = args.cert
    
    global headers
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get the current date and time, and format it
    current_datetime = datetime.datetime.now().strftime('%d%b%Y_%H%M')

    # Get the input path of the filename from the argument - Input file containing repo names
    list_repos_file_path = args.repo_file 
    output_log_folder = args.output_folder
    
    # Create output directory if it doesn't exist
    os.makedirs(output_log_folder, exist_ok=True)
    
    # Extract the base filename without the extension
    base_filename = os.path.splitext(os.path.basename(list_repos_file_path))[0]
    
    # Log file name 
    branchrule_log_file = f"{output_log_folder}/LOG_{base_filename}_{current_datetime}.log"
    # Set up the logger
    logging.basicConfig(filename=f"{branchrule_log_file}",level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')
    log_and_print(f" Input details file path = {list_repos_file_path}","info")

    repos_input_details = load_repositories_from_file(list_repos_file_path)
    custom_prop={}

    if not GITHUB_TOKEN:
        raise ValueError(f"{args.token_env} environment variable not set.")
    if not CERT_PATH:
        log_and_print("Certificate path not provided. Proceeding without certificate verification.","info")

    if not repos_input_details:
        log_and_print(f"No repositories found in the file {list_repos_file_path}.","error")
    else:
        log_and_print(f"...Customer Property setting - Process  Start...","info")
        repo_count = 0
        for repo_detail, properties_str, settings_str in repos_input_details:  
            repo_count += 1
            try:
                log_and_print(f"{repo_count}... Processing repository: '{repo_detail}' ")
                
                # First process repository settings
                process_repo_settings(repo_detail, settings_str)
                
                # Then process custom properties if any
                if properties_str:
                    log_and_print(f"Setting custom properties: [{properties_str}]")
                    properties_list = properties_str.split(',')
                    custom_prop['properties']=[]
                    for i,prop_val in enumerate(properties_list):
                        custom_prop['properties']=[]
                        prop,val = prop_val.split('=')
                        log_and_print(f"... custom_prop = '{prop}' : value to be set = '{val}' ","info")
                        custom_prop['properties'].append({'property_name':prop,'value':val})
                        custom_setting_update(repo_detail,custom_prop)
                
                #log_and_print(f"{index}... Completed Branch protection ruleset at Repo : '{repo_detail}' ")
            except Exception as e:
                log_and_print(f"{repo_count}... Failed at Repo : '{repo_detail}' due to error: {str(e)}","info")

    log_and_print("*** Customer Property setting Process Completed... Review Status & log file... ***")

if __name__ == '__main__':
    main()
 
