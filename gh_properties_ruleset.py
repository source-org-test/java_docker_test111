import requests
import json
import os
import logging
import datetime
import argparse

# GitHub API base URL
API_URL = "https://api.github.com"

# Repository input file delimiter 
INPUT_FILE_DELIMITER = ";"  

# GitHub token and organization/repo details
GITHUB_TOKEN = os.getenv('ZILVERTON_GITHUB_TOKEN')
CERT_PATH = os.getenv('ZILVERTON_CERT_PATH')
ORG_NAME = "zilvertonz"  
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
                repo_detail, github_team_role = line.strip().split(INPUT_FILE_DELIMITER)
                repos.append((repo_detail, github_team_role))
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


def custom_setting_update(REPO_NAME,custom_properties):
    # URL to the repository custom property API endpoint
    custom_property_url = f"{API_URL}/repos/{ORG_NAME}/{REPO_NAME}/properties/values"
     
    # Make the API request to set the branch protection rules
    response = requests.patch(
        custom_property_url,
        headers=headers,
        data=json.dumps(custom_properties),
        verify=CERT_PATH
    )
    
    # Check if the request was successful
    if response.status_code == 204:
        log_and_print(f"...Successfully set custom property [] for repository '{REPO_NAME}'...","success")
    else:
        log_and_print(f"...Failed to set cutom property - status code: {response.status_code}","error")
        log_and_print(response.json(),"error")
        

def main():
    # Setup argument parser for command-line flags
    parser = argparse.ArgumentParser(description=f"...Branch Protection ruleset creation for repositories...")
    parser.add_argument('-r', '--repo_file',type=str,required=True,help="Path to the CSV file containing list of repositories")
    parser.add_argument('-o', '--output_folder', type=str, default='./output', help="Path to the folder where the migration summary will be saved (default: './output').")
    
    args = parser.parse_args()

    # Get the current date and time, and format it
    current_datetime = datetime.datetime.now().strftime('%d%b%Y_%H%M')

    # Get the input path of the filename from the argument - Input file containing repo names
    list_repos_file_path = args.repo_file 
    output_log_folder = args.output_folder
    
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
        raise ValueError("ZILVERTON_GITHUB_TOKEN environment variable not set.")
    if not CERT_PATH:
        raise ValueError("ZILVERTON_CERT_PATH environment variable not set.")

    if not repos_input_details:
        log_and_print(f"No repositories found in the file {list_repos_file_path}.","error")
    else:
        log_and_print(f"...Customer Property setting - Process  Start...","info")
        for index, (repo_detail,proprties) in enumerate(repos_input_details, start=1):  
            try:
                log_and_print(f"{index}... Setting property [{proprties}] at Repo : '{repo_detail}' ","info")
                custom_prop['properties']=[]
                props = proprties.split(",")

                for i,prop_val in enumerate(props):
                    custom_prop['properties']=[]
                    prop,val = prop_val.split('=')
                    log_and_print(f"... custom_prop = '{prop}' : value to be set = '{val}' ","info")
                    custom_prop['properties'].append({'property_name':prop,'value':val})
                    custom_setting_update(repo_detail,custom_prop)
                
                #log_and_print(f"{index}... Completed Branch protection ruleset at Repo : '{repo_detail}' ")
            except Exception as e:
                log_and_print(f"{index}... Failed at Repo : '{repo_detail}' due to error: {str(e)}","info")

    log_and_print("*** Customer Property setting Process Completed... Review Status & log file... ***")

if __name__ == '__main__':
    main()
 
